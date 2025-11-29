# Cursor MCP 测试指南

## ✅ 配置已完成

配置已自动设置完成！

## 📋 配置信息

- **配置文件**: `/Users/gzp/Github/mymcp/config.yaml`
- **Cursor MCP 配置**: `~/.cursor/mcp.json`

## 🚀 测试步骤

### 步骤 1: 设置环境变量（如果使用 IntelliJ-RunControl）

```bash
# 在终端中设置（当前会话有效）
export INTELLIJ_RUNCONTROL_TOKEN="your_token_here"

# 或添加到 ~/.zshrc 使其永久生效
echo 'export INTELLIJ_RUNCONTROL_TOKEN="your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### 步骤 2: 重启 Cursor

**重要**: 必须重启 Cursor 才能使 MCP 配置生效！

1. 完全退出 Cursor（⌘Q）
2. 重新打开 Cursor

### 步骤 3: 验证 MCP 连接

在 Cursor 中：

1. 打开命令面板（⌘⇧P）
2. 搜索 "MCP" 或查看 MCP 状态
3. 确认 `mymcp` 服务已连接

### 步骤 4: 测试命令

在 Cursor 的聊天界面中尝试以下命令：

#### 基础测试
- "列出可用的工具"
- "显示 mymcp 的工具列表"

#### IntelliJ-RunControl 测试（如果已配置）
- "列出我的 IntelliJ 项目"
- "列出所有运行配置"
- "启动我的 Spring Boot 应用"（需要指定配置名称）
- "查看应用的控制台日志"（需要指定配置名称）

#### 其他命令测试
- "获取天气信息"（如果配置了天气 API）
- "执行测试脚本"（如果配置了脚本命令）

## 🔍 验证配置

### 检查配置文件

```bash
# 查看 Cursor MCP 配置
cat ~/.cursor/mcp.json | python3 -m json.tool

# 查看 MyMCP 配置
cat /Users/gzp/Github/mymcp/config.yaml | head -20
```

### 手动测试 MCP 服务

```bash
# 测试服务是否能正常启动
cd /Users/gzp/Github/mymcp
uvx mymcp --config config.yaml --help
```

## 🐛 故障排除

### 问题 1: MCP 服务未连接

**症状**: Cursor 中看不到 mymcp 服务

**解决**:
1. 检查配置文件路径是否正确
2. 确认 `uvx` 命令可用: `which uvx`
3. 查看 Cursor 的 MCP 日志
4. 重启 Cursor

### 问题 2: 命令不可用

**症状**: 工具列表中看不到命令

**解决**:
1. 检查 `config.yaml` 中的命令是否 `enabled: true`
2. 查看配置文件语法是否正确
3. 检查日志文件: `cat mcp.log`

### 问题 3: IntelliJ 命令失败

**症状**: IntelliJ 相关命令返回错误

**解决**:
1. 确认 IntelliJ-RunControl 插件已安装并启用
2. 检查 Token 是否正确设置
3. 验证 IntelliJ IDEA 正在运行
4. 测试 HTTP API 直接调用:
   ```bash
   curl -H "X-IntelliJ-Token: $INTELLIJ_RUNCONTROL_TOKEN" \
     http://127.0.0.1:17777/projects
   ```

### 问题 4: 环境变量未传递

**症状**: Token 相关错误

**解决**:
1. 检查环境变量是否设置: `echo $INTELLIJ_RUNCONTROL_TOKEN`
2. 在 Cursor MCP 配置中直接设置 `env`（已在配置中）
3. 重启 Cursor

## 📊 查看日志

### MyMCP 日志

```bash
# 如果启用了日志文件
tail -f /Users/gzp/Github/mymcp/mcp.log

# 或启动时查看输出
cd /Users/gzp/Github/mymcp
uvx mymcp --config config.yaml --log-level DEBUG
```

### Cursor MCP 日志

Cursor 的 MCP 日志位置：
```
~/Library/Application Support/Cursor/logs/*/exthost/anysphere.cursor-mcp/
```

或者查看 Cursor 的输出面板中的 MCP 相关日志。

## 🎯 测试清单

- [ ] Cursor 已重启
- [ ] MCP 服务已连接（在 Cursor 中可见）
- [ ] 可以列出工具
- [ ] 基础命令可以调用
- [ ] IntelliJ 命令可以调用（如果配置了）
- [ ] 环境变量正确传递
- [ ] 日志无错误

## 💡 提示

1. **首次使用**: 建议先测试简单的命令，确认基本功能正常
2. **调试模式**: 使用 `--log-level DEBUG` 查看详细日志
3. **管理界面**: 使用 `--admin` 启动管理界面查看状态
4. **配置热重载**: 修改配置文件后会自动重载，无需重启

## 📚 相关文档

- [快速开始指南](QUICK_START_INTELLIJ.md)
- [IntelliJ 集成文档](docs/intellij-integration.md)
- [测试指南](TEST_INTELLIJ.md)

## 🎉 成功标志

如果一切正常，你应该能够：
- ✅ 在 Cursor 中看到 mymcp 服务
- ✅ 列出所有可用工具
- ✅ 成功调用命令并获得响应
- ✅ IntelliJ 相关命令正常工作（如果配置了）

祝测试顺利！🚀

