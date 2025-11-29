# MCP 自定义命令服务设计文档

## 1. 项目概述

### 1.1 项目目标
构建一个轻量级的 MCP (Model Context Protocol) 服务器，支持：
- 自定义命令与接口/脚本的绑定
- 灵活的鉴权机制
- 基于配置文件的管理端
- 无需数据库的轻量级部署

### 1.2 核心特性
- ✅ 命令自定义：用户可定义命令名称和对应的执行逻辑
- ✅ 接口调用：支持 HTTP/HTTPS API 调用
- ✅ 脚本执行：支持执行本地脚本（Python、Shell 等）
- ✅ 鉴权支持：支持多种鉴权方式（API Key、Bearer Token、Basic Auth、OAuth2 等）
- ✅ **MCP 服务聚合：作为顶层 MCP 服务，集成其他 MCP 服务**
- ✅ **热更新：添加/移除 MCP 服务时无需重启**
- ✅ 管理端：提供 Web 管理界面
- ✅ 配置持久化：基于 YAML/JSON 配置文件
- ✅ 轻量级：无数据库依赖，单文件配置
- ✅ **uvx 支持：可通过 `uvx` 直接运行，无需安装**

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (顶层聚合服务)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Command      │  │ Auth         │  │ Executor     │      │
│  │ Manager      │  │ Manager      │  │ (HTTP/Script)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                  │               │
│         └─────────────────┴──────────────────┘               │
│                         │                                     │
│  ┌──────────────────────▼──────────────────────┐             │
│  │         MCP Client Manager                 │             │
│  │  ┌────────────┐  ┌────────────┐  ┌──────┐ │             │
│  │  │ MCP Client │  │ MCP Client │  │ ...  │ │             │
│  │  │ (Service1) │  │ (Service2) │  │      │ │             │
│  │  └────────────┘  └────────────┘  └──────┘ │             │
│  └──────────────────────┬──────────────────────┘             │
│                         │                                     │
│                  ┌──────▼───────┐                            │
│                  │ Config       │                            │
│                  │ Manager      │                            │
│                  │ (Hot Reload) │                            │
│                  └──────┬───────┘                            │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                  ┌───────▼────────┐
                  │  config.yaml   │
                  └────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────────┐
│                  Web Admin UI                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Command      │  │ MCP Service │  │ Auth Config  │        │
│  │ Management   │  │ Management  │  │ Management   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │     其他 MCP 服务                    │
        │  ┌──────────┐  ┌──────────┐         │
        │  │ Service1 │  │ Service2 │  ...    │
        │  └──────────┘  └──────────┘         │
        └─────────────────────────────────────┘
```

### 2.2 组件说明

#### 2.2.1 MCP Server
- **Command Manager**: 管理命令定义和路由（包括本地命令和聚合的 MCP 服务命令）
- **Auth Manager**: 处理各种鉴权方式
- **Executor**: 执行 HTTP 请求或脚本
- **MCP Client Manager**: 管理多个 MCP 服务客户端连接，支持热更新
- **Config Manager**: 读写配置文件，支持热重载

#### 2.2.2 Web Admin UI
- **Command Management**: 命令的增删改查
- **MCP Service Management**: MCP 服务的添加、移除、启用/禁用（支持热更新）
- **Endpoint Management**: 接口端点管理
- **Auth Config Management**: 鉴权配置管理

## 3. 数据模型

### 3.1 配置文件结构 (config.yaml)

```yaml
# MCP 服务器配置
server:
  host: "0.0.0.0"
  port: 8000
  admin_port: 8080  # 管理端端口

