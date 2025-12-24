# MCP 工具代理优化需求文档

## 背景

当前 MyMCP 将所有 MCP 工具直接暴露给 Cursor，导致：
- 工具数量过多（可能几十甚至上百个）
- Cursor 加载工具列表时性能过慢
- 工具列表过长，难以查找和使用

## 目标

优化 MyMCP，使其：
1. **减少暴露的工具数量**：只暴露 2-3 个核心工具
2. **提供搜索功能**：让大模型可以搜索可用的 MCP 工具
3. **提供执行功能**：通过通用化的工具执行接口来调用实际的 MCP 工具
4. **保持功能完整性**：不丢失任何原有功能

## 需求分析

### 1. 工具索引系统

需要建立一个工具索引/文档系统，包含：
- **工具元数据**：工具名称、描述、参数定义、所属服务等
- **可搜索性**：支持按名称、描述、参数等字段搜索
- **实时更新**：当 MCP 服务连接/断开时，自动更新索引

### 2. 核心工具设计

#### 2.1 `mcp_search_tools` - 工具搜索工具

**功能**：搜索可用的 MCP 工具

**参数**：
- `query` (string, required): 搜索关键词，支持模糊匹配
- `service_name` (string, optional): 按服务名称过滤
- `limit` (number, optional): 返回结果数量限制，默认 20

**返回**：
```json
{
  "tools": [
    {
      "name": "tool_name",
      "display_name": "fs_read_file",  // 带前缀的显示名称
      "description": "工具描述",
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
  "total": 50,
  "limit": 20
}
```

#### 2.2 `mcp_execute_tool` - 工具执行工具

**功能**：执行指定的 MCP 工具

**参数**：
- `tool_name` (string, required): 要执行的工具名称（可以是显示名称或原始名称）
- `arguments` (object, required): 工具参数，JSON 对象格式

**返回**：
```json
{
  "success": true,
  "result": "工具执行结果",
  "error": null
}
```

#### 2.3 `mcp_list_services` - 服务列表工具（可选）

**功能**：列出所有已连接的 MCP 服务

**参数**：无

**返回**：
```json
{
  "services": [
    {
      "name": "filesystem",
      "description": "文件系统操作服务",
      "status": "connected",
      "tool_count": 15
    }
  ]
}
```

### 3. 工具索引构建

#### 3.1 索引数据结构

```python
class ToolIndex:
    name: str  # 原始工具名
    display_name: str  # 显示名称（带前缀）
    description: str
    service_name: str
    service_description: str
    parameters: dict  # 参数定义
    input_schema: dict  # 完整的输入 schema
    created_at: datetime
    updated_at: datetime
```

#### 3.2 索引更新时机

- MCP 服务连接成功时：获取工具列表并建立索引
- MCP 服务断开时：移除该服务的工具索引
- 配置热更新时：重新构建索引

### 4. 搜索实现

#### 4.1 搜索策略

1. **名称匹配**：工具名称包含关键词（不区分大小写）
2. **描述匹配**：工具描述包含关键词
3. **参数匹配**：参数名称或描述包含关键词
4. **服务匹配**：服务名称或描述包含关键词

#### 4.2 搜索排序

- 名称完全匹配 > 名称前缀匹配 > 描述匹配 > 参数匹配
- 按相关性排序返回结果

### 5. 执行实现

#### 5.1 工具名称解析

- 支持显示名称（带前缀）：`fs_read_file`
- 支持原始名称：`read_file`
- 如果存在多个同名工具，优先匹配显示名称

#### 5.2 参数验证

- 验证必需参数是否存在
- 验证参数类型是否正确
- 返回清晰的错误信息

#### 5.3 执行流程

1. 根据工具名称查找索引
2. 验证参数
3. 调用对应的 MCP 服务
4. 返回执行结果

## 实现计划

### 阶段 1：工具索引系统

1. 创建 `ToolIndex` 数据模型
2. 创建 `ToolIndexManager` 管理工具索引
3. 在 MCP 服务连接时自动构建索引
4. 在 MCP 服务断开时清理索引

### 阶段 2：搜索功能

1. 实现 `mcp_search_tools` 工具
2. 实现搜索算法（名称、描述、参数匹配）
3. 实现结果排序和分页

### 阶段 3：执行功能

1. 实现 `mcp_execute_tool` 工具
2. 实现工具名称解析
3. 实现参数验证
4. 实现错误处理

### 阶段 4：集成和优化

1. 修改 `McpServer` 只暴露核心工具
2. 保持向后兼容（可选：通过配置开关）
3. 性能优化和测试

## 配置选项

在 `config.yaml` 中添加：

```yaml
global:
  # ... 其他配置
  tool_proxy_mode: true  # 启用工具代理模式（默认 false，保持向后兼容）
  tool_proxy:
    enable_search: true
    enable_execute: true
    enable_list_services: true
    search_limit: 20
```

## 向后兼容

- 默认保持原有行为（直接暴露所有工具）
- 通过配置 `tool_proxy_mode: true` 启用新模式
- 可以逐步迁移，不影响现有用户

## 性能优化

1. **索引缓存**：工具索引缓存在内存中，避免重复查询
2. **延迟加载**：只在需要时连接 MCP 服务
3. **搜索结果缓存**：常用搜索关键词结果缓存（可选）

## 测试计划

1. 单元测试：工具索引、搜索、执行功能
2. 集成测试：与真实 MCP 服务集成
3. 性能测试：大量工具场景下的性能表现
4. 兼容性测试：确保向后兼容

## 文档更新

1. 更新 README，说明新功能
2. 添加使用示例
3. 更新配置文档

