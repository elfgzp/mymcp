# IntelliJ-RunControl 快速集成指南

## 5 分钟快速开始

### 步骤 1: 安装 IntelliJ-RunControl 插件

1. 下载插件: [IntelliJ-RunControl-1.0.3.zip](https://github.com/SagenKoder/IntelliJ-RunControl/releases)
2. IntelliJ IDEA: **Settings → Plugins → ⚙️ → Install Plugin from Disk**
3. 选择下载的 zip 文件
4. 重启 IntelliJ IDEA

### 步骤 2: 获取 API Token

1. IntelliJ IDEA: **Settings → Tools → RunControl**
2. 复制显示的 **API Token**
3. 设置环境变量：
   ```bash
   export INTELLIJ_RUNCONTROL_TOKEN="your_copied_token"
   ```

### 步骤 3: 配置 MyMCP

1. 复制配置文件：
   ```bash
   cp config.intellij-example.yaml config.yaml
   ```

2. 配置文件已包含所有 IntelliJ-RunControl 命令，无需修改

### 步骤 4: 配置 Cursor MCP

1. 找到 Cursor MCP 配置文件：

   **macOS**:
   ```
   ~/Library/Application Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
   ```

   **Windows**:
   ```
   %APPDATA%\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json
   ```

2. 编辑配置文件，添加：

   ```json
   {
     "mcpServers": {
       "mymcp": {
         "command": "uvx",
         "args": [
           "mymcp",
           "--config",
           "/absolute/path/to/your/config.yaml"
         ],
         "env": {
           "INTELLIJ_RUNCONTROL_TOKEN": "your_token_here"
         }
       }
     }
   }
   ```

   **注意**: 
   - 将 `/absolute/path/to/your/config.yaml` 替换为实际路径
   - 将 `your_token_here` 替换为实际的 Token

3. 保存文件并重启 Cursor

### 步骤 5: 测试

在 Cursor 中尝试：

1. "列出 IntelliJ 项目" → 使用 `intellij_list_projects`
2. "列出运行配置" → 使用 `intellij_list_run_configs`
3. "启动我的应用" → 使用 `intellij_run_config`

## 可用命令列表

| 命令 | 功能 |
|------|------|
| `intellij_list_projects` | 列出所有项目 |
| `intellij_list_run_configs` | 列出运行配置 |
| `intellij_get_run_config` | 获取配置详情 |
| `intellij_run_config` | 启动配置 |
| `intellij_debug_config` | 调试模式启动 |
| `intellij_stop_config` | 停止配置 |
| `intellij_restart_config` | 重启配置 |
| `intellij_list_logs` | 列出日志源 |
| `intellij_get_logs` | 读取日志 |
| `intellij_tail_logs` | 获取日志尾部 |
| `intellij_search_logs` | 搜索日志 |

## 使用示例

### 在 Cursor 中

你可以直接说：
- "列出我的 IntelliJ 项目"
- "启动 Spring Boot 应用"
- "查看应用的控制台日志"
- "搜索日志中的错误"

### 命令行测试

```bash
# 测试服务是否运行
uvx mymcp --config config.yaml --admin

# 访问管理界面
# http://localhost:18888
```

## 故障排除

### Token 错误
- 检查环境变量是否正确设置
- 验证 Token 是否与 IntelliJ 插件中的一致

### 连接失败
- 确认 IntelliJ-RunControl 插件已启用
- 检查插件设置中的端口（默认 17777）
- 确认 HTTP API 已启用

### 命令不可用
- 检查配置文件路径是否正确
- 查看日志确认错误
- 验证命令是否启用

## 更多信息

详细文档请查看: [docs/intellij-integration.md](docs/intellij-integration.md)