# 命令配置
commands:
  - name: "get_weather"              # 命令名称
    description: "获取天气信息"      # 命令描述
    type: "http"                     # 类型: http 或 script
    enabled: true                    # 是否启用
    
    # HTTP 类型配置
    http:
      method: "GET"                  # HTTP 方法
      url: "https://api.weather.com/v1/current"
      headers:                       # 自定义请求头
        User-Agent: "MCP-Client/1.0"
      params:                        # URL 参数（支持变量）
        city: "{city}"
        api_key: "{api_key}"
      auth:                          # 鉴权配置引用
        ref: "weather_api_auth"
      timeout: 30                    # 超时时间（秒）
      response_format: "json"         # 响应格式: json, xml, text
      
    # Script 类型配置
    # script:
    #   interpreter: "python3"        # 解释器: python3, bash, node, etc.
    #   path: "/path/to/script.py"    # 脚本路径
    #   args:                         # 脚本参数
    #     - "{arg1}"
    #     - "{arg2}"
    #   env:                          # 环境变量
    #     API_KEY: "{api_key}"
    
    # 输入参数定义
    parameters:
      - name: "city"
        type: "string"
        required: true
        description: "城市名称"
      - name: "api_key"
        type: "string"
        required: false
        description: "API 密钥（可选）"

# 鉴权配置
auth_configs:
  - name: "weather_api_auth"         # 鉴权配置名称
    type: "api_key"                  # 鉴权类型
    # 类型: api_key, bearer_token, basic_auth, oauth2, custom_header
    
    # API Key 类型
    api_key:
      location: "query"              # 位置: header, query, body
      name: "api_key"                # 参数名
      value: "${WEATHER_API_KEY}"    # 支持环境变量
    
    # Bearer Token 类型
    # bearer_token:
    #   token: "${TOKEN}"
    
    # Basic Auth 类型
    # basic_auth:
    #   username: "${USERNAME}"
    #   password: "${PASSWORD}"
    
    # OAuth2 类型
    # oauth2:
    #   client_id: "${CLIENT_ID}"
    #   client_secret: "${CLIENT_SECRET}"
    #   token_url: "https://oauth.example.com/token"
    #   scope: "read write"
    
    # Custom Header 类型
    # custom_header:
    #   headers:
    #     X-API-Key: "${API_KEY}"
    #     X-Client-ID: "${CLIENT_ID}"

# MCP 服务聚合配置（作为顶层服务集成其他 MCP 服务）
mcp_servers:
  - name: "filesystem"               # MCP 服务名称（用于命令前缀，可选）
    description: "文件系统操作服务"   # 服务描述
    enabled: true                    # 是否启用
    connection:
      type: "stdio"                   # 连接类型: stdio, sse, websocket
      # stdio 类型配置
      command: "uvx"                  # 启动命令
      args:                           # 命令参数
        - "mcp-server-filesystem"
        - "/path/to/allowed/dir"
      # 或使用 sse 类型
      # type: "sse"
      # url: "https://mcp-server.example.com/sse"
      # 或使用 websocket 类型
      # type: "websocket"
      # url: "ws://mcp-server.example.com/ws"
    prefix: "fs"                     # 命令前缀（可选，用于避免命名冲突）
    # 如果设置 prefix，工具名会变为 "fs_list_files" 而不是 "list_files"
    timeout: 30                      # 连接超时时间
    retry_on_failure: true           # 失败时是否重试
    auto_reconnect: true             # 是否自动重连
    
  - name: "github"
    description: "GitHub API 服务"
    enabled: true
    connection:
      type: "stdio"
      command: "uvx"
      args:
        - "github:modelcontextprotocol/servers"
        - "github-mcp"
    prefix: "gh"                     # 使用前缀避免冲突
    timeout: 30

# 全局配置
global:
  default_timeout: 30                # 默认超时时间
  max_retries: 3                     # 最大重试次数
  retry_delay: 1                     # 重试延迟（秒）
  log_level: "INFO"                  # 日志级别
  log_file: "mcp.log"                # 日志文件路径
  hot_reload: true                   # 是否启用热重载（配置文件变更时自动重载）
  hot_reload_interval: 2             # 热重载检查间隔（秒）
```

### 3.2 命令执行流程

```
用户请求命令
    │
    ▼
