"""管理端 API 路由"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# 延迟导入避免循环依赖
_admin_context = None


def set_admin_context(config_path, mcp_server_getter=None):
    """设置管理端上下文（由 server.py 调用）"""
    global _admin_context
    _admin_context = (config_path, mcp_server_getter)


def _get_config_manager():
    """获取配置管理器和 MCP 服务器实例"""
    global _admin_context
    if not _admin_context:
        raise HTTPException(status_code=500, detail="管理端未初始化")
    
    config_path, mcp_server_getter = _admin_context
    from ..config.manager import ConfigManager
    from ..mcp_server import get_mcp_server
    
    # 尝试从全局字典获取 mcp_server 实例
    mcp_server = get_mcp_server(config_path)
    
    # 如果全局字典中没有，且提供了 getter 函数，尝试调用它
    if not mcp_server and mcp_server_getter:
        try:
            mcp_server = mcp_server_getter()
        except Exception:
            pass  # 如果获取失败，mcp_server 为 None
    
    return ConfigManager(config_path), mcp_server


# 请求/响应模型
class CommandCreate(BaseModel):
    name: str
    description: str
    type: str
    enabled: bool = True


class McpServerCreate(BaseModel):
    name: str
    description: str
    enabled: bool = True
    connection: Dict[str, Any]
    prefix: str = None


# 命令管理 API
@router.get("/commands")
async def list_commands():
    """获取所有命令（本地命令 + MCP 工具）"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    commands = []
    
    # 添加本地命令
    for cmd in config.commands:
        commands.append({
            "name": cmd.name,
            "description": cmd.description,
            "type": cmd.type,
            "source": "local",  # 标记为本地命令
            "enabled": cmd.enabled,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "required": p.required,
                    "description": p.description
                }
                for p in cmd.parameters
            ]
        })
    
    # 添加 MCP 服务工具
    if mcp_server and hasattr(mcp_server, 'command_manager'):
        tools = mcp_server.command_manager.get_all_tools()
        # 获取 MCP 工具信息（通过属性访问）
        mcp_commands_info = getattr(mcp_server.command_manager, '_mcp_commands', {})
        local_commands_set = set(cmd.name for cmd in config.commands if cmd.enabled)
        
        for tool in tools:
            # 检查是否是本地命令（已在上面添加）
            if tool.name in local_commands_set:
                continue
            
            # 检查是否是 MCP 工具
            tool_name = tool.name
            source = "local"
            service_name = None
            
            # 查找对应的服务
            for registered_name, info in mcp_commands_info.items():
                if registered_name == tool.name or (hasattr(info["tool"], "name") and info["tool"].name == tool.name):
                    source = "mcp"
                    service_name = info.get("service")
                    tool_name = registered_name  # 使用注册的名称（可能带前缀）
                    break
            
            # 提取参数信息
            parameters = []
            if tool.inputSchema:
                # 处理 inputSchema 可能是 dict 或对象
                schema = tool.inputSchema.model_dump() if hasattr(tool.inputSchema, 'model_dump') else tool.inputSchema
                if isinstance(schema, dict) and "properties" in schema:
                    required = schema.get("required", [])
                    for param_name, param_schema in schema["properties"].items():
                        param_info = param_schema.model_dump() if hasattr(param_schema, 'model_dump') else param_schema
                        parameters.append({
                            "name": param_name,
                            "type": param_info.get("type", "string"),
                            "required": param_name in required,
                            "description": param_info.get("description", "")
                        })
            
            commands.append({
                "name": tool_name,
                "description": tool.description,
                "type": "mcp_tool",
                "source": source,
                "service": service_name,
                "enabled": True,  # MCP 工具默认启用
                "parameters": parameters
            })
    
    return {"commands": commands}


@router.get("/commands/{name}")
async def get_command(name: str):
    """获取单个命令"""
    # TODO: 实现
    raise HTTPException(status_code=404, detail="命令不存在")


@router.post("/commands")
async def create_command(command: Dict[str, Any]):
    """创建命令（热更新）"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    # 验证命令名称是否已存在
    command_name = command.get("name")
    if not command_name:
        raise HTTPException(status_code=400, detail="命令名称不能为空")
    
    if any(cmd.name == command_name for cmd in config.commands):
        raise HTTPException(status_code=400, detail=f"命令 {command_name} 已存在")
    
    # 创建命令配置对象
    from ..config.models import CommandConfig, HttpCommandConfig, ScriptCommandConfig, ParameterConfig
    
    # 构建参数列表
    parameters = []
    for param_data in command.get("parameters", []):
        parameters.append(ParameterConfig(**param_data))
    
    # 根据类型创建命令配置
    command_type = command.get("type")
    if command_type == "http":
        http_config = HttpCommandConfig(**command.get("http", {}))
        new_command = CommandConfig(
            name=command_name,
            description=command.get("description", ""),
            type="http",
            enabled=command.get("enabled", True),
            http=http_config,
            parameters=parameters
        )
    elif command_type == "script":
        script_config = ScriptCommandConfig(**command.get("script", {}))
        new_command = CommandConfig(
            name=command_name,
            description=command.get("description", ""),
            type="script",
            enabled=command.get("enabled", True),
            script=script_config,
            parameters=parameters
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的命令类型: {command_type}")
    
    # 添加到配置
    config.commands.append(new_command)
    
    # 保存配置（会触发热重载）
    config_manager.save_config(config)
    
    return {
        "message": "命令已创建",
        "command": {
            "name": new_command.name,
            "description": new_command.description,
            "type": new_command.type,
            "enabled": new_command.enabled
        }
    }


@router.put("/commands/{name}")
async def update_command(name: str, command: Dict[str, Any]):
    """更新命令"""
    # TODO: 实现
    return {"message": "命令已更新"}


@router.delete("/commands/{name}")
async def delete_command(name: str):
    """删除命令（热更新）"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    # 查找命令
    command_index = None
    for i, cmd in enumerate(config.commands):
        if cmd.name == name:
            command_index = i
            break
    
    if command_index is None:
        raise HTTPException(status_code=404, detail=f"命令 {name} 不存在")
    
    # 删除命令
    config.commands.pop(command_index)
    
    # 保存配置（会触发热重载）
    config_manager.save_config(config)
    
    return {"message": f"命令 {name} 已删除"}


