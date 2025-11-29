"""MCP 服务器主程序"""

import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config.manager import ConfigManager
from .config.models import Config
from .command.manager import CommandManager
from .auth.manager import AuthManager
from .mcp_client.manager import McpClientManager

logger = logging.getLogger(__name__)


class McpServer:
    """MCP 服务器"""

    def __init__(self, config_path: str):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        
        # 初始化管理器
        self.auth_manager = AuthManager(self.config)
        self.command_manager = CommandManager(self.config, self.auth_manager)
        self.mcp_client_manager = McpClientManager(self.config, self.command_manager)
        
        # 设置配置变更回调
        self.config_manager.on_config_changed = self._on_config_changed
        
        # 创建 MCP 服务器
        self.server = Server("mymcp")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """设置 MCP 服务器处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出所有可用工具"""
            return self.command_manager.get_all_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """调用工具"""
            try:
                # 检查是否是本地命令
                if name in [cmd.name for cmd in self.config.commands]:
                    return await self.command_manager.call_tool(name, arguments)
                
                # 检查是否是 MCP 服务工具
                # 查找工具对应的服务
                for service_name, client in self.mcp_client_manager.clients.items():
                    tools = await client.list_tools()
                    for tool in tools:
                        tool_name = tool.name
                        # 检查是否有前缀
                        for server_config in self.config.mcp_servers:
                            if server_config.name == service_name:
                                if server_config.prefix:
                                    tool_name = f"{server_config.prefix}_{tool.name}"
                                break
                        
                        if tool_name == name:
                            result = await self.mcp_client_manager.call_tool(
                                service_name, tool.name, arguments
                            )
                            # 转换结果格式
                            contents = []
                            for content in result.content:
                                if content.type == "text":
                                    contents.append(TextContent(type="text", text=content.text))
                                else:
                                    contents.append(TextContent(type="text", text=str(content)))
                            return contents
                
                raise ValueError(f"工具不存在: {name}")
            
            except Exception as e:
                logger.error(f"调用工具 {name} 失败: {e}", exc_info=True)
                raise

    async def _on_config_changed(self, old_config: Config, new_config: Config) -> None:
        """配置变更回调"""
        logger.info("检测到配置变更，开始热重载...")
        
        # 更新配置
        self.config = new_config
        
        # 重新加载管理器
        self.auth_manager.reload(new_config)
        self.command_manager.reload(new_config)
        
        # 重新加载 MCP 客户端
        await self.mcp_client_manager.reload(old_config, new_config)
        
        logger.info("配置热重载完成")

    async def run(self) -> None:
        """运行服务器"""
        # 初始化 MCP 客户端
        await self.mcp_client_manager.initialize()
        
        # 启动配置监控
        self.config_manager.start_watching()
        
        try:
            # 运行 MCP 服务器
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        finally:
            # 清理资源
            self.config_manager.stop_watching()
            await self.mcp_client_manager.shutdown()

    @classmethod
    async def main(cls, config_path: str) -> None:
        """主函数"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        server = cls(config_path)
        await server.run()


async def run_server(config_path: str) -> None:
    """运行服务器（便捷函数）"""
    await McpServer.main(config_path)

