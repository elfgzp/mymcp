"""MCP 客户端管理器"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from mcp.types import Tool

from ..config.models import Config, McpServerConfig
from .client import McpClient
from .connection import McpConnection

logger = logging.getLogger(__name__)


class McpClientManager:
    """MCP 客户端管理器"""

    def __init__(self, config: Config, command_manager):
        self.config = config
        self.command_manager = command_manager
        self.clients: Dict[str, McpClient] = {}
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self) -> None:
        """初始化所有启用的 MCP 服务"""
        for server_config in self.config.mcp_servers:
            if server_config.enabled:
                await self.add_server(server_config)

    async def add_server(self, server_config: McpServerConfig) -> None:
        """添加 MCP 服务"""
        if server_config.name in self.clients:
            await self.remove_server(server_config.name)

        try:
            connection = McpConnection(
                name=server_config.name,
                command=server_config.connection.command or "uvx",
                args=server_config.connection.args or [],
                timeout=server_config.timeout
            )

            client = McpClient(server_config.name, connection)
            await client.connect()

            # 获取工具列表
            tools = await client.list_tools()

            # 注册工具到命令管理器
            for tool in tools:
                tool_name = f"{server_config.prefix}_{tool.name}" if server_config.prefix else tool.name
                self.command_manager.register_mcp_tool(server_config.name, tool, server_config.prefix)

            self.clients[server_config.name] = client
            logger.info(f"MCP 服务 {server_config.name} 已连接，工具数量: {len(tools)}")

            # 如果启用自动重连，启动监控任务
            if server_config.auto_reconnect:
                self._start_reconnect_monitor(server_config.name, server_config)

        except Exception as e:
            logger.error(f"连接 MCP 服务 {server_config.name} 失败: {e}")
            if server_config.retry_on_failure:
                await self._retry_connect(server_config)

    async def remove_server(self, name: str) -> None:
        """移除 MCP 服务"""
        if name in self.clients:
            client = self.clients[name]
            await client.disconnect()
            del self.clients[name]

        # 停止重连监控
        if name in self._reconnect_tasks:
            self._reconnect_tasks[name].cancel()
            del self._reconnect_tasks[name]

        # 注销工具
        self.command_manager.unregister_mcp_tools(name)
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
                            logger.info(f"MCP 服务 {name} 重连成功")
                        except Exception as e:
                            logger.error(f"MCP 服务 {name} 重连失败: {e}")

        task = asyncio.create_task(monitor())
        self._reconnect_tasks[name] = task

    async def _retry_connect(self, server_config: McpServerConfig, max_retries: int = 3) -> None:
        """重试连接"""
        for i in range(max_retries):
            await asyncio.sleep(2 ** i)  # 指数退避
            try:
                await self.add_server(server_config)
                return
            except Exception as e:
                logger.error(f"重试连接 {server_config.name} 失败 ({i+1}/{max_retries}): {e}")

    async def shutdown(self) -> None:
        """关闭所有连接"""
        for name in list(self.clients.keys()):
            await self.remove_server(name)

