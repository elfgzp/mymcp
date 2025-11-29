# IntelliJ-RunControl 集成指南

## 概述

IntelliJ-RunControl 是一个 IntelliJ IDEA 插件，提供 HTTP API 来控制运行配置。我们的 MCP 服务可以通过 HTTP 命令功能完美集成它。

**参考**: [IntelliJ-RunControl GitHub](https://github.com/SagenKoder/IntelliJ-RunControl)

## 前置条件

1. **安装 IntelliJ-RunControl 插件**
   - 下载 `IntelliJ-RunControl-1.0.3.zip`
   - Settings → Plugins → ⚙️ → Install Plugin from Disk
   - 重启 IntelliJ IDEA

2. **获取 API Token**
   - Settings → Tools → RunControl
   - 复制 API Token

3. **设置环境变量**
   ```bash
   export INTELLIJ_RUNCONTROL_TOKEN="your_token_here"
   ```

## 配置步骤

### 1. 创建配置文件

复制示例配置文件：
```bash
cp config.intellij-example.yaml config.yaml
```

### 2. 设置 Token

编辑 `config.yaml`，确保 Token 正确配置（通过环境变量）：
```yaml
auth_configs:
  - name: "intellij_auth"
    type: "custom_header"
    custom_header:
      headers:
        X-IntelliJ-Token: "${INTELLIJ_RUNCONTROL_TOKEN}"
```

### 3. 启动服务

```bash
# 使用 uvx 运行
uvx mymcp --config config.yaml

# 或启动管理端
uvx mymcp --config config.yaml --admin
```

## 可用命令

配置完成后，以下命令将可用：

### 项目管理
- `intellij_list_projects` - 列出所有打开的项目

### 运行配置管理
- `intellij_list_run_configs` - 列出所有运行配置
- `intellij_get_run_config` - 获取运行配置详情
- `intellij_run_config` - 启动运行配置
- `intellij_debug_config` - 调试模式启动
- `intellij_stop_config` - 停止运行配置
- `intellij_restart_config` - 重启运行配置

### 日志管理
- `intellij_list_logs` - 列出可用日志源
- `intellij_get_logs` - 读取日志（分页）
- `intellij_tail_logs` - 获取日志尾部
- `intellij_search_logs` - 搜索日志

## 使用示例

### 通过 MCP 客户端调用

```python
# 列出所有项目
result = mcp_client.call_tool(
    "intellij_list_projects",
    arguments={}
)

# 列出运行配置
result = mcp_client.call_tool(
    "intellij_list_run_configs",
    arguments={}
)

# 启动运行配置
result = mcp_client.call_tool(
    "intellij_run_config",
    arguments={
        "name": "MySpringApp"
    }
)

# 获取日志
result = mcp_client.call_tool(
    "intellij_tail_logs",
    arguments={
        "name": "MySpringApp",
        "source": "console",
        "lines": 50
    }
)

# 搜索错误日志
result = mcp_client.call_tool(
    "intellij_search_logs",
    arguments={
        "name": "MySpringApp",
        "source": "server.log",
        "query": "ERROR",
        "maxResults": 10
    }
)
```

### 多项目支持

```python
# 指定项目
result = mcp_client.call_tool(
    "intellij_run_config",
    arguments={
        "name": "Backend",
        "project": "my-backend"
    }
)
```

## 配置 Cursor MCP

### 1. 编辑 Cursor MCP 配置

在 Cursor 的 MCP 配置文件中添加：

**macOS**: `~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json`

**Windows**: `%APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json`

### 2. 添加配置

```json
{
  "mcpServers": {
    "mymcp": {
      "command": "uvx",
      "args": [
        "mymcp",
        "--config",
        "/path/to/your/config.yaml"
      ],
      "env": {
        "INTELLIJ_RUNCONTROL_TOKEN": "your_token_here"
      }
    }
  }
}
```

### 3. 重启 Cursor

重启 Cursor 后，IntelliJ-RunControl 的命令将可用。

## 测试

### 1. 测试连接

```bash
# 测试列出项目
curl -H "X-IntelliJ-Token: $INTELLIJ_RUNCONTROL_TOKEN" \
  http://127.0.0.1:17777/projects
```

### 2. 测试 MCP 服务

在 Cursor 中，可以尝试：
- "列出 IntelliJ 项目"
- "启动我的 Spring Boot 应用"
- "查看应用日志"

## 故障排除

### 1. 401 Unauthorized

- 检查 Token 是否正确设置
- 验证环境变量 `INTELLIJ_RUNCONTROL_TOKEN` 是否正确

### 2. 连接失败

- 确认 IntelliJ-RunControl 插件已启用
- 检查插件设置中的端口（默认 17777）
- 确认插件 HTTP API 已启用

### 3. 命令不可用

- 检查配置文件是否正确加载
- 查看日志文件确认错误信息
- 验证命令是否已启用（`enabled: true`）

## 高级配置

### 自定义端口

如果 IntelliJ-RunControl 使用非默认端口，修改配置中的 URL：

```yaml
http:
  url: "http://127.0.0.1:YOUR_PORT/projects"
```

### 组合使用

可以将 IntelliJ-RunControl 命令与其他 MCP 服务组合使用：

```yaml
mcp_servers:
  - name: "filesystem"
    # ... 其他 MCP 服务配置
```

这样可以在一个统一的 MCP 服务中使用所有功能。

## 参考

- [IntelliJ-RunControl GitHub](https://github.com/SagenKoder/IntelliJ-RunControl)
- [MCP 协议文档](https://modelcontextprotocol.io/)

