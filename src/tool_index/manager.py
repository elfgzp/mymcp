"""工具索引管理器"""

import logging
from typing import Dict, List, Optional
from mcp.types import Tool

from .models import ToolIndex
from .search_engine import create_search_engine, SimpleSearchEngine

logger = logging.getLogger(__name__)


class ToolIndexManager:
    """工具索引管理器"""
    
    def __init__(self, use_whoosh: bool = True):
        # 索引存储：{display_name: ToolIndex}
        self._index: Dict[str, ToolIndex] = {}
        # 服务工具映射：{service_name: [display_names]}
        self._service_tools: Dict[str, List[str]] = {}
        # 搜索引擎
        self._search_engine = create_search_engine(use_whoosh=use_whoosh)
    
    def add_tool(
        self,
        tool: Tool,
        service_name: str,
        service_description: str,
        prefix: Optional[str] = None
    ) -> None:
        """添加工具到索引"""
        display_name = f"{prefix}_{tool.name}" if prefix else tool.name
        
        # 提取参数信息
        parameters = {}
        input_schema = tool.inputSchema or {}
        if isinstance(input_schema, dict):
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            for param_name, param_schema in properties.items():
                parameters[param_name] = {
                    "type": param_schema.get("type", "string"),
                    "description": param_schema.get("description", ""),
                    "required": param_name in required
                }
        
        tool_index = ToolIndex(
            name=tool.name,
            display_name=display_name,
            description=tool.description or "",
            service_name=service_name,
            service_description=service_description,
            parameters=parameters,
            input_schema=input_schema
        )
        
        self._index[display_name] = tool_index
        
        # 更新服务工具映射
        if service_name not in self._service_tools:
            self._service_tools[service_name] = []
        if display_name not in self._service_tools[service_name]:
            self._service_tools[service_name].append(display_name)
        
        # 添加到搜索引擎
        self._search_engine.add_tool(tool_index)
        self._search_engine.commit()
        
        logger.debug(f"已添加工具到索引: {display_name} (服务: {service_name})")
    
    def remove_service_tools(self, service_name: str) -> None:
        """移除服务的所有工具"""
        if service_name not in self._service_tools:
            return
        
        display_names = self._service_tools[service_name]
        for display_name in display_names:
            if display_name in self._index:
                del self._index[display_name]
        
        del self._service_tools[service_name]
        
        # 从搜索引擎移除
        self._search_engine.remove_service_tools(service_name)
        # 如果是简单引擎，需要重建索引
        if isinstance(self._search_engine, SimpleSearchEngine):
            # 重建索引
            self._search_engine.clear()
            for tool_index in self._index.values():
                self._search_engine.add_tool(tool_index)
            self._search_engine.commit()
        
        logger.debug(f"已移除服务 {service_name} 的所有工具 ({len(display_names)} 个)")
    
    def search(
        self,
        query: str,
        service_name: Optional[str] = None,
        limit: int = 20
    ) -> List[ToolIndex]:
        """搜索工具（使用搜索引擎）"""
        # 使用搜索引擎搜索
        search_results = self._search_engine.search(query, service_name, limit)
        
        # 转换为 ToolIndex 列表
        results = []
        for result in search_results:
            display_name = result["display_name"]
            if display_name in self._index:
                results.append(self._index[display_name])
        
        return results
    
    def get_tool(self, tool_name: str) -> Optional[ToolIndex]:
        """获取工具索引（支持显示名称和原始名称）"""
        # 先尝试显示名称
        if tool_name in self._index:
            return self._index[tool_name]
        
        # 尝试原始名称
        for tool_index in self._index.values():
            if tool_index.name == tool_name:
                return tool_index
        
        return None
    
    def get_service_tools(self, service_name: str) -> List[ToolIndex]:
        """获取服务的所有工具"""
        if service_name not in self._service_tools:
            return []
        
        tools = []
        for display_name in self._service_tools[service_name]:
            if display_name in self._index:
                tools.append(self._index[display_name])
        
        return tools
    
    def get_all_services(self) -> List[str]:
        """获取所有服务名称"""
        return list(self._service_tools.keys())
    
    def get_tool_count(self, service_name: Optional[str] = None) -> int:
        """获取工具数量"""
        if service_name:
            return len(self._service_tools.get(service_name, []))
        return len(self._index)
    
    def clear(self) -> None:
        """清空所有索引"""
        self._index.clear()
        self._service_tools.clear()
        self._search_engine.clear()
        logger.debug("已清空所有工具索引")

