"""命令管理器"""

from typing import Dict, List, Optional, Any
from mcp.types import Tool, TextContent

from ..config.models import CommandConfig, Config
from .executor import CommandExecutor
from ..auth.manager import AuthManager


class CommandManager:
    """命令管理器"""

    def __init__(self, config: Config, auth_manager: AuthManager):
        self.config = config
        self.auth_manager = auth_manager
        self.executor = CommandExecutor(config, auth_manager)
        self._local_commands: Dict[str, CommandConfig] = {}
        self._mcp_commands: Dict[str, Dict[str, Any]] = {}  # {tool_name: {service, tool}}
        self._build_local_commands()

    def _build_local_commands(self) -> None:
        """构建本地命令索引"""
        self._local_commands = {
            cmd.name: cmd for cmd in self.config.commands if cmd.enabled
        }

    def register_mcp_tool(self, service_name: str, tool: Tool, prefix: Optional[str] = None) -> None:
        """注册 MCP 服务工具"""
        tool_name = f"{prefix}_{tool.name}" if prefix else tool.name
        self._mcp_commands[tool_name] = {
            "service": service_name,
            "tool": tool,
            "original_name": tool.name
        }

    def unregister_mcp_tools(self, service_name: str) -> None:
        """注销 MCP 服务工具"""
        to_remove = [
            name for name, info in self._mcp_commands.items()
            if info["service"] == service_name
        ]
        for name in to_remove:
            del self._mcp_commands[name]

    def get_all_tools(self) -> List[Tool]:
        """获取所有工具（本地 + MCP）"""
        tools = []
        
        # 添加本地命令
        for cmd in self._local_commands.values():
            tools.append(self._command_to_tool(cmd))
        
        # 添加 MCP 服务工具
        for tool_info in self._mcp_commands.values():
            tools.append(tool_info["tool"])
        
        return tools

    def _command_to_tool(self, command: CommandConfig) -> Tool:
        """将命令配置转换为 Tool"""
        properties = {}
        required = []
        
        for param in command.parameters:
            param_type = param.type
            if param_type == "string":
                schema_type = "string"
            elif param_type == "number":
                schema_type = "number"
            elif param_type == "boolean":
                schema_type = "boolean"
            elif param_type == "array":
                schema_type = "array"
            elif param_type == "object":
                schema_type = "object"
            else:
                schema_type = "string"
            
            properties[param.name] = {
                "type": schema_type,
                "description": param.description or ""
            }
            
            if param.required:
                required.append(param.name)
        
        return Tool(
            name=command.name,
            description=command.description,
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": required
            }
        )

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """调用工具"""
        # 检查是否是本地命令
        if name in self._local_commands:
            command = self._local_commands[name]
            result = await self.executor.execute(command, arguments)
            
            # 转换为 TextContent
            if isinstance(result, (dict, list)):
                import json
                text = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                text = str(result)
            
            return [TextContent(type="text", text=text)]
        
        # 检查是否是 MCP 服务工具
        if name in self._mcp_commands:
            # MCP 工具调用由 MCP Client Manager 处理
            raise ValueError(f"MCP 工具 {name} 应由 MCP Client Manager 处理")
        
        raise ValueError(f"工具不存在: {name}")

    def reload(self, config: Config) -> None:
        """重新加载配置"""
        self.config = config
        self._build_local_commands()

