# MyMCP

轻量级 MCP (Model Context Protocol) 自定义命令服务，支持服务聚合和热更新。

## 特性

- ✅ **自定义命令**: 支持 HTTP 接口调用和脚本执行
- ✅ **MCP 服务聚合**: 作为顶层 MCP 服务，可以集成多个其他 MCP 服务
- ✅ **热更新**: 添加/移除 MCP 服务时无需重启，配置变更立即生效
- ✅ **灵活鉴权**: 支持多种鉴权方式（API Key、Bearer Token、Basic Auth、OAuth2 等）
- ✅ **管理界面**: 提供 Web 管理界面，方便配置管理
- ✅ **轻量级**: 无数据库依赖，基于单文件配置
- ✅ **uvx 支持**: 可通过 `uvx` 直接运行，无需预先安装
- ✅ **工具代理模式** (NEW): 优化性能，减少暴露的工具数量，支持搜索和执行

## 快速开始

### 安装 uv（如果还没有）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 运行

#### 方式 1: 从 PyPI 或本地安装运行

```bash
# 使用 uvx 直接运行（无需安装，推荐）
uvx mymcp --config config.yaml

# 启动管理端（默认端口 18888，避免冲突）
uvx mymcp --config config.yaml --admin

# 启动管理端并自动打开浏览器
uvx mymcp --config config.yaml --admin --open-admin

# 使用环境变量控制自动打开浏览器
MYMCP_OPEN_ADMIN=1 uvx mymcp --config config.yaml --admin

# 自定义管理端端口
uvx mymcp --config config.yaml --admin --admin-port 19999
```

#### 方式 2: 从 Git 仓库直接运行（类似 serena）

```bash
# 从 GitHub 仓库直接运行（自动查找配置文件）
uvx --from git+https://github.com/your-username/mymcp start-mcp-server

# 指定配置文件路径
uvx --from git+https://github.com/your-username/mymcp start-mcp-server --config /path/to/config.yaml
```

在 Cursor 或 Claude Desktop 的 MCP 配置中：

```json
{
  "mcpServers": {
    "mymcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-username/mymcp",
        "start-mcp-server",
        "--config",
        "/absolute/path/to/your/config.yaml"
      ]
    }
  }
}
```

或者使用自动查找配置文件（会在当前目录和 `~/.config/mymcp/` 查找）：

```json
{
  "mcpServers": {
    "mymcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/your-username/mymcp",
        "start-mcp-server"
      ]
    }
  }
}
```

### 开发模式

```bash
# 安装依赖
uv pip install -e .

# 运行测试
python test_basic.py

# 直接运行
python -m src --config config.yaml --admin
```

## 配置文件示例

创建 `config.yaml`:

```yaml
# MCP 服务器配置
server:
  host: "0.0.0.0"
  port: 8000
  admin_port: 8080

# 命令配置
commands:
  - name: "get_weather"
    description: "获取天气信息"
    type: "http"
    enabled: true
    http:
      method: "GET"
      url: "https://api.weather.com/v1/current"
      params:
        city: "{city}"
    parameters:
      - name: "city"
        type: "string"
        required: true
        description: "城市名称"

# MCP 服务聚合配置
mcp_servers:
  - name: "filesystem"
    description: "文件系统操作服务"
    enabled: true
    connection:
      type: "stdio"
      command: "uvx"
      args:
        - "mcp-server-filesystem"
        - "/path/to/allowed/dir"
    prefix: "fs"

# 鉴权配置
auth_configs:
  - name: "weather_api_auth"
    type: "api_key"
    api_key:
      location: "query"
      name: "api_key"
      value: "${WEATHER_API_KEY}"

# 全局配置
global:
  default_timeout: 30
  max_retries: 3
  retry_delay: 1
  log_level: "INFO"
  hot_reload: true
```

## 集成示例

### IntelliJ-RunControl 集成

我们已完美支持集成 IntelliJ-RunControl（IntelliJ IDEA 运行控制插件）：

```bash
# 1. 复制配置文件
cp config.intellij-example.yaml config.yaml

# 2. 设置 Token 环境变量
export INTELLIJ_RUNCONTROL_TOKEN="your_token"

# 3. 启动服务
uvx mymcp --config config.yaml
```

详细集成指南: [docs/integration/QUICK_START_INTELLIJ.md](docs/integration/QUICK_START_INTELLIJ.md)

## 文档

### 核心文档
- [设计文档](docs/design.md) - 完整的系统设计
- [uvx 部署指南](docs/uvx-deployment.md) - uvx 使用说明

### 集成指南
- [IntelliJ-RunControl 快速开始](docs/integration/QUICK_START_INTELLIJ.md) - 5分钟快速集成
- [IntelliJ-RunControl 集成文档](docs/integration/intellij-integration.md) - 详细集成说明
- [IntelliJ-RunControl 测试指南](docs/integration/TEST_INTELLIJ.md) - 测试步骤

### 使用指南
- [Cursor 测试指南](docs/guides/CURSOR_TEST_GUIDE.md) - Cursor MCP 配置

### 开发文档
- [实现说明](docs/development/IMPLEMENTATION.md) - 实现细节
- [优化总结](docs/development/OPTIMIZATION.md) - 优化记录
- [项目总结](docs/development/SUMMARY.md) - 项目总结

完整文档索引: [docs/README.md](docs/README.md)

## 开发

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
pytest

# 运行服务
python -m src --config config.yaml
```

## License

MIT