Command Manager 查找命令
    │
    ├─ 本地命令（commands 中定义）
    │   │
    │   ▼
    │   验证参数（必需参数、类型检查）
    │   │
    │   ▼
    │   根据命令类型执行：
    │   ├─ HTTP 类型
    │   │   ├─ 应用鉴权配置
    │   │   ├─ 替换变量（参数、环境变量）
    │   │   ├─ 发送 HTTP 请求
    │   │   └─ 返回响应
    │   │
    │   └─ Script 类型
    │       ├─ 替换变量（参数、环境变量）
    │       ├─ 执行脚本
    │       └─ 返回输出
    │
    └─ MCP 服务命令（从聚合的 MCP 服务获取）
        │
        ▼
        MCP Client Manager 路由到对应的 MCP 服务
        │
        ▼
        检查服务连接状态（如断开则自动重连）
        │
        ▼
        转发请求到对应的 MCP 服务
        │
        ▼
        返回响应（透传或转换格式）
```

### 3.3 MCP 服务聚合流程

```
配置文件变更（添加/移除/修改 MCP 服务）
    │
    ▼
Config Manager 检测变更（热重载）
    │
    ▼
MCP Client Manager 处理变更：
    ├─ 新增服务
    │   ├─ 建立连接
    │   ├─ 获取工具列表
    │   ├─ 注册到 Command Manager
    │   └─ 更新工具列表（无需重启）
    │
    ├─ 移除服务
    │   ├─ 断开连接
    │   ├─ 从 Command Manager 注销工具
    │   └─ 更新工具列表
    │
    └─ 修改服务
        ├─ 断开旧连接
        ├─ 建立新连接
        └─ 更新工具列表
```

## 4. API 设计

### 4.1 MCP Protocol 接口

#### 4.1.1 列出可用工具
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

响应：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "获取天气信息",
        "inputSchema": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "城市名称"
            }
          },
          "required": ["city"]
        }
      }
    ]
  }
}
```

#### 4.1.2 调用工具
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "city": "北京"
    }
  },
  "id": 2
}
```

响应：
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"temperature\": 25, \"condition\": \"晴天\"}"
      }
    ]
  }
}
```

### 4.2 管理端 API

#### 4.2.1 命令管理

**获取所有命令**
```
GET /api/commands
```

**获取单个命令**
```
GET /api/commands/{name}
```

**创建命令**
```
POST /api/commands
Content-Type: application/json

{
  "name": "new_command",
  "description": "新命令",
  "type": "http",
  "http": { ... },
  "parameters": [ ... ]
}
```

**更新命令**
```
PUT /api/commands/{name}
```

**删除命令**
```
DELETE /api/commands/{name}
```

**启用/禁用命令**
```
PATCH /api/commands/{name}/toggle
```

#### 4.2.2 鉴权配置管理

**获取所有鉴权配置**
```
GET /api/auth-configs
```

**创建鉴权配置**
```
POST /api/auth-configs
```

**更新鉴权配置**
```
PUT /api/auth-configs/{name}
```

**删除鉴权配置**
```
DELETE /api/auth-configs/{name}
```

#### 4.2.3 MCP 服务管理

**获取所有 MCP 服务**
```
GET /api/mcp-servers
```

响应：
```json
{
  "servers": [
    {
      "name": "filesystem",
      "description": "文件系统操作服务",
      "enabled": true,
      "status": "connected",
      "tools_count": 5,
      "connection": {
        "type": "stdio",
        "command": "uvx",
        "args": ["mcp-server-filesystem"]
      }
    }
  ]
}
```

**获取单个 MCP 服务**
```
GET /api/mcp-servers/{name}
```

**添加 MCP 服务（热更新）**
```
POST /api/mcp-servers
Content-Type: application/json

{
  "name": "new_mcp_service",
  "description": "新的 MCP 服务",
  "enabled": true,
  "connection": {
    "type": "stdio",
    "command": "uvx",
    "args": ["mcp-server-name"]
  },
  "prefix": "new",
  "timeout": 30
}
```

响应：立即生效，无需重启

**更新 MCP 服务（热更新）**
```
PUT /api/mcp-servers/{name}
```

