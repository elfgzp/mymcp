"""MCP 连接管理"""

import asyncio
import logging
import os
from typing import Optional, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class McpConnection:
    """MCP 连接"""

    def __init__(self, name: str, command: str, args: list, timeout: int = 30, env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = env  # 环境变量
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
            logger.debug(f"[{self.name}] 连接已存在，直接返回")
            return self.session

        try:
            # 准备环境变量（合并系统环境变量和自定义环境变量）
            process_env = None
            if self.env:
                # 过滤掉空值和未解析的环境变量占位符
                filtered_env = {
                    k: v for k, v in self.env.items()
                    if v and not (isinstance(v, str) and v.startswith("${") and v.endswith("}"))
                }
                logger.debug(f"[{self.name}] 过滤后的环境变量数量: {len(filtered_env)}/{len(self.env)}")
                if filtered_env:
                    process_env = {**os.environ, **filtered_env}
                    logger.debug(f"[{self.name}] 使用自定义环境变量")
                else:
                    # 如果没有有效的环境变量，使用系统环境变量
                    process_env = os.environ
                    logger.debug(f"[{self.name}] 使用系统环境变量")
            else:
                process_env = os.environ
                logger.debug(f"[{self.name}] 未配置环境变量，使用系统环境变量")
            
            logger.debug(f"[{self.name}] 创建 StdioServerParameters: command={self.command}, args={self.args}")
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=process_env
            )

            # stdio_client 返回异步上下文管理器，需要使用 async with
            # 使用 asyncio.wait_for 添加超时控制
            logger.debug(f"[{self.name}] 创建 stdio_client...")
            stdio_transport_context = stdio_client(server_params)
            
            try:
                logger.debug(f"[{self.name}] 等待 stdio 传输建立（超时: {self.timeout}秒）...")
                self._read_stream, self._write_stream = await asyncio.wait_for(
                    stdio_transport_context.__aenter__(),
                    timeout=self.timeout
                )
                logger.debug(f"[{self.name}] stdio 传输已建立")
            except asyncio.TimeoutError:
                logger.error(f"[{self.name}] stdio 传输建立超时（{self.timeout} 秒）")
                raise TimeoutError(f"连接 {self.name} 超时（{self.timeout} 秒）")
            
            # 创建会话
            logger.debug(f"[{self.name}] 创建 ClientSession...")
            self.session = ClientSession(self._read_stream, self._write_stream)
            
            # 初始化会话（也添加超时控制）
            init_timeout = min(self.timeout, 30)  # 初始化最多30秒
            try:
                logger.debug(f"[{self.name}] 初始化会话（超时: {init_timeout}秒）...")
                # ClientSession.__aenter__() 会自动发送 InitializeRequest
                # 并等待 InitializedNotification
                # 如果 Cursor 可以直接使用 Rainbow MCP 服务，说明标准初始化方式应该是有效的
                init_result = await asyncio.wait_for(
                    self.session.__aenter__(),
                    timeout=init_timeout
                )
                logger.debug(f"[{self.name}] 会话初始化成功")
                # 记录初始化结果（如果有的话）
                if init_result:
                    logger.debug(f"[{self.name}] 初始化结果: {type(init_result)}")
                
                # 显式调用 initialize() 方法，确保初始化完成
                # 从测试脚本发现，ClientSession.__aenter__() 可能只发送了 InitializeRequest
                # 但没有等待 InitializedNotification，需要显式调用 initialize() 来确保初始化完成
                logger.debug(f"[{self.name}] 显式调用 initialize() 方法确保初始化完成...")
                try:
                    init_result2 = await self.session.initialize()
                    logger.debug(f"[{self.name}] ✓ initialize() 调用成功")
                    if hasattr(init_result2, 'serverInfo'):
                        logger.debug(f"[{self.name}] 服务器信息: {init_result2.serverInfo}")
                except Exception as e:
                    # 如果 initialize() 失败（可能已经初始化），记录警告但继续
                    logger.debug(f"[{self.name}] initialize() 调用失败（可能已经初始化）: {e}")
            except asyncio.TimeoutError:
                logger.error(f"[{self.name}] 会话初始化超时（{init_timeout} 秒）")
                # 清理已创建的流
                try:
                    await stdio_transport_context.__aexit__(None, None, None)
                except Exception as cleanup_error:
                    logger.warning(f"[{self.name}] 清理 stdio 传输时出错: {cleanup_error}")
                raise TimeoutError(f"初始化 {self.name} 会话超时")
            
            # 保存上下文管理器以便断开时使用
            self._stdio_context = stdio_transport_context
            
            self._connected = True
            logger.info(f"[{self.name}] ✓ MCP 连接已建立")
            return self.session
        except Exception as e:
            error_msg = str(e)
            self._connection_error = error_msg
            logger.error(f"[{self.name}] ✗ 建立 MCP 连接失败: {e}", exc_info=True)
            logger.error(f"[{self.name}] 错误类型: {type(e).__name__}")
            logger.error(f"[{self.name}] 错误消息: {error_msg}")
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

