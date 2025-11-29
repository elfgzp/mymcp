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
        # 对于启动较慢的服务（如 serena、工蜂），增加超时时间
        # 如果超时时间小于 60 秒，默认设置为 60 秒
        # 对于使用 uvx 和 git+ 的服务，可能需要更长时间
        full_command = " ".join([command] + args)
        if "uvx" in command and "git+" in full_command:
            self.timeout = max(timeout, 180)  # git 克隆需要更长时间，增加到180秒
        elif "npx" in command:
            self.timeout = max(timeout, 90)  # npx 下载和启动也需要时间，增加到90秒
        else:
            self.timeout = max(timeout, 60) if timeout < 60 else timeout
        self.session: Optional[ClientSession] = None
        self._connected = False
        self._read_stream = None
        self._write_stream = None
        self._stdio_context = None
        self._connection_error: Optional[str] = None

    async def connect(self) -> ClientSession:
        """建立连接"""
        if self._connected and self.session:
            return self.session

        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args
            )

            # stdio_client 返回异步上下文管理器，需要使用 async with
            # 使用 asyncio.wait_for 添加超时控制
            stdio_transport_context = stdio_client(server_params)
            
            try:
                self._read_stream, self._write_stream = await asyncio.wait_for(
                    stdio_transport_context.__aenter__(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"连接 {self.name} 超时（{self.timeout} 秒）")
            
            # 创建会话
            self.session = ClientSession(self._read_stream, self._write_stream)
            
            # 初始化会话（也添加超时控制）
            try:
                await asyncio.wait_for(
                    self.session.__aenter__(),
                    timeout=min(self.timeout, 30)  # 初始化最多30秒
                )
            except asyncio.TimeoutError:
                # 清理已创建的流
                try:
                    await stdio_transport_context.__aexit__(None, None, None)
                except:
                    pass
                raise TimeoutError(f"初始化 {self.name} 会话超时")
            
            # 保存上下文管理器以便断开时使用
            self._stdio_context = stdio_transport_context
            
            self._connected = True
            logger.info(f"MCP 连接 {self.name} 已建立")
            return self.session
        except Exception as e:
            error_msg = str(e)
            self._connection_error = error_msg
            logger.error(f"建立 MCP 连接 {self.name} 失败: {e}", exc_info=True)
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """断开连接"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"断开 MCP 会话 {self.name} 时出错: {e}")
            finally:
                self.session = None
        
        # 关闭 stdio 传输
        if hasattr(self, '_stdio_context') and self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"关闭 stdio 传输 {self.name} 时出错: {e}")
            finally:
                self._stdio_context = None
                self._read_stream = None
                self._write_stream = None
        
        self._connected = False
        logger.info(f"MCP 连接 {self.name} 已断开")

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected and self.session is not None
    
    @property
    def connection_error(self) -> Optional[str]:
        """连接错误信息"""
        return self._connection_error