**删除 MCP 服务（热更新）**
```
DELETE /api/mcp-servers/{name}
```

**启用/禁用 MCP 服务（热更新）**
```
PATCH /api/mcp-servers/{name}/toggle
```

**测试 MCP 服务连接**
```
POST /api/mcp-servers/{name}/test
```

**获取 MCP 服务的工具列表**
```
GET /api/mcp-servers/{name}/tools
```

**重连 MCP 服务**
```
POST /api/mcp-servers/{name}/reconnect
```

#### 4.2.4 配置管理

**获取完整配置**
```
GET /api/config
```

**保存配置**
```
POST /api/config
```

**重载配置（热更新）**
```
POST /api/config/reload
```

**获取配置变更历史（可选）**
```
GET /api/config/history
```

## 5. 管理端设计

### 5.1 功能模块

#### 5.1.1 命令管理页面
- 命令列表（表格展示）
- 命令详情（编辑表单）
- 命令测试（测试执行）
- 启用/禁用切换

#### 5.1.2 鉴权配置页面
- 鉴权配置列表
- 鉴权配置编辑（支持多种类型）
- 环境变量管理提示

#### 5.1.3 MCP 服务管理页面
- MCP 服务列表（显示连接状态、工具数量）
- 添加 MCP 服务（支持 stdio、sse、websocket）
- 编辑 MCP 服务配置
- 启用/禁用 MCP 服务（热更新）
- 测试连接
- 查看服务提供的工具列表
- 重连服务

#### 5.1.4 配置概览
- 配置文件内容预览
- 配置验证
- 配置导出/导入
- 热重载状态

### 5.2 技术选型

**前端框架**: 
- 轻量级选择：原生 HTML + JavaScript + Tailwind CSS
- 或：Vue 3 + Vite（更现代但稍重）

**后端框架**:
- FastAPI（Python，与 MCP Server 集成方便）
- 或：Flask（更轻量）

## 6. 技术栈

### 6.1 核心依赖
- **Python 3.9+**
- **mcp**: MCP Protocol 实现（官方 SDK，支持 Server 和 Client）
- **httpx**: HTTP 客户端（支持异步，轻量级）
- **pyyaml**: YAML 配置文件解析
- **pydantic**: 数据验证和配置管理
- **watchdog**: 文件系统监控（用于热重载）
- **fastapi**: Web 框架（管理端，可选，仅管理端需要）
- **uvicorn**: ASGI 服务器（可选，仅管理端需要）

### 6.2 可选依赖
- **jinja2**: 模板引擎（管理端 UI，可选）
- **aiofiles**: 异步文件操作（可选）

### 6.3 包管理
- **uv**: 使用 `uv` 作为包管理工具
- **pyproject.toml**: 项目配置和依赖声明
- **uvx 支持**: 通过 `uvx` 直接运行，无需预先安装

## 7. 项目结构

```
mymcp/
├── README.md
├── LICENSE
├── pyproject.toml                 # uv 项目配置（包含 scripts 入口）
├── config.yaml                    # 配置文件（示例）
├── .env.example                   # 环境变量示例
├── src/
│   ├── __init__.py
│   ├── __main__.py                # 主入口（支持 python -m）
│   ├── mcp_server.py             # MCP 服务器主程序
│   ├── config/
│   │   ├── __init__.py
│   │   ├── manager.py            # 配置管理器（支持热重载）
│   │   ├── models.py             # 配置数据模型
│   │   └── watcher.py            # 配置文件监控
│   ├── command/
│   │   ├── __init__.py
│   │   ├── manager.py            # 命令管理器（统一管理本地和 MCP 命令）
│   │   └── executor.py            # 命令执行器
│   ├── mcp_client/
│   │   ├── __init__.py
│   │   ├── manager.py            # MCP 客户端管理器（管理多个 MCP 服务连接）
│   │   ├── client.py             # MCP 客户端实现
│   │   └── connection.py         # 连接管理（stdio/sse/websocket）
│   ├── auth/
│   │   ├── __init__.py
│   │   └── manager.py            # 鉴权管理器
│   └── admin/
│       ├── __init__.py
│       ├── server.py             # 管理端服务器
│       ├── routes.py              # API 路由
│       └── templates/             # HTML 模板
│           └── index.html
├── scripts/                       # 示例脚本
│   └── example.py
├── tests/                         # 测试文件
│   ├── __init__.py
│   ├── test_command.py
│   ├── test_auth.py
│   └── test_config.py
└── docs/
    ├── design.md                  # 本文档
    ├── api.md                     # API 文档
    └── usage.md                   # 使用文档
```