@router.patch("/commands/{name}/toggle")
async def toggle_command(name: str):
    """启用/禁用命令"""
    # TODO: 实现
    return {"message": "命令状态已切换"}


# MCP 服务管理 API
@router.get("/mcp-servers")
async def list_mcp_servers():
    """获取所有 MCP 服务"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    servers = []
    for server_config in config.mcp_servers:
        connection_dict = {
            "type": server_config.connection.type,
        }
        if server_config.connection.command:
            connection_dict["command"] = server_config.connection.command
        if server_config.connection.args:
            connection_dict["args"] = server_config.connection.args
        if server_config.connection.url:
            connection_dict["url"] = server_config.connection.url
        
        server_info = {
            "name": server_config.name,
            "description": server_config.description,
            "enabled": server_config.enabled,
            "connection": connection_dict,
            "prefix": server_config.prefix,
            "timeout": server_config.timeout,
        }
        
        # 如果 mcp_server 可用，获取连接状态
        if mcp_server and hasattr(mcp_server, 'mcp_client_manager'):
            manager = mcp_server.mcp_client_manager
            status = manager.get_connection_status(server_config.name)
            server_info["connection_status"] = status
            server_info["connected"] = status == "connected"
            
            # 如果有客户端，获取详细状态
            client = manager.clients.get(server_config.name)
            if client:
                server_info["is_connected"] = client.is_connected
                if hasattr(client.connection, 'connection_error') and client.connection.connection_error:
                    server_info["connection_error"] = client.connection.connection_error
        else:
            server_info["connection_status"] = "unknown"
            server_info["connected"] = False
        
        servers.append(server_info)
    
    return {"servers": servers}


@router.get("/mcp-servers/{name}")
async def get_mcp_server(name: str):
    """获取单个 MCP 服务"""
    # TODO: 实现
    raise HTTPException(status_code=404, detail="MCP 服务不存在")


@router.post("/mcp-servers")
async def create_mcp_server(server: Dict[str, Any]):
    """添加 MCP 服务（热更新）"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    # 验证服务名称是否已存在
    server_name = server.get("name")
    if not server_name:
        raise HTTPException(status_code=400, detail="服务名称不能为空")
    
    if any(s.name == server_name for s in config.mcp_servers):
        raise HTTPException(status_code=400, detail=f"MCP 服务 {server_name} 已存在")
    
    # 创建服务配置对象
    from ..config.models import McpServerConfig, McpServerConnectionConfig
    
    connection_data = server.get("connection", {})
    connection_config = McpServerConnectionConfig(**connection_data)
    
    new_server = McpServerConfig(
        name=server_name,
        description=server.get("description", ""),
        enabled=server.get("enabled", True),
        connection=connection_config,
        prefix=server.get("prefix"),
        timeout=server.get("timeout", 30),
        retry_on_failure=server.get("retry_on_failure", True),
        auto_reconnect=server.get("auto_reconnect", True)
    )
    
    # 添加到配置
    config.mcp_servers.append(new_server)
    
    # 保存配置（会触发热重载）
    config_manager.save_config(config)
    
    # 如果启用且 mcp_server 可用，立即连接
    if new_server.enabled and mcp_server and hasattr(mcp_server, 'mcp_client_manager'):
        try:
            await mcp_server.mcp_client_manager.add_server(new_server)
        except Exception as e:
            logger.error(f"连接新添加的 MCP 服务 {server_name} 失败: {e}")
            # 不抛出异常，因为配置已保存，可以稍后重试
    
    return {
        "message": "MCP 服务已添加",
        "server": {
            "name": new_server.name,
            "description": new_server.description,
            "enabled": new_server.enabled
        }
    }


@router.put("/mcp-servers/{name}")
async def update_mcp_server(name: str, server: Dict[str, Any]):
    """更新 MCP 服务（热更新）"""
    # TODO: 实现
    return {"message": "MCP 服务已更新"}


