"""MCP 服务器主程序"""

import asyncio
import logging
import sys
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config.manager import ConfigManager
from .config.models import Config
from .command.manager import CommandManager
from .auth.manager import AuthManager
from .mcp_client.manager import McpClientManager
from .tool_index.manager import ToolIndexManager
from .tool_proxy.tools import (
    create_proxy_tools,
    handle_search_tools,
    handle_execute_tool,
    handle_list_services
)

logger = logging.getLogger(__name__)

# 全局变量存储 McpServer 实例（用于管理端访问）
_global_mcp_servers: dict[str, "McpServer"] = {}


class McpServer:
    """MCP 服务器"""

    def __init__(self, config_path: str):
        self.config_path = str(config_path)
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        
        # 初始化管理器
        self.auth_manager = AuthManager(self.config)
        self.command_manager = CommandManager(self.config, self.auth_manager)
        
        # 初始化工具索引管理器（如果启用代理模式）
        self.tool_index_manager = None
        if self.config.global_config.tool_proxy_mode:
            use_whoosh = True  # 可以添加配置选项
            try:
                self.tool_index_manager = ToolIndexManager(use_whoosh=use_whoosh)
            except ImportError:
                logger.warning("Whoosh 未安装，使用简单搜索引擎")
                self.tool_index_manager = ToolIndexManager(use_whoosh=False)
        
        self.mcp_client_manager = McpClientManager(
            self.config,
            self.command_manager,
            tool_index_manager=self.tool_index_manager
        )
        
        # 如果启用工具代理模式，将本地命令也添加到索引中
        if self.tool_index_manager:
            for cmd in self.config.commands:
                if cmd.enabled:
                    tool = self.command_manager._command_to_tool(cmd)
                    self.tool_index_manager.add_tool(
                        tool=tool,
                        service_name="local",
                        service_description="本地命令",
                        prefix=None
                    )
        
        # 设置配置变更回调
        self.config_manager.on_config_changed = self._on_config_changed
        
        # 创建 MCP 服务器
        self.server = Server("mymcp")
        self._setup_handlers()
        
        # 注册到全局字典
        _global_mcp_servers[self.config_path] = self

    def _setup_handlers(self) -> None:
        """设置 MCP 服务器处理器"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出所有可用工具"""
            # 如果启用代理模式，只返回代理工具
            if self.config.global_config.tool_proxy_mode and self.tool_index_manager:
                proxy_tools = create_proxy_tools(
                    self.tool_index_manager,
                    self.mcp_client_manager,
                    self.config
                )
                # 根据配置决定是否暴露本地命令
                if self.config.global_config.tool_proxy.expose_local_commands:
                    local_tools = []
                    for cmd in self.config.commands:
                        if cmd.enabled:
                            local_tools.append(self.command_manager._command_to_tool(cmd))
                    return local_tools + proxy_tools
                else:
                    # 代理模式下不直接暴露本地命令，需要通过搜索和执行工具访问
                    return proxy_tools
            else:
                # 传统模式：返回所有工具
                return self.command_manager.get_all_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """调用工具"""
            try:
                # 检查是否是本地命令
                if name in [cmd.name for cmd in self.config.commands]:
                    return await self.command_manager.call_tool(name, arguments)
                
                # 如果启用代理模式，检查是否是代理工具
                if self.config.global_config.tool_proxy_mode and self.tool_index_manager:
                    if name == "mcp_search_tools":
                        query = arguments.get("query", "")
                        service_name = arguments.get("service_name")
                        limit = arguments.get("limit", self.config.global_config.tool_proxy.search_limit)
                        result = await handle_search_tools(
                            self.tool_index_manager,
                            query,
                            service_name,
                            limit
                        )
                        import json
                        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                    
                    elif name == "mcp_execute_tool":
                        tool_name = arguments.get("tool_name")
                        tool_arguments = arguments.get("arguments", {})
                        result = await handle_execute_tool(
                            self.tool_index_manager,
                            self.mcp_client_manager,
                            self.config,
                            tool_name,
                            tool_arguments,
                            command_manager=self.command_manager
                        )
                        import json
                        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                    
                    elif name == "mcp_list_services":
                        result = await handle_list_services(
                            self.tool_index_manager,
                            self.mcp_client_manager
                        )
                        import json
                        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                
                # 传统模式：检查是否是 MCP 服务工具
                if not self.config.global_config.tool_proxy_mode:
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
        # 异步初始化 MCP 客户端（不阻塞）
        # initialize() 内部会创建异步任务，不会阻塞
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
        import sys
        # 将日志输出到 stderr，避免干扰 MCP 协议的 stdout
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr
        )
        
        server = cls(config_path)
        await server.run()


def get_mcp_server(config_path: str) -> Optional["McpServer"]:
    """获取全局的 McpServer 实例"""
    return _global_mcp_servers.get(str(config_path))


async def run_server(config_path: str) -> None:
    """运行服务器（便捷函数）"""
    await McpServer.main(config_path)