### 7.1 uvx 运行支持

项目通过 `pyproject.toml` 配置，支持以下运行方式：

```toml
[project.scripts]
mymcp = "src.__main__:main"
```

运行方式：
```bash
# 方式 1: 使用 uvx 直接运行（推荐）
uvx mymcp --config config.yaml

# 方式 2: 安装后运行
uv pip install -e .
mymcp --config config.yaml

# 方式 3: 作为模块运行
python -m src --config config.yaml
```

## 8. 安全考虑

### 8.1 配置文件安全
- 敏感信息（API Key、Token）使用环境变量
- 配置文件权限控制（建议 600）
- 支持配置文件加密（可选）

### 8.2 脚本执行安全
- 脚本路径白名单
- 脚本执行权限限制
- 沙箱执行环境（可选）

### 8.3 管理端安全
- 管理端访问控制（IP 白名单或认证）
- HTTPS 支持（生产环境）
- CORS 配置

## 9. 实现计划

### 9.1 Phase 1: 核心功能
- [ ] 配置管理器（读取/写入 YAML）
- [ ] 命令管理器（命令注册和路由）
- [ ] HTTP 执行器
- [ ] 基础鉴权（API Key、Bearer Token）

### 9.2 Phase 2: MCP 协议
- [ ] MCP 服务器实现
- [ ] 工具列表接口
- [ ] 工具调用接口
- [ ] 错误处理

### 9.3 Phase 3: MCP 服务聚合（核心功能）
- [ ] MCP 客户端实现（支持 stdio）
- [ ] MCP 客户端管理器（管理多个连接）
- [ ] 工具聚合（将 MCP 服务工具注册到本地）
- [ ] 命令路由（区分本地命令和 MCP 服务命令）
- [ ] 连接管理（自动重连、健康检查）

### 9.4 Phase 4: 热更新机制
- [ ] 配置文件监控（watchdog）
- [ ] 配置热重载
- [ ] MCP 服务热添加/移除
- [ ] 工具列表动态更新
- [ ] 连接状态管理

### 9.5 Phase 5: 脚本执行
- [ ] 脚本执行器
- [ ] 多解释器支持
- [ ] 参数传递
- [ ] 输出解析

### 9.6 Phase 6: 管理端
- [ ] 管理端 API
- [ ] Web UI（命令管理）
- [ ] Web UI（MCP 服务管理）
- [ ] Web UI（鉴权配置）
- [ ] 实时状态更新（WebSocket 或 SSE）

### 9.7 Phase 7: 高级功能
- [ ] 更多连接类型（sse、websocket）
- [ ] 更多鉴权方式（OAuth2、Basic Auth）
- [ ] 请求重试机制
- [ ] 响应缓存（可选）
- [ ] 日志和监控
- [ ] 性能优化（连接池、请求合并）

## 10. 使用示例

### 10.1 快速开始

#### 安装和运行

```bash
# 使用 uvx 直接运行（无需安装）
uvx mymcp --config config.yaml

# 或者指定 GitHub 仓库
uvx github:your-username/mymcp --config config.yaml
```

#### 配置文件示例

```yaml
commands:
  - name: "search_github"
    description: "搜索 GitHub 仓库"
    type: "http"
    http:
      method: "GET"
      url: "https://api.github.com/search/repositories"
      params:
        q: "{query}"
      auth:
        ref: "github_auth"
    parameters:
      - name: "query"
        type: "string"
        required: true

auth_configs:
  - name: "github_auth"
    type: "bearer_token"
    bearer_token:
      token: "${GITHUB_TOKEN}"
```

