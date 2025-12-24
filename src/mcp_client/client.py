"""MCP 客户端实现"""

import logging
from typing import List, Dict, Any, Optional
from mcp.types import Tool

from .connection import McpConnection

logger = logging.getLogger(__name__)


class McpClient:
    """MCP 客户端"""

    def __init__(self, name: str, connection: McpConnection):
        self.name = name
        self.connection = connection
        self.session = None
        self._tools_cache: Optional[List[Tool]] = None

    async def connect(self) -> None:
        """建立连接"""
        self.session = await self.connection.connect()

    async def disconnect(self) -> None:
        """断开连接"""
        await self.connection.disconnect()
        self.session = None
        self._tools_cache = None

    async def list_tools(self) -> List[Tool]:
        """获取工具列表"""
        if self._tools_cache:
            return self._tools_cache

        if not self.session:
            await self.connect()
        
        # 检查连接状态
        if not self.is_connected:
            logger.warning(f"[{self.name}] 连接未建立，尝试重新连接...")
            await self.connect()
        
        # 检查 session 是否有效
        if not self.session:
            raise ConnectionError(f"[{self.name}] 会话未初始化，无法获取工具列表")
        
        # 检查连接流是否已关闭
        if hasattr(self.connection, '_write_stream') and self.connection._write_stream:
            if hasattr(self.connection._write_stream, 'closed') and self.connection._write_stream.closed:
                logger.warning(f"[{self.name}] 写入流已关闭，尝试重新连接...")
                await self.connect()
                if not self.session:
                    raise ConnectionError(f"[{self.name}] 重新连接失败，无法获取工具列表")

        try:
            # 尝试获取工具列表
            logger.debug(f"[{self.name}] 调用 session.list_tools()...")
            
            # 检查 session.list_tools 的签名，看是否需要参数
            import inspect
            sig = inspect.signature(self.session.list_tools)
            logger.debug(f"[{self.name}] list_tools 方法签名: {sig}")
            
            # 检查 session 的状态，确保已初始化
            if hasattr(self.session, '_initialized'):
                logger.debug(f"[{self.name}] session._initialized: {self.session._initialized}")
            if hasattr(self.session, '_server_info'):
                logger.debug(f"[{self.name}] session._server_info: {self.session._server_info}")
            
            # 简化调用逻辑：直接使用最简单的方式（不传参数）
            # 如果 Cursor 可以直接使用 Rainbow MCP 服务，说明不传参数的方式是正确的
            # MCP SDK 的 list_tools 方法应该支持不传参数（使用默认值）
            logger.debug(f"[{self.name}] 准备调用 list_tools()（无参数）...")
            result = await self.session.list_tools()
            
            self._tools_cache = result.tools
            logger.info(f"[{self.name}] ✓ 获取到 {len(self._tools_cache)} 个工具")
            return self._tools_cache
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # 记录错误信息用于调试
            logger.debug(f"[{self.name}] list_tools() 异常: 类型={error_type}, 消息={error_msg}")
            
            # 如果是 "Invalid request parameters" 或 "Connection closed"（可能是未初始化导致的），尝试调用 initialize() 后重试
            # 注意：某些服务（如 tapd）在未完全初始化时，list_tools() 会返回 "Connection closed"
            # 但调用 initialize() 后可以正常工作
            should_try_initialize = (
                "Invalid request parameters" in error_msg or 
                "request before initialization" in error_msg.lower() or
                ("Connection closed" in error_msg and error_type == "McpError")  # McpError: Connection closed 可能是未初始化
            )
            
            logger.debug(f"[{self.name}] should_try_initialize={should_try_initialize}, error_type={error_type}, error_msg={error_msg}")
            
            if should_try_initialize:
                logger.debug(f"[{self.name}] list_tools() 失败，可能是未完全初始化，尝试调用 initialize()...")
                logger.debug(f"[{self.name}] 错误类型: {error_type}, 错误消息: {error_msg}")
                try:
                    init_result = await self.session.initialize()
                    logger.debug(f"[{self.name}] ✓ initialize() 调用成功")
                    if hasattr(init_result, 'serverInfo'):
                        logger.debug(f"[{self.name}] 服务器信息: {init_result.serverInfo}")
                    
                    # 重试 list_tools()
                    logger.debug(f"[{self.name}] 重试 list_tools()...")
                    result = await self.session.list_tools()
                    self._tools_cache = result.tools
                    logger.info(f"[{self.name}] ✓ 获取到 {len(self._tools_cache)} 个工具（调用 initialize() 后）")
                    return self._tools_cache
                except Exception as init_error:
                    init_error_msg = str(init_error)
                    init_error_type = type(init_error).__name__
                    # 如果 initialize() 失败且是连接关闭错误，说明服务不支持重复初始化
                    if "closed" in init_error_msg.lower() or "Connection closed" in init_error_msg or "ClosedResourceError" in init_error_type:
                        logger.warning(f"[{self.name}] initialize() 调用失败：连接已关闭（服务不支持重复初始化）: {init_error}")
                        # 继续抛出原始错误
                    else:
                        logger.warning(f"[{self.name}] initialize() 调用失败: {init_error_type}: {init_error_msg}")
                        # 继续抛出原始错误
            
            # 如果是 ClosedResourceError 或其他连接关闭错误，且没有尝试 initialize()，说明连接已关闭
            # 注意：如果 should_try_initialize 为 True，说明已经尝试或将要尝试 initialize()，不应该在这里处理
            if not should_try_initialize and ("ClosedResourceError" in error_type or "closed" in error_msg.lower()):
                logger.error(f"[{self.name}] 获取工具列表失败：连接已关闭 ({error_type}: {error_msg})")
                self._tools_cache = None
                # 标记连接为失败状态
                self.connection._connected = False
                # 尝试清理连接
                try:
                    await self.disconnect()
                except Exception as cleanup_error:
                    logger.debug(f"[{self.name}] 清理连接时出错: {cleanup_error}")
                raise ConnectionError(f"[{self.name}] 连接已关闭，无法获取工具列表: {error_msg}")
            
            # 只在 DEBUG 级别记录详细错误，避免日志过多
            # 上层重试机制会记录最终的错误信息
            logger.debug(f"[{self.name}] 获取工具列表失败: {error_type}: {error_msg}")
            
            # 如果是 "Invalid request parameters" 错误，记录一次警告即可
            if "Invalid request parameters" in error_msg or "invalid" in error_msg.lower():
                logger.debug(f"[{self.name}] 检测到 'Invalid request parameters' 错误，可能是 MCP 协议版本不兼容")
            
            raise

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """调用工具"""
        if not self.session:
            await self.connect()

        try:
            result = await self.session.call_tool(name, arguments)
            return result
        except Exception as e:
            logger.error(f"MCP 客户端 {self.name} 调用工具 {name} 失败: {e}", exc_info=True)
            raise

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self.connection.is_connected

