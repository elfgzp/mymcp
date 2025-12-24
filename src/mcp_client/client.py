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