### 10.2 命令调用示例

#### 通过 MCP 客户端调用

```python
# 通过 MCP 客户端调用
result = mcp_client.call_tool(
    "search_github",
    arguments={"query": "python mcp"}
)
```

#### 通过命令行测试

```bash
# 启动 MCP 服务器（stdio 模式）
uvx mymcp --config config.yaml

# 在另一个终端，使用 MCP 客户端连接
# 或通过 Cursor/Claude Desktop 等支持 MCP 的客户端连接
```

### 10.3 管理端使用

```bash
# 启动 MCP 服务器和管理端
uvx mymcp --config config.yaml --admin

# 访问管理界面
# http://localhost:8080
```

### 10.4 MCP 服务聚合示例

#### 配置文件示例（聚合多个 MCP 服务）

```yaml
# 本地命令
commands:
  - name: "get_weather"
    description: "获取天气信息"
    type: "http"
    http:
      method: "GET"
      url: "https://api.weather.com/v1/current"
      params:
        city: "{city}"

# 聚合其他 MCP 服务
mcp_servers:
  # 文件系统服务
  - name: "filesystem"
    description: "文件系统操作"
    enabled: true
    connection:
      type: "stdio"
      command: "uvx"
      args:
        - "mcp-server-filesystem"
        - "/path/to/allowed/dir"
    prefix: "fs"  # 工具名会变为 fs_list_files, fs_read_file 等

  # GitHub 服务
  - name: "github"
    description: "GitHub API 操作"
    enabled: true
    connection:
      type: "stdio"
      command: "uvx"
      args:
        - "github:modelcontextprotocol/servers"
        - "github-mcp"
    prefix: "gh"  # 工具名会变为 gh_search_repos, gh_get_issue 等

  # 数据库服务（示例）
  - name: "database"
    description: "数据库操作"
    enabled: false  # 暂时禁用
    connection:
      type: "stdio"
      command: "python"
      args:
        - "-m"
        - "mcp_server_database"
        - "--config"
        - "/path/to/db-config.json"
    prefix: "db"
```

#### 使用聚合后的工具

当配置了上述 MCP 服务后，客户端可以同时使用：

1. **本地命令**: `get_weather`
2. **文件系统服务工具**: `fs_list_files`, `fs_read_file`, `fs_write_file` 等
3. **GitHub 服务工具**: `gh_search_repos`, `gh_get_issue`, `gh_create_pr` 等

所有工具都会在 `tools/list` 接口中统一返回。

#### 热更新示例

```bash
# 1. 启动服务
uvx mymcp --config config.yaml --admin

# 2. 通过管理界面添加新的 MCP 服务
# POST /api/mcp-servers
{
  "name": "slack",
  "description": "Slack 集成",
  "enabled": true,
  "connection": {
    "type": "stdio",
    "command": "uvx",
    "args": ["mcp-server-slack"]
  },
  "prefix": "slack"
}

# 3. 新服务立即生效，无需重启
# 工具列表自动更新，包含新的 slack_* 工具

# 4. 禁用服务
# PATCH /api/mcp-servers/slack/toggle
# 服务立即断开，工具从列表中移除

# 5. 重新启用
# PATCH /api/mcp-servers/slack/toggle
# 服务自动重连，工具重新可用
```

## 11. MCP 服务聚合详细设计

### 11.1 设计目标

1. **统一入口**: 将多个 MCP 服务的工具聚合到一个统一的 MCP 服务器中
2. **透明代理**: 客户端无需知道工具来自哪个 MCP 服务
3. **热更新**: 添加/移除 MCP 服务时无需重启主服务
4. **命名空间**: 通过前缀避免工具名冲突
5. **故障隔离**: 单个 MCP 服务故障不影响其他服务

### 11.2 架构设计

#### 11.2.1 工具聚合流程

