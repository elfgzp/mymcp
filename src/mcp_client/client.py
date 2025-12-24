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
            
            # 根据签名调用（某些 MCP 服务可能需要参数）
            # 如果参数都有默认值，可以不传参数（使用默认值）
            # 如果参数没有默认值，需要显式传递 None
            params_with_defaults = [p for p in sig.parameters.values() if p.default != inspect.Parameter.empty]
            params_without_defaults = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]
            
            if len(params_without_defaults) == 0:
                # 所有参数都有默认值，可以不传参数
                if len(sig.parameters) == 0:
                    result = await self.session.list_tools()
                else:
                    # 对于有可选参数的情况，优先不传参数（使用默认值）
                    # 某些 MCP 服务（如 Rainbow）的装饰器可能不支持带参数的函数签名
                    logger.debug(f"[{self.name}] list_tools 有可选参数，尝试不传参数（使用默认值）...")
                    try:
                        # 首先尝试不传任何参数
                        result = await self.session.list_tools()
                    except Exception as e1:
                        error_msg1 = str(e1)
                        logger.debug(f"[{self.name}] 不传参数失败: {error_msg1}")
                        # 如果失败，尝试显式传递 None（按位置参数）
                        try:
                            logger.debug(f"[{self.name}] 尝试显式传递 None 作为位置参数...")
                            result = await self.session.list_tools(None)
                        except Exception as e2:
                            error_msg2 = str(e2)
                            logger.debug(f"[{self.name}] 传递 None 失败: {error_msg2}")
                            # 最后尝试传递 None 作为关键字参数
                            try:
                                logger.debug(f"[{self.name}] 尝试传递 None 作为关键字参数...")
                                result = await self.session.list_tools(cursor=None, params=None)
                            except Exception as e3:
                                # 所有尝试都失败，抛出最后一个错误
                                logger.error(f"[{self.name}] 所有参数传递方式都失败，使用最后一个错误")
                                raise e3
            else:
                # 有必需参数，需要传递
                logger.warning(f"[{self.name}] list_tools 有必需参数，可能需要特殊处理")
                result = await self.session.list_tools()
            
            self._tools_cache = result.tools
            logger.info(f"[{self.name}] ✓ 获取到 {len(self._tools_cache)} 个工具")
            return self._tools_cache
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"[{self.name}] ✗ 获取工具列表失败: {error_type}: {error_msg}")
            logger.error(f"[{self.name}] 错误详情: {e}", exc_info=True)
            
            # 如果是 "Invalid request parameters" 错误，尝试其他方法
            if "Invalid request parameters" in error_msg or "invalid" in error_msg.lower():
                logger.warning(f"[{self.name}] 检测到 'Invalid request parameters' 错误，可能是 MCP 协议版本不兼容")
                try:
                    # 尝试获取服务器信息
                    logger.debug(f"[{self.name}] 尝试获取服务器 capabilities...")
                    if hasattr(self.session, 'initialize_result'):
                        init_result = self.session.initialize_result
                        logger.debug(f"[{self.name}] 服务器 capabilities: {init_result.capabilities if hasattr(init_result, 'capabilities') else 'N/A'}")
                    
                    # 尝试直接调用底层方法（如果可用）
                    if hasattr(self.session, '_send_request'):
                        logger.debug(f"[{self.name}] 尝试使用底层方法...")
                        # 这里可以尝试其他调用方式
                except Exception as cap_error:
                    logger.debug(f"[{self.name}] 获取 capabilities 失败: {cap_error}")
            
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

