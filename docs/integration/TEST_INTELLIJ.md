# IntelliJ-RunControl 集成测试指南

## 测试准备

### 1. 确保 IntelliJ-RunControl 插件运行

1. 打开 IntelliJ IDEA
2. 确认插件已安装并启用
3. **Settings → Tools → RunControl** 确认 HTTP API 已启用
4. 复制 API Token

### 2. 设置环境变量

```bash
export INTELLIJ_RUNCONTROL_TOKEN="your_token_here"
```

### 3. 准备配置文件

```bash
# 复制示例配置
cp config.intellij-example.yaml config.yaml

# 验证配置
cat config.yaml | grep -A 2 "intellij_auth"
```

## 测试步骤

### 步骤 1: 测试 HTTP API 直接调用

```bash
# 测试列出项目
curl -H "X-IntelliJ-Token: $INTELLIJ_RUNCONTROL_TOKEN" \
  http://127.0.0.1:17777/projects

# 测试列出运行配置
curl -H "X-IntelliJ-Token: $INTELLIJ_RUNCONTROL_TOKEN" \
  http://127.0.0.1:17777/run-configs
```

如果这些命令成功，说明 IntelliJ-RunControl 插件正常工作。

### 步骤 2: 测试 MyMCP 服务

```bash
# 启动 MyMCP 服务（带管理端）
uvx mymcp --config config.yaml --admin

# 在另一个终端，访问管理界面
# http://localhost:18888
```

### 步骤 3: 测试 MCP 工具列表

使用 MCP 客户端测试工具列表：

```python
# test_mcp_tools.py
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_tools():
    server_params = StdioServerParameters(
        command="uvx",
        args=["mymcp", "--config", "config.yaml"]
    )
    
    stdio_transport = await stdio_client(server_params)
    async with ClientSession(stdio_transport[0], stdio_transport[1]) as session:
        # 列出工具
        result = await session.list_tools()
        print(f"找到 {len(result.tools)} 个工具:")
        for tool in result.tools:
            if tool.name.startswith("intellij_"):
                print(f"  - {tool.name}: {tool.description}")

if __name__ == "__main__":
    asyncio.run(test_tools())
```

运行：
```bash
python test_mcp_tools.py
```

### 步骤 4: 测试工具调用

```python
# test_tool_call.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_call():
    server_params = StdioServerParameters(
        command="uvx",
        args=["mymcp", "--config", "config.yaml"]
    )
    
    stdio_transport = await stdio_client(server_params)
    async with ClientSession(stdio_transport[0], stdio_transport[1]) as session:
        # 调用工具
        result = await session.call_tool(
            "intellij_list_projects",
            {}
        )
        print("结果:")
        for content in result.content:
            print(content.text)

if __name__ == "__main__":
    asyncio.run(test_call())
```

### 步骤 5: 配置 Cursor MCP

1. 找到配置文件：
   ```bash
   # macOS
   open ~/Library/Application\ Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
   
   # 或手动编辑
   nano ~/Library/Application\ Support/Cursor/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
   ```

2. 添加配置（使用绝对路径）：
   ```json
   {
     "mcpServers": {
       "mymcp": {
         "command": "uvx",
         "args": [
           "mymcp",
           "--config",
           "/Users/your_username/path/to/mymcp/config.yaml"
         ],
         "env": {
           "INTELLIJ_RUNCONTROL_TOKEN": "your_token_here"
         }
       }
     }
   }
   ```

3. 重启 Cursor

4. 在 Cursor 中测试：
   - 打开 Cursor
   - 尝试说："列出我的 IntelliJ 项目"
   - 或："启动我的 Spring Boot 应用"

## 验证清单

- [ ] IntelliJ-RunControl 插件已安装并启用
- [ ] HTTP API 已启用（Settings → Tools → RunControl）
- [ ] API Token 已获取并设置到环境变量
- [ ] 配置文件 `config.yaml` 已创建
- [ ] MyMCP 服务可以启动
- [ ] 工具列表包含 `intellij_*` 命令
- [ ] 可以调用 `intellij_list_projects` 工具
- [ ] Cursor MCP 配置已添加
- [ ] Cursor 中可以识别 IntelliJ 相关命令

## 常见问题

### 问题 1: Token 认证失败

**症状**: 401 Unauthorized

**解决**:
- 检查环境变量是否正确设置
- 验证 Token 是否与 IntelliJ 插件中的一致
- 确认配置文件中的鉴权配置正确

### 问题 2: 连接被拒绝

**症状**: Connection refused

**解决**:
- 确认 IntelliJ-RunControl 插件 HTTP API 已启用
- 检查端口是否为 17777（或插件设置中的端口）
- 确认 IntelliJ IDEA 正在运行

### 问题 3: 工具不可用

**症状**: 工具列表中看不到 `intellij_*` 命令

**解决**:
- 检查配置文件是否正确加载
- 确认命令的 `enabled: true`
- 查看日志文件确认错误

### 问题 4: Cursor 中无法使用

**症状**: Cursor 中无法识别命令

**解决**:
- 确认配置文件路径是绝对路径
- 检查环境变量是否正确传递
- 重启 Cursor
- 查看 Cursor 的 MCP 日志

## 调试技巧

### 查看日志

```bash
# MyMCP 日志
tail -f mcp.log

# 或启动时查看输出
uvx mymcp --config config.yaml --admin --log-level DEBUG
```

### 测试单个命令

```bash
# 使用 curl 直接测试
curl -H "X-IntelliJ-Token: $INTELLIJ_RUNCONTROL_TOKEN" \
  http://127.0.0.1:17777/run-configs

# 使用管理界面测试
# http://localhost:18888/api/commands
```

## 下一步

集成成功后，你可以：
1. 在 Cursor 中直接控制 IntelliJ IDEA 的运行配置
2. 查看应用日志
3. 搜索错误信息
4. 自动化开发工作流

享受使用！🎉