```
启动时：
1. 加载配置文件
2. 为每个启用的 MCP 服务建立连接
3. 调用每个服务的 tools/list 获取工具列表
4. 应用前缀（如果配置了）
5. 注册到 Command Manager
6. 合并所有工具（本地 + MCP 服务）
7. 返回统一的工具列表给客户端
```

#### 11.2.2 工具调用路由

```
客户端调用工具 "fs_read_file"
    │
    ▼
Command Manager 查找工具
    │
    ├─ 本地命令？ → 执行本地逻辑
    │
    └─ MCP 服务工具？
        │
        ▼
        解析前缀 "fs" → 找到对应的 MCP 服务
        │
        ▼
        MCP Client Manager 路由到 "filesystem" 服务
        │
        ▼
        转发请求到 filesystem MCP 服务
        │
        ▼
        返回响应（透传）
```

### 11.3 连接管理

#### 11.3.1 连接类型支持

1. **stdio** (默认)
   - 通过子进程启动 MCP 服务
   - 通过标准输入/输出通信
   - 适合本地 MCP 服务

2. **sse** (Server-Sent Events)
   - 通过 HTTP SSE 连接
   - 适合远程 MCP 服务
   - 支持自动重连

3. **websocket**
   - 通过 WebSocket 连接
   - 适合实时双向通信
   - 支持自动重连

#### 11.3.2 连接生命周期

```
建立连接
    │
    ▼
初始化 MCP 协议握手
    │
    ▼
获取工具列表
    │
    ▼
注册工具到 Command Manager
    │
    ▼
保持连接（心跳检测）
    │
    ├─ 正常 → 继续服务
    │
    └─ 断开 → 自动重连（如果启用）
        │
        └─ 重连成功 → 重新注册工具
        │
        └─ 重连失败 → 标记为断开，工具不可用
```

### 11.4 热更新机制

#### 11.4.1 配置文件监控

```python
# 使用 watchdog 监控配置文件
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == config_path:
            # 检测到配置文件变更
            reload_config()
```

#### 11.4.2 热更新流程

```
配置文件变更
    │
    ▼
Config Manager 检测变更
    │
    ▼
解析新配置
    │
    ▼
对比旧配置，识别变更：
    ├─ 新增 MCP 服务
    │   ├─ 建立连接
    │   ├─ 获取工具列表
    │   └─ 注册工具
    │
    ├─ 移除 MCP 服务
    │   ├─ 断开连接
    │   └─ 注销工具
    │
    ├─ 修改 MCP 服务
    │   ├─ 断开旧连接
    │   ├─ 建立新连接
    │   └─ 更新工具列表
    │
    └─ 启用/禁用服务
        ├─ 启用：建立连接并注册工具
        └─ 禁用：断开连接并注销工具
```

#### 11.4.3 工具列表更新

```python
# 工具列表动态更新，无需重启
class CommandManager:
    def update_tools_from_mcp_service(self, service_name, tools):
        # 移除旧工具
        self.unregister_mcp_tools(service_name)
        
        # 注册新工具
        for tool in tools:
            tool_name = self.apply_prefix(service_name, tool.name)
            self.register_tool(tool_name, tool, source="mcp", service=service_name)
        
        # 通知客户端工具列表已更新（如果支持）
        self.notify_tools_updated()
```

### 11.5 错误处理

#### 11.5.1 连接错误

- **连接失败**: 记录错误，标记服务为不可用，工具不注册
- **连接超时**: 重试机制，达到最大重试次数后标记为失败
- **协议错误**: 记录错误日志，断开连接

#### 11.5.2 调用错误

- **服务断开**: 尝试自动重连，如果重连失败，返回错误给客户端
- **工具不存在**: 返回明确的错误信息
- **调用超时**: 返回超时错误，不影响其他工具

#### 11.5.3 故障隔离

- 单个 MCP 服务故障不影响其他服务
- 本地命令不受 MCP 服务故障影响
- 错误信息包含服务名称，便于调试

### 11.6 性能优化

#### 11.6.1 连接池

