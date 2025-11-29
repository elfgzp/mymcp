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
            result = await self.session.list_tools()
            self._tools_cache = result.tools
            logger.debug(f"MCP 客户端 {self.name} 获取到 {len(self._tools_cache)} 个工具")
            return self._tools_cache
        except Exception as e:
            logger.error(f"获取 MCP 客户端 {self.name} 工具列表失败: {e}", exc_info=True)
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

