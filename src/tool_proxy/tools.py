"""工具代理工具定义"""

import json
import logging
from typing import Any, Dict, List
from mcp.types import Tool

from ..tool_index.manager import ToolIndexManager
from ..mcp_client.manager import McpClientManager
from ..config.models import Config

logger = logging.getLogger(__name__)


def create_proxy_tools(
    tool_index_manager: ToolIndexManager,
    mcp_client_manager: McpClientManager,
    config: Config
) -> List[Tool]:
    """创建代理工具"""
    tools = []
    proxy_config = config.global_config.tool_proxy
    
    # 搜索工具
    if proxy_config.enable_search:
        tools.append(_create_search_tool(tool_index_manager, proxy_config))
    
    # 执行工具
    if proxy_config.enable_execute:
        tools.append(_create_execute_tool(tool_index_manager, mcp_client_manager, config))
    
    # 服务列表工具
    if proxy_config.enable_list_services:
        tools.append(_create_list_services_tool(tool_index_manager, mcp_client_manager))
    
    return tools


def _create_search_tool(tool_index_manager: ToolIndexManager, proxy_config) -> Tool:
    """创建搜索工具"""
    return Tool(
        name="mcp_search_tools",
        description="搜索可用的 MCP 工具。通过关键词搜索工具名称、描述、参数等信息。",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，支持模糊匹配工具名称、描述、参数等"
                },
                "service_name": {
                    "type": "string",
                    "description": "可选：按服务名称过滤结果"
                },
                "limit": {
                    "type": "number",
                    "description": f"返回结果数量限制，默认 {proxy_config.search_limit}",
                    "default": proxy_config.search_limit
                }
            },
            "required": ["query"]
        }
    )


def _create_execute_tool(
    tool_index_manager: ToolIndexManager,
    mcp_client_manager: McpClientManager,
    config: Config
) -> Tool:
    """创建执行工具"""
    return Tool(
        name="mcp_execute_tool",
        description="执行指定的 MCP 工具。通过工具名称和参数执行相应的 MCP 命令。",
        inputSchema={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "要执行的工具名称（可以是显示名称或原始名称）"
                },
                "arguments": {
                    "type": "object",
                    "description": "工具参数，JSON 对象格式"
                }
            },
            "required": ["tool_name", "arguments"]
        }
    )


def _create_list_services_tool(
    tool_index_manager: ToolIndexManager,
    mcp_client_manager: McpClientManager
) -> Tool:
    """创建服务列表工具"""
    return Tool(
        name="mcp_list_services",
        description="列出所有已连接的 MCP 服务及其状态。",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )


async def handle_search_tools(
    tool_index_manager: ToolIndexManager,
    query: str,
    service_name: str = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """处理工具搜索"""
    results = tool_index_manager.search(query, service_name, limit)
    
    return {
        "tools": [tool.to_dict() for tool in results],
        "total": len(results),
        "limit": limit,
        "query": query,
        "service_name": service_name
    }


async def handle_execute_tool(
    tool_index_manager: ToolIndexManager,
    mcp_client_manager: McpClientManager,
    config: Config,
    tool_name: str,
    arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """处理工具执行"""
    # 查找工具索引
    tool_index = tool_index_manager.get_tool(tool_name)
    if not tool_index:
        return {
            "success": False,
            "error": f"工具不存在: {tool_name}",
            "result": None
        }
    
    # 验证参数
    required_params = [
        name for name, info in tool_index.parameters.items()
        if info.get("required", False)
    ]
    
    missing_params = [param for param in required_params if param not in arguments]
    if missing_params:
        return {
            "success": False,
            "error": f"缺少必需参数: {', '.join(missing_params)}",
            "result": None
        }
    
    try:
        # 调用 MCP 服务工具
        result = await mcp_client_manager.call_tool(
            tool_index.service_name,
            tool_index.name,  # 使用原始名称
            arguments
        )
        
        # 转换结果格式
        contents = []
        for content in result.content:
            if content.type == "text":
                contents.append(content.text)
            else:
                contents.append(str(content))
        
        result_text = "\n".join(contents) if len(contents) > 1 else (contents[0] if contents else "")
        
        return {
            "success": True,
            "error": None,
            "result": result_text,
            "tool_name": tool_index.display_name,
            "service": tool_index.service_name
        }
    
    except Exception as e:
        logger.error(f"执行工具 {tool_name} 失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "result": None
        }


async def handle_list_services(
    tool_index_manager: ToolIndexManager,
    mcp_client_manager: McpClientManager
) -> Dict[str, Any]:
    """处理服务列表"""
    services = []
    all_services = tool_index_manager.get_all_services()
    connection_status = mcp_client_manager.get_all_connection_status()
    
    for service_name in all_services:
        tools = tool_index_manager.get_service_tools(service_name)
        status = connection_status.get(service_name, "unknown")
        
        services.append({
            "name": service_name,
            "description": tools[0].service_description if tools else "",
            "status": status,
            "tool_count": len(tools)
        })
    
    return {
        "services": services,
        "total": len(services)
    }

