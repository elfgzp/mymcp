"""工具索引数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ToolIndex:
    """工具索引项"""
    
    name: str  # 原始工具名
    display_name: str  # 显示名称（带前缀）
    description: str
    service_name: str
    service_description: str
    parameters: Dict[str, Any]  # 参数定义
    input_schema: Dict[str, Any]  # 完整的输入 schema
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "service": self.service_name,
            "service_description": self.service_description,
            "parameters": self.parameters,
            "input_schema": self.input_schema,
        }
    
    def matches_query(self, query: str) -> bool:
        """检查是否匹配搜索关键词"""
        query_lower = query.lower()
        
        # 名称匹配
        if query_lower in self.name.lower() or query_lower in self.display_name.lower():
            return True
        
        # 描述匹配
        if query_lower in self.description.lower():
            return True
        
        # 服务名称匹配
        if query_lower in self.service_name.lower() or query_lower in self.service_description.lower():
            return True
        
        # 参数匹配
        for param_name, param_info in self.parameters.items():
            if query_lower in param_name.lower():
                return True
            if isinstance(param_info, dict) and "description" in param_info:
                if query_lower in param_info["description"].lower():
                    return True
        
        return False
    
    def get_match_score(self, query: str) -> int:
        """获取匹配分数（用于排序）"""
        query_lower = query.lower()
        score = 0
        
        # 名称完全匹配（最高分）
        if query_lower == self.name.lower() or query_lower == self.display_name.lower():
            score += 100
        # 名称前缀匹配
        elif self.name.lower().startswith(query_lower) or self.display_name.lower().startswith(query_lower):
            score += 50
        # 名称包含
        elif query_lower in self.name.lower() or query_lower in self.display_name.lower():
            score += 30
        
        # 描述匹配
        if query_lower in self.description.lower():
            score += 10
        
        # 参数匹配
        for param_name, param_info in self.parameters.items():
            if query_lower in param_name.lower():
                score += 5
            if isinstance(param_info, dict) and "description" in param_info:
                if query_lower in param_info["description"].lower():
                    score += 3
        
        return score