- 保持 MCP 服务连接，避免频繁建立连接
- 支持连接复用

#### 11.6.2 工具列表缓存

- 缓存每个 MCP 服务的工具列表
- 仅在服务重连或配置变更时更新

#### 11.6.3 异步处理

- MCP 服务调用使用异步 I/O
- 支持并发调用多个 MCP 服务

## 12. 扩展性考虑

### 12.1 插件系统（未来）
- 自定义执行器插件
- 自定义鉴权插件
- 自定义响应处理器

### 12.2 多配置文件支持
- 支持配置文件目录
- 配置文件合并
- 环境特定配置

### 12.3 配置验证
- Schema 验证
- 配置检查工具
- 配置迁移工具

## 13. uvx 运行设计

### 13.1 设计目标
- 支持通过 `uvx` 直接运行，无需预先安装
- 最小化依赖，快速启动
- 单文件可执行，便于分发

### 13.2 实现要点

#### 13.2.1 pyproject.toml 配置
```toml
[project]
name = "mymcp"
version = "0.1.0"
description = "轻量级 MCP 自定义命令服务"
requires-python = ">=3.9"
dependencies = [
    "mcp>=0.1.0",
    "httpx>=0.25.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "fastapi>=0.104.0",  # 仅管理端需要
    "uvicorn>=0.24.0",   # 仅管理端需要
]

[project.scripts]
mymcp = "src.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 13.2.2 主入口设计
- `src/__main__.py`: 提供 `main()` 函数作为入口点
- 支持命令行参数：
  - `--config`: 配置文件路径
  - `--admin`: 启动管理端
  - `--port`: MCP 服务器端口
  - `--admin-port`: 管理端端口

#### 13.2.3 轻量化策略
- **按需加载**: 管理端功能仅在 `--admin` 时加载
- **最小依赖**: 核心功能仅依赖必要库
- **可选依赖**: 管理端相关依赖标记为可选
- **单文件配置**: 所有配置集中在一个 YAML 文件

### 13.3 运行模式

#### 13.3.1 stdio 模式（默认）
```bash
uvx mymcp --config config.yaml
```
- 通过标准输入/输出与 MCP 客户端通信
- 适合集成到 Cursor、Claude Desktop 等

#### 13.3.2 管理端模式
```bash
uvx mymcp --config config.yaml --admin
```
- 启动 MCP 服务器（stdio）
- 同时启动 Web 管理界面（HTTP）

### 13.4 性能优化
- **延迟导入**: 仅在需要时导入管理端相关模块
- **配置缓存**: 配置文件解析结果缓存
- **连接池**: HTTP 客户端使用连接池

## 14. 总结

本设计文档描述了一个轻量级、可扩展的 MCP 自定义命令服务系统。系统具有以下核心特性：

### 14.1 核心功能
1. **自定义命令**: 支持 HTTP 接口调用和脚本执行
2. **MCP 服务聚合**: 作为顶层 MCP 服务，可以集成多个其他 MCP 服务
3. **热更新**: 添加/移除 MCP 服务时无需重启，配置变更立即生效
4. **灵活鉴权**: 支持多种鉴权方式（API Key、Bearer Token、Basic Auth、OAuth2 等）
5. **管理界面**: 提供 Web 管理界面，方便配置管理
6. **轻量级**: 无数据库依赖，基于单文件配置

### 14.2 技术亮点
- **uvx 支持**: 可通过 `uvx` 直接运行，无需预先安装
- **热重载**: 配置文件监控和自动重载
- **故障隔离**: 单个 MCP 服务故障不影响其他服务
- **命名空间**: 通过前缀避免工具名冲突
- **透明代理**: 客户端无需知道工具来自哪个 MCP 服务

### 14.3 使用场景
- 统一管理多个 MCP 服务
- 自定义业务逻辑命令
- 快速集成第三方 API
- 脚本自动化执行
- 作为 MCP 服务的网关/代理

整个系统设计简洁，易于部署和维护，适合作为 MCP 生态系统的统一入口和扩展平台。

