# 工具代理模式使用指南

## 概述

工具代理模式是 MyMCP 的性能优化功能，通过减少暴露给 Cursor 的工具数量来提升性能。

## 工作原理

### 传统模式（默认）

- 所有 MCP 工具直接暴露给 Cursor
- 工具数量可能达到几十甚至上百个
- Cursor 加载工具列表时性能较慢

### 代理模式

- 只暴露 2-3 个核心工具：
  - `mcp_search_tools` - 搜索可用工具
  - `mcp_execute_tool` - 执行指定工具
  - `mcp_list_services` - 列出所有服务
- 所有其他工具通过索引系统管理
- 大模型先搜索工具，再执行

## 启用方式

在 `config.yaml` 中设置：

```yaml
global:
  tool_proxy_mode: true  # 启用工具代理模式
  tool_proxy:
    enable_search: true
    enable_execute: true
    enable_list_services: true
    search_limit: 20
```

## 使用示例

### 1. 搜索工具

```json
{
  "name": "mcp_search_tools",
  "arguments": {
    "query": "read file",
    "service_name": "filesystem",
    "limit": 10
  }
}
```

返回结果：
```json
{
  "tools": [
    {
      "name": "read_file",
      "display_name": "fs_read_file",
      "description": "读取文件内容",
      "service": "filesystem",
      "parameters": {
        "path": {
          "type": "string",
          "description": "文件路径",
          "required": true
        }
      }
    }
  ],
  "total": 1,
  "limit": 10
}
```

### 2. 执行工具

```json
{
  "name": "mcp_execute_tool",
  "arguments": {
    "tool_name": "fs_read_file",
    "arguments": {
      "path": "/path/to/file.txt"
    }
  }
}
```

返回结果：
```json
{
  "success": true,
  "result": "文件内容...",
  "error": null,
  "tool_name": "fs_read_file",
  "service": "filesystem"
}
```

### 3. 列出服务

```json
{
  "name": "mcp_list_services",
  "arguments": {}
}
```

返回结果：
```json
{
  "services": [
    {
      "name": "filesystem",
      "description": "文件系统操作服务",
      "status": "connected",
      "tool_count": 15
    }
  ],
  "total": 1
}
```

## 搜索功能

### 搜索策略

工具索引系统支持以下搜索方式：

1. **名称匹配**：工具名称包含关键词
2. **描述匹配**：工具描述包含关键词
3. **参数匹配**：参数名称或描述包含关键词
4. **服务匹配**：服务名称或描述包含关键词

### 搜索排序

结果按相关性排序：
- 名称完全匹配（最高优先级）
- 名称前缀匹配
- 名称包含匹配
- 描述匹配
- 参数匹配

## 搜索引擎

MyMCP 支持两种搜索引擎：

### 1. Whoosh（推荐）

- 纯 Python 实现
- 支持全文搜索
- 更好的搜索质量
- 需要安装：`pip install whoosh` 或 `uv pip install "mymcp[search]"`

### 2. 简单引擎（默认）

- 无需额外依赖
- 基于字符串匹配
- 适合工具数量较少的情况（< 1000）

## 性能优化

### 优势

1. **减少工具数量**：从几十/上百个工具减少到 2-3 个
2. **提升加载速度**：Cursor 加载工具列表更快
3. **更好的搜索体验**：支持全文搜索和相关性排序
4. **保持功能完整**：不丢失任何原有功能

### 适用场景

- MCP 工具数量较多（> 20 个）
- 需要频繁搜索工具
- 对性能有要求

### 不适用场景

- MCP 工具数量较少（< 10 个）
- 需要直接访问所有工具
- 对延迟敏感（需要直接调用）

## 向后兼容

- 默认保持传统模式（`tool_proxy_mode: false`）
- 可以随时切换模式
- 不影响现有配置

## 故障排查

### 问题：搜索无结果

1. 检查 MCP 服务是否已连接
2. 检查搜索关键词是否正确
3. 查看日志确认工具索引是否已建立

### 问题：执行工具失败

1. 检查工具名称是否正确（支持显示名称和原始名称）
2. 检查参数是否完整（特别是必需参数）
3. 查看错误信息了解具体原因

### 问题：Whoosh 未安装

如果看到 "Whoosh 未安装" 警告：
- 安装 Whoosh：`pip install whoosh` 或 `uv pip install "mymcp[search]"`
- 或者使用简单引擎（无需安装，但搜索质量略低）

