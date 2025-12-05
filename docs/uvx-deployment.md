# uvx 部署和使用指南

## 概述

本项目设计为通过 `uvx` 直接运行，无需预先安装。`uvx` 是 `uv` 工具的一部分，可以临时运行 Python 包，类似于 `npx` 对于 Node.js。

## 前置要求

### 安装 uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# 或使用 homebrew (macOS)
brew install uv
```

### 验证安装

```bash
uv --version
```

## 使用方式

### 方式 1: 从本地项目运行

```bash
# 克隆或下载项目
git clone https://github.com/your-username/mymcp.git
cd mymcp

# 使用 uvx 运行（会自动安装依赖）
uvx mymcp --config config.yaml
```

### 方式 2: 从 GitHub 直接运行

```bash
# 如果项目已发布到 PyPI
uvx mymcp --config config.yaml

# 或从 GitHub 仓库运行（使用 start-mcp-server 入口点）
uvx --from git+https://github.com/your-username/mymcp start-mcp-server --config config.yaml

# 自动查找配置文件（会在当前目录和 ~/.config/mymcp/ 查找）
uvx --from git+https://github.com/your-username/mymcp start-mcp-server
```

### 方式 3: 从本地路径运行

```bash
# 指定本地项目路径
uvx --from ./mymcp mymcp --config config.yaml
```

## 命令行参数

```bash
uvx mymcp [OPTIONS]

选项:
  --config PATH          配置文件路径 (默认: config.yaml)
  --admin                启动管理端 (默认: False)
  --port PORT            MCP 服务器端口 (默认: 通过 stdio)
  --admin-port PORT      管理端端口 (默认: 8080)
  --log-level LEVEL     日志级别 (默认: INFO)
  --log-file PATH        日志文件路径 (可选)
  --help                 显示帮助信息
```

## 使用示例

### 示例 1: 基本运行（stdio 模式）

```bash
# 启动 MCP 服务器，通过标准输入/输出通信
uvx mymcp --config config.yaml
```

这个模式适合：
- 集成到 Cursor、Claude Desktop 等支持 MCP 的客户端
- 通过管道与其他工具交互

### 示例 2: 启动管理端

```bash
# 启动 MCP 服务器和管理端 Web 界面
uvx mymcp --config config.yaml --admin

# 访问管理界面
# http://localhost:8080
```

### 示例 3: 自定义配置和端口

```bash
# 使用自定义配置文件和管理端口
uvx mymcp \
  --config /path/to/my-config.yaml \
  --admin \
  --admin-port 9000
```

## 配置文件

### 配置文件位置

1. **命令行指定**: `--config /path/to/config.yaml`
2. **当前目录**: `./config.yaml`
3. **用户配置目录**: `~/.config/mymcp/config.yaml`
4. **默认**: `./config.yaml`

### 配置文件示例

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
      auth:
        ref: "weather_api_auth"
    parameters:
      - name: "city"
        type: "string"
        required: true
        description: "城市名称"

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
  log_level: "INFO"
```

### 环境变量

敏感信息应使用环境变量：

```bash
# 设置环境变量
export WEATHER_API_KEY="your-api-key-here"

# 运行服务
uvx mymcp --config config.yaml
```

或使用 `.env` 文件：

```bash
# .env 文件
WEATHER_API_KEY=your-api-key-here
GITHUB_TOKEN=your-github-token

# 运行（需要支持 .env 加载，或手动 source）
source .env && uvx mymcp --config config.yaml
```

## 集成到 MCP 客户端

### Cursor 配置

#### 方式 1: 从 PyPI 或本地安装运行

在 Cursor 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "mymcp": {
      "command": "uvx",
      "args": [
        "mymcp",
        "--config",
        "/path/to/config.yaml"
      ]
    }
  }
}
```

#### 方式 2: 从 Git 仓库直接运行（推荐，类似 serena）

从 GitHub 仓库直接运行，无需预先安装：

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
        "/path/to/config.yaml"
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

### Claude Desktop 配置

#### 方式 1: 从 PyPI 或本地安装运行

在 Claude Desktop 的配置文件中添加：

```json
{
  "mcpServers": {
    "mymcp": {
      "command": "uvx",
      "args": [
        "mymcp",
        "--config",
        "/path/to/config.yaml"
      ]
    }
  }
}
```

#### 方式 2: 从 Git 仓库直接运行

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
        "/path/to/config.yaml"
      ]
    }
  }
}
```

## 性能优化

### 缓存依赖

`uvx` 会自动缓存已安装的依赖，但你可以手动管理：

```bash
# 查看缓存
uv cache dir

# 清理缓存（如果需要）
uv cache clean
```

### 预安装依赖

如果需要更快的启动速度，可以预先安装：

```bash
# 进入项目目录
cd mymcp

# 安装依赖
uv pip install -e .

# 直接运行（不再需要 uvx）
mymcp --config config.yaml
```

## 故障排除

### 问题 1: uvx 找不到命令

**解决方案**:
```bash
# 确保在项目根目录
cd mymcp

# 或使用完整路径
uvx --from /path/to/mymcp mymcp --config config.yaml
```

### 问题 2: 依赖安装失败

**解决方案**:
```bash
# 检查 Python 版本（需要 3.9+）
python --version

# 手动安装依赖
cd mymcp
uv pip install -r requirements.txt
```

### 问题 3: 配置文件找不到

**解决方案**:
```bash
# 使用绝对路径
uvx mymcp --config /absolute/path/to/config.yaml

# 或确保配置文件在当前目录
ls config.yaml
```

### 问题 4: 权限问题

**解决方案**:
```bash
# 确保脚本有执行权限
chmod +x src/__main__.py

# 或使用 python -m
uvx python -m src --config config.yaml
```

## 开发模式

### 本地开发

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
pytest

# 运行服务
python -m src --config config.yaml
```

### 调试模式

```bash
# 启用详细日志
uvx mymcp --config config.yaml --log-level DEBUG

# 或使用 Python 调试器
uvx python -m pdb -m src --config config.yaml
```

## 发布到 PyPI（可选）

如果希望其他人可以直接使用 `uvx mymcp`，需要发布到 PyPI：

```bash
# 构建包
uv build

# 发布到 PyPI
uv publish
```

发布后，用户可以直接运行：
```bash
uvx mymcp --config config.yaml
```

## 总结

通过 `uvx` 运行本项目提供了以下优势：

1. **无需安装**: 直接运行，自动管理依赖
2. **版本隔离**: 每次运行使用独立的虚拟环境
3. **快速启动**: 依赖缓存机制加速启动
4. **易于分发**: 支持从 GitHub、PyPI 等多种来源运行
5. **轻量级**: 最小化系统影响

这使得项目非常适合作为 MCP 服务器使用，用户可以快速尝试和集成，无需复杂的安装步骤。

