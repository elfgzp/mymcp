"""工具搜索引擎 - 基于 Whoosh"""

import logging
from typing import List, Optional, Dict, Any
from io import BytesIO

try:
    from whoosh import index
    from whoosh.fields import Schema, TEXT, ID, STORED
    from whoosh.qparser import QueryParser, MultifieldParser
    from whoosh.query import And, Or, Term
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False

from .models import ToolIndex

logger = logging.getLogger(__name__)


class WhooshSearchEngine:
    """基于 Whoosh 的搜索引擎"""
    
    def __init__(self):
        if not WHOOSH_AVAILABLE:
            raise ImportError(
                "Whoosh 未安装。请运行: pip install whoosh\n"
                "或者使用 SimpleSearchEngine（无需额外依赖）"
            )
        
        # 定义 schema
        self.schema = Schema(
            display_name=ID(stored=True),  # 工具显示名称（唯一）
            name=TEXT(stored=True),  # 原始工具名
            description=TEXT(stored=True),  # 工具描述
            service_name=ID(stored=True),  # 服务名称
            service_description=TEXT(stored=True),  # 服务描述
            parameters=TEXT(stored=True),  # 参数字符串（用于搜索）
            content=TEXT  # 全文搜索字段（包含所有可搜索内容）
        )
        
        # 创建内存索引
        self._index = index.create_index(self.schema, indexname="memory")
        self._writer = None
        self._tool_count = 0
    
    def add_tool(self, tool_index: ToolIndex) -> None:
        """添加工具到索引"""
        if self._writer is None:
            self._writer = self._index.writer()
        
        # 构建参数字符串（用于搜索）
        params_text = " ".join([
            f"{name} {info.get('description', '')}"
            for name, info in tool_index.parameters.items()
        ])
        
        # 构建全文搜索内容
        content = " ".join([
            tool_index.display_name,
            tool_index.name,
            tool_index.description,
            tool_index.service_name,
            tool_index.service_description,
            params_text
        ])
        
        self._writer.add_document(
            display_name=tool_index.display_name,
            name=tool_index.name,
            description=tool_index.description,
            service_name=tool_index.service_name,
            service_description=tool_index.service_description,
            parameters=params_text,
            content=content
        )
        self._tool_count += 1
    
    def commit(self) -> None:
        """提交索引更改"""
        if self._writer is not None:
            self._writer.commit()
            self._writer = None
    
    def search(
        self,
        query: str,
        service_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索工具"""
        if self._tool_count == 0:
            return []
        
        # 确保索引已提交
        if self._writer is not None:
            self.commit()
        
        with self._index.searcher() as searcher:
            # 构建查询
            query_parts = []
            
            # 主查询（全文搜索）
            if query:
                # 使用 MultifieldParser 在多个字段中搜索
                parser = MultifieldParser(
                    ["content", "name", "display_name", "description"],
                    schema=self.schema
                )
                main_query = parser.parse(query)
                query_parts.append(main_query)
            
            # 服务过滤
            if service_name:
                query_parts.append(Term("service_name", service_name))
            
            # 组合查询
            if len(query_parts) == 1:
                final_query = query_parts[0]
            elif len(query_parts) > 1:
                final_query = And(query_parts)
            else:
                # 无查询条件，返回所有
                final_query = None
            
            # 执行搜索
            if final_query:
                results = searcher.search(final_query, limit=limit)
            else:
                # 返回所有结果
                results = searcher.documents()[:limit]
            
            # 转换为字典列表
            return [
                {
                    "display_name": hit["display_name"],
                    "name": hit["name"],
                    "description": hit["description"],
                    "service_name": hit["service_name"],
                    "service_description": hit["service_description"],
                    "score": hit.score if hasattr(hit, "score") else 0.0
                }
                for hit in results
            ]
    
    def remove_service_tools(self, service_name: str) -> None:
        """移除服务的所有工具（需要重建索引）"""
        # Whoosh 不支持直接删除，需要重建索引
        # 这个方法标记需要重建索引
        # 注意：实际删除操作由 ToolIndexManager 处理
        logger.debug(f"Whoosh 索引需要重建以移除服务 {service_name} 的工具")
    
    def clear(self) -> None:
        """清空索引"""
        # 重新创建索引
        self._index = index.create_index(self.schema, indexname="memory")
        self._writer = None
        self._tool_count = 0


class SimpleSearchEngine:
    """简单的搜索引擎（无需额外依赖，基于字符串匹配）"""
    
    def __init__(self):
        self._tools: List[ToolIndex] = []
    
    def add_tool(self, tool_index: ToolIndex) -> None:
        """添加工具到索引"""
        self._tools.append(tool_index)
    
    def commit(self) -> None:
        """提交索引更改（简单引擎无需提交）"""
        pass
    
    def search(
        self,
        query: str,
        service_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索工具"""
        results = []
        
        for tool_index in self._tools:
            # 服务过滤
            if service_name and tool_index.service_name != service_name:
                continue
            
            # 匹配检查
            if not query or tool_index.matches_query(query):
                score = tool_index.get_match_score(query) if query else 0
                results.append({
                    "display_name": tool_index.display_name,
                    "name": tool_index.name,
                    "description": tool_index.description,
                    "service_name": tool_index.service_name,
                    "service_description": tool_index.service_description,
                    "score": score
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:limit]
    
    def remove_service_tools(self, service_name: str) -> None:
        """移除服务的所有工具"""
        self._tools = [
            tool for tool in self._tools
            if tool.service_name != service_name
        ]
    
    def clear(self) -> None:
        """清空索引"""
        self._tools.clear()


def create_search_engine(use_whoosh: bool = True) -> Any:
    """创建搜索引擎"""
    if use_whoosh and WHOOSH_AVAILABLE:
        try:
            return WhooshSearchEngine()
        except Exception as e:
            logger.warning(f"创建 Whoosh 搜索引擎失败，使用简单引擎: {e}")
            return SimpleSearchEngine()
    else:
        return SimpleSearchEngine()