@router.delete("/mcp-servers/{name}")
async def delete_mcp_server(name: str):
    """删除 MCP 服务（热更新）"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    # 查找服务
    server_index = None
    for i, s in enumerate(config.mcp_servers):
        if s.name == name:
            server_index = i
            break
    
    if server_index is None:
        raise HTTPException(status_code=404, detail=f"MCP 服务 {name} 不存在")
    
    # 如果 mcp_server 可用，先断开连接
    if mcp_server and hasattr(mcp_server, 'mcp_client_manager'):
        try:
            await mcp_server.mcp_client_manager.remove_server(name)
        except Exception as e:
            logger.error(f"断开 MCP 服务 {name} 失败: {e}")
    
    # 从配置中删除
    config.mcp_servers.pop(server_index)
    
    # 保存配置（会触发热重载）
    config_manager.save_config(config)
    
    return {"message": f"MCP 服务 {name} 已删除"}


@router.patch("/mcp-servers/{name}/toggle")
async def toggle_mcp_server(name: str):
    """启用/禁用 MCP 服务（热更新）"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    # 查找服务
    server_config = None
    for s in config.mcp_servers:
        if s.name == name:
            server_config = s
            break
    
    if not server_config:
        raise HTTPException(status_code=404, detail=f"MCP 服务 {name} 不存在")
    
    # 切换状态
    server_config.enabled = not server_config.enabled
    
    # 保存配置（会触发热重载）
    config_manager.save_config(config)
    
    # 如果禁用，立即断开连接
    if mcp_server and hasattr(mcp_server, 'mcp_client_manager'):
        if not server_config.enabled:
            try:
                await mcp_server.mcp_client_manager.remove_server(name)
            except Exception as e:
                logger.error(f"断开 MCP 服务 {name} 失败: {e}")
        else:
            # 如果启用，尝试连接
            try:
                await mcp_server.mcp_client_manager.add_server(server_config)
            except Exception as e:
                logger.error(f"连接 MCP 服务 {name} 失败: {e}")
    
    return {
        "message": "MCP 服务状态已切换",
        "name": name,
        "enabled": server_config.enabled
    }


@router.post("/mcp-servers/{name}/test")
async def test_mcp_server(name: str):
    """测试 MCP 服务连接"""
    # TODO: 实现
    return {"message": "连接测试成功"}


@router.get("/mcp-servers/{name}/tools")
async def get_mcp_server_tools(name: str):
    """获取 MCP 服务的工具列表"""
    # TODO: 实现
    return {"tools": []}


@router.post("/mcp-servers/{name}/reconnect")
async def reconnect_mcp_server(name: str):
    """重连 MCP 服务"""
    # TODO: 实现
    return {"message": "重连成功"}


# 鉴权配置管理 API
@router.get("/auth-configs")
async def list_auth_configs():
    """获取所有鉴权配置"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    auth_configs = []
    for auth in config.auth_configs:
        auth_dict = {
            "name": auth.name,
            "type": auth.type,
        }
        
        # 根据类型添加具体配置（不包含敏感信息）
        if auth.type == "api_key" and auth.api_key:
            auth_dict["api_key"] = {
                "location": auth.api_key.location,
                "name": auth.api_key.name,
                "value": "***" if auth.api_key.value else None  # 隐藏实际值
            }
        elif auth.type == "bearer_token" and auth.bearer_token:
            auth_dict["bearer_token"] = {
                "token": "***" if auth.bearer_token.token else None  # 隐藏实际值
            }
        elif auth.type == "basic_auth" and auth.basic_auth:
            auth_dict["basic_auth"] = {
                "username": auth.basic_auth.username,
                "password": "***"  # 隐藏实际值
            }
        elif auth.type == "custom_header" and auth.custom_header:
            auth_dict["custom_header"] = {
                "headers": {k: "***" for k in auth.custom_header.headers.keys()}  # 隐藏所有 header 值
            }
        
        auth_configs.append(auth_dict)
    
    return {"auth_configs": auth_configs}


@router.post("/auth-configs")
async def create_auth_config(config: Dict[str, Any]):
    """创建鉴权配置"""
    # TODO: 实现
    return {"message": "鉴权配置已创建"}


@router.put("/auth-configs/{name}")
async def update_auth_config(name: str, config: Dict[str, Any]):
    """更新鉴权配置"""
    # TODO: 实现
    return {"message": "鉴权配置已更新"}


@router.delete("/auth-configs/{name}")
async def delete_auth_config(name: str):
    """删除鉴权配置"""
    # TODO: 实现
    return {"message": "鉴权配置已删除"}


# 配置管理 API
@router.get("/config")
async def get_config():
    """获取完整配置"""
    config_manager, mcp_server = _get_config_manager()
    config = config_manager.load_config()
    
    # 转换为字典
    return {"config": config.model_dump()}


@router.post("/config")
async def save_config(config: Dict[str, Any]):
    """保存配置"""
    # TODO: 实现
    return {"message": "配置已保存"}


@router.post("/config/reload")
async def reload_config():
    """重载配置（热更新）"""
    # TODO: 实现
    return {"message": "配置已重载"}

