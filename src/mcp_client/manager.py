"""MCP 客户端管理器"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from mcp.types import Tool

from ..config.models import Config, McpServerConfig
from .client import McpClient
from .connection import McpConnection
from ..tool_index.manager import ToolIndexManager

logger = logging.getLogger(__name__)


class McpClientManager:
    """MCP 客户端管理器"""

    def __init__(self, config: Config, command_manager, tool_index_manager: ToolIndexManager = None):
        self.config = config
        self.command_manager = command_manager
        self.tool_index_manager = tool_index_manager
        self.clients: Dict[str, McpClient] = {}
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}
        self._init_tasks: Dict[str, asyncio.Task] = {}  # 初始化任务
        self._retry_tasks: Dict[str, asyncio.Task] = {}  # 重试任务
        self._connection_status: Dict[str, str] = {}  # 连接状态: "connecting", "connected", "error", "disconnected"
        self._retry_counts: Dict[str, int] = {}  # 重试次数计数

    async def initialize(self) -> None:
        """初始化所有启用的 MCP 服务（异步，不阻塞）"""
        enabled_servers = [s for s in self.config.mcp_servers if s.enabled]
        logger.info(f"开始初始化 {len(enabled_servers)} 个 MCP 服务: {[s.name for s in enabled_servers]}")
        
        for server_config in enabled_servers:
            # 异步启动，不阻塞主流程
            logger.info(f"创建异步任务连接服务: {server_config.name}")
            task = asyncio.create_task(self._async_add_server(server_config))
            self._init_tasks[server_config.name] = task

    async def _async_add_server(self, server_config: McpServerConfig) -> None:
        """异步添加 MCP 服务（内部方法）"""
        # 如果已经在重试，不要重复启动
        if server_config.name in self._retry_tasks:
            logger.debug(f"MCP 服务 {server_config.name} 已在重试中，跳过")
            return
        
        self._connection_status[server_config.name] = "connecting"
        try:
            await self.add_server(server_config, skip_retry=True)  # 首次连接不自动重试
        except Exception as e:
            error_msg = str(e)
            self._connection_status[server_config.name] = f"error: {error_msg[:100]}"
            # 只记录简要错误，避免日志过多
            logger.error(f"异步连接 MCP 服务 {server_config.name} 失败: {error_msg[:100]}")
            logger.debug(f"详细错误: {e}", exc_info=True)
            
            # 如果启用重试，启动重试任务
            if server_config.retry_on_failure:
                self._start_retry_task(server_config)
            else:
                # 如果未启用重试，直接标记为失败并停止
                logger.info(f"MCP 服务 {server_config.name} 未启用重试，停止连接尝试")

    async def add_server(self, server_config: McpServerConfig, skip_retry: bool = False) -> None:
        """添加 MCP 服务"""
        # 检查服务是否已禁用
        if not server_config.enabled:
            logger.debug(f"MCP 服务 {server_config.name} 已禁用，跳过连接")
            return
        
        if server_config.name in self.clients:
            await self.remove_server(server_config.name)

        self._connection_status[server_config.name] = "connecting"
        
        # 详细日志：连接信息
        logger.info(f"[{server_config.name}] 开始连接 MCP 服务...")
        logger.info(f"[{server_config.name}] 命令: {server_config.connection.command or 'uvx'}")
        logger.info(f"[{server_config.name}] 参数: {server_config.connection.args}")
        logger.info(f"[{server_config.name}] 超时: {server_config.timeout} 秒")
        if server_config.env:
            # 不打印敏感信息，只打印键名
            env_keys = list(server_config.env.keys())
            logger.info(f"[{server_config.name}] 环境变量: {env_keys}")
            # 打印非敏感环境变量的值
            for key, value in server_config.env.items():
                if not any(sensitive in key.upper() for sensitive in ['COOKIE', 'TOKEN', 'PASSWORD', 'SECRET', 'KEY']):
                    logger.debug(f"[{server_config.name}] {key} = {value}")
        
        try:
            connection = McpConnection(
                name=server_config.name,
                command=server_config.connection.command or "uvx",
                args=server_config.connection.args or [],
                timeout=server_config.timeout,
                env=server_config.env
            )

            client = McpClient(server_config.name, connection)
            logger.info(f"[{server_config.name}] 正在建立连接...")
            await client.connect()
            logger.info(f"[{server_config.name}] 连接已建立，等待服务完全启动...")
            
            # 等待初始化完成（包括 InitializedNotification）
            # 从 Cursor 的日志看，初始化后需要等待 InitializedNotification 才能调用 list_tools
            # 增加等待时间，确保初始化完全完成
            await asyncio.sleep(1.0)
            logger.debug(f"[{server_config.name}] 等待初始化完成...")
            
            logger.info(f"[{server_config.name}] 正在获取工具列表...")

            # 获取工具列表（带重试机制）
            max_retries = 3
            retry_delay = 1.0
            tools = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    tools = await client.list_tools()
                    logger.info(f"[{server_config.name}] ✓ 获取到 {len(tools)} 个工具")
                    break
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    if attempt < max_retries - 1:
                        # 重试时只记录简要警告，避免日志过多
                        logger.warning(f"[{server_config.name}] 获取工具列表失败 (尝试 {attempt + 1}/{max_retries}): {error_msg[:100]}")
                        logger.debug(f"[{server_config.name}] 等待 {retry_delay} 秒后重试...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        # 最后一次失败时记录完整错误信息，然后停止重试
                        logger.error(f"[{server_config.name}] 获取工具列表失败，已达到最大重试次数: {error_msg}")
                        logger.debug(f"[{server_config.name}] 错误详情: {e}", exc_info=True)
                        # 标记服务为失败状态，停止后续重试
                        self._connection_status[server_config.name] = f"error: {error_msg[:100]}"
                        # 如果启用了重试，但已达到最大重试次数，停止重试任务
                        if server_config.retry_on_failure and server_config.name in self._retry_tasks:
                            task = self._retry_tasks[server_config.name]
                            if not task.done():
                                task.cancel()
                                logger.info(f"[{server_config.name}] 已停止重试任务，避免日志污染")
                        raise
            
            if tools is None:
                raise last_error or Exception("获取工具列表失败")

            # 注册工具到命令管理器
            tool_names = []
            for tool in tools:
                tool_name = f"{server_config.prefix}_{tool.name}" if server_config.prefix else tool.name
                tool_names.append(tool_name)
                self.command_manager.register_mcp_tool(server_config.name, tool, server_config.prefix)
            logger.debug(f"[{server_config.name}] 已注册工具: {tool_names[:5]}{'...' if len(tool_names) > 5 else ''}")
            
            # 添加到工具索引（如果启用）
            if self.tool_index_manager:
                indexed_count = 0
                for tool in tools:
                    self.tool_index_manager.add_tool(
                        tool=tool,
                        service_name=server_config.name,
                        service_description=server_config.description,
                        prefix=server_config.prefix
                    )
                    indexed_count += 1
                logger.info(f"[{server_config.name}] 已添加 {indexed_count} 个工具到索引")

            self.clients[server_config.name] = client
            self._connection_status[server_config.name] = "connected"
            self._retry_counts[server_config.name] = 0  # 重置重试计数
            logger.info(f"[{server_config.name}] ✓ MCP 服务连接成功，工具数量: {len(tools)}")

            # 如果启用自动重连，启动监控任务
            if server_config.auto_reconnect:
                self._start_reconnect_monitor(server_config.name, server_config)

        except Exception as e:
            error_msg = str(e)
            self._connection_status[server_config.name] = f"error: {error_msg}"
            logger.error(f"[{server_config.name}] ✗ 连接 MCP 服务失败: {e}", exc_info=True)
            logger.error(f"[{server_config.name}] 错误类型: {type(e).__name__}")
            logger.error(f"[{server_config.name}] 错误详情: {error_msg}")
            
            # 只有在不跳过重试且启用重试时才启动重试任务
            if not skip_retry and server_config.retry_on_failure:
                logger.info(f"[{server_config.name}] 将启动重试任务...")
                self._start_retry_task(server_config)
            raise

    async def remove_server(self, name: str) -> None:
        """移除 MCP 服务"""
        if name in self.clients:
            client = self.clients[name]
            await client.disconnect()
            del self.clients[name]

        # 停止初始化任务
        if name in self._init_tasks:
            self._init_tasks[name].cancel()
            del self._init_tasks[name]

        # 停止重试任务
        if name in self._retry_tasks:
            self._retry_tasks[name].cancel()
            del self._retry_tasks[name]
            if name in self._retry_counts:
                del self._retry_counts[name]

        # 停止重连监控
        if name in self._reconnect_tasks:
            self._reconnect_tasks[name].cancel()
            del self._reconnect_tasks[name]

        # 注销工具
        self.command_manager.unregister_mcp_tools(name)
        
        # 从工具索引移除
        if self.tool_index_manager:
            self.tool_index_manager.remove_service_tools(name)
        
        self._connection_status[name] = "disconnected"
        logger.info(f"MCP 服务 {name} 已移除")

    async def call_tool(self, service_name: str, tool_name: str, arguments: Dict) -> Any:
        """调用 MCP 服务工具"""
        if service_name not in self.clients:
            raise ValueError(f"MCP 服务 {service_name} 未连接")

        client = self.clients[service_name]
        return await client.call_tool(tool_name, arguments)

    async def reload(self, old_config: Config, new_config: Config) -> None:
        """重新加载配置（热更新）"""
        old_servers = {s.name: s for s in old_config.mcp_servers}
        new_servers = {s.name: s for s in new_config.mcp_servers}

        # 找出需要添加的服务
        for name, server_config in new_servers.items():
            if name not in old_servers or server_config != old_servers[name]:
                if server_config.enabled:
                    await self.add_server(server_config)
                elif name in self.clients:
                    await self.remove_server(name)

        # 找出需要移除的服务
        for name in old_servers:
            if name not in new_servers:
                await self.remove_server(name)

        # 更新配置
        self.config = new_config

    def _start_reconnect_monitor(self, name: str, server_config: McpServerConfig) -> None:
        """启动重连监控"""
        async def monitor():
            while True:
                await asyncio.sleep(30)  # 每30秒检查一次
                if name in self.clients:
                    client = self.clients[name]
                    if not client.is_connected:
                        logger.warning(f"MCP 服务 {name} 连接断开，尝试重连...")
                        try:
                            await client.connect()
                            # 重新获取工具列表
                            tools = await client.list_tools()
                            for tool in tools:
                                tool_name = f"{server_config.prefix}_{tool.name}" if server_config.prefix else tool.name
                                self.command_manager.register_mcp_tool(name, tool, server_config.prefix)
                            
                            # 更新工具索引
                            if self.tool_index_manager:
                                # 先移除旧索引
                                self.tool_index_manager.remove_service_tools(name)
                                # 重新添加
                                for tool in tools:
                                    self.tool_index_manager.add_tool(
                                        tool=tool,
                                        service_name=name,
                                        service_description=server_config.description,
                                        prefix=server_config.prefix
                                    )
                            
                            logger.info(f"MCP 服务 {name} 重连成功")
                        except Exception as e:
                            logger.error(f"MCP 服务 {name} 重连失败: {e}")

        task = asyncio.create_task(monitor())
        self._reconnect_tasks[name] = task

    def _start_retry_task(self, server_config: McpServerConfig) -> None:
        """启动重试任务（避免重复启动）"""
        name = server_config.name
        
        # 如果已经有重试任务在运行，不重复启动
        if name in self._retry_tasks:
            task = self._retry_tasks[name]
            if not task.done():
                logger.debug(f"MCP 服务 {name} 已有重试任务在运行，跳过")
                return
        
        # 初始化重试计数
        if name not in self._retry_counts:
            self._retry_counts[name] = 0
        
        async def retry_loop():
            """重试循环"""
            max_retries = getattr(self.config.global_config, 'max_retries', 3)
            retry_delay = getattr(self.config.global_config, 'retry_delay', 10)  # 默认10秒，给服务更多启动时间
            
            while True:
                # 检查服务是否已禁用
                current_config = None
                for s in self.config.mcp_servers:
                    if s.name == name:
                        current_config = s
                        break
                
                if not current_config or not current_config.enabled:
                    logger.info(f"MCP 服务 {name} 已禁用，停止重试")
                    self._connection_status[name] = "disconnected"
                    break
                
                # 检查重试次数
                retry_count = self._retry_counts.get(name, 0)
                if retry_count >= max_retries:
                    # 达到最大重试次数后，只记录一次警告，然后停止
                    logger.warning(f"MCP 服务 {name} 已达到最大重试次数 ({max_retries})，停止重试。如需重新尝试，请重启服务或修改配置。")
                    self._connection_status[name] = f"error: 已达到最大重试次数 ({max_retries})"
                    # 清理重试计数，避免后续继续重试
                    if name in self._retry_counts:
                        del self._retry_counts[name]
                    break
                
                # 等待后重试（指数退避，但最小间隔为 retry_delay，最大60秒）
                wait_time = min(max(retry_delay, 2 ** retry_count), 60)
                logger.info(f"MCP 服务 {name} 将在 {wait_time} 秒后重试 ({retry_count + 1}/{max_retries})...")
                await asyncio.sleep(wait_time)
                
                # 检查是否已经连接成功（可能在其他地方连接成功了）
                if name in self.clients and self.clients[name].is_connected:
                    logger.info(f"MCP 服务 {name} 已连接，停止重试")
                    break
                
                # 尝试连接（在重试前增加计数）
                self._connection_status[name] = "connecting"
                retry_count += 1
                self._retry_counts[name] = retry_count
                
                try:
                    # 使用 skip_retry=True 避免递归调用
                    await self.add_server(server_config, skip_retry=True)
                    logger.info(f"MCP 服务 {name} 重试连接成功")
                    break  # 连接成功，退出重试循环
                except Exception as e:
                    error_msg = str(e)
                    self._connection_status[name] = f"error: {error_msg[:100]}"
                    # 重试时只记录简要警告，避免日志过多
                    logger.warning(f"MCP 服务 {name} 重试连接失败 ({retry_count}/{max_retries}): {error_msg[:100]}")
                    logger.debug(f"详细错误: {e}", exc_info=True)
                    # 如果已达到最大重试次数，退出循环
                    if retry_count >= max_retries:
                        logger.warning(f"MCP 服务 {name} 已达到最大重试次数 ({max_retries})，停止重试")
                        self._connection_status[name] = f"error: 已达到最大重试次数"
                        break
                    # 否则继续重试循环
        
        # 创建并保存重试任务
        task = asyncio.create_task(retry_loop())
        self._retry_tasks[name] = task
        
        # 任务完成后清理
        def cleanup_task(t):
            if name in self._retry_tasks and self._retry_tasks[name] == t:
                del self._retry_tasks[name]
        
        task.add_done_callback(cleanup_task)

    def get_connection_status(self, name: str) -> str:
        """获取连接状态"""
        return self._connection_status.get(name, "unknown")
    
    def get_all_connection_status(self) -> Dict[str, str]:
        """获取所有连接状态"""
        return self._connection_status.copy()

    async def shutdown(self) -> None:
        """关闭所有连接"""
        # 取消所有初始化任务
        for task in self._init_tasks.values():
            task.cancel()
        self._init_tasks.clear()
        
        # 取消所有重试任务
        for task in self._retry_tasks.values():
            task.cancel()
        self._retry_tasks.clear()
        self._retry_counts.clear()
        
        # 关闭所有连接
        for name in list(self.clients.keys()):
            await self.remove_server(name)

