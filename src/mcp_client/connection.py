"""MCP 连接管理"""

import asyncio
import logging
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class McpConnection:
    """MCP 连接"""

    def __init__(self, name: str, command: str, args: list, timeout: int = 30):
        self.name = name
        self.command = command
        self.args = args
        self.timeout = timeout
        self.session: Optional[ClientSession] = None
        self._connected = False
        self._read_stream = None
        self._write_stream = None

    async def connect(self) -> ClientSession:
        """建立连接"""
        if self._connected and self.session:
            return self.session

        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args
            )

            # 使用 stdio_client 建立连接
            stdio_transport = await stdio_client(server_params)
            self._read_stream, self._write_stream = stdio_transport
            
            # 创建会话
            self.session = ClientSession(self._read_stream, self._write_stream)
            
            # 初始化会话
            await self.session.__aenter__()
            
            self._connected = True
            logger.info(f"MCP 连接 {self.name} 已建立")
            return self.session
        except Exception as e:
            logger.error(f"建立 MCP 连接 {self.name} 失败: {e}", exc_info=True)
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
                logger.info(f"MCP 连接 {self.name} 已断开")
            except Exception as e:
                logger.warning(f"断开 MCP 连接 {self.name} 时出错: {e}")
            finally:
                self.session = None
                self._read_stream = None
                self._write_stream = None
        
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected and self.session is not None

