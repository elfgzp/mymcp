# Rainbow MCP 服务问题排查指南

## 当前状态

### ✅ 已完成的修复

1. **Rainbow MCP 服务代码修复**
   - `list_tools()` 函数签名已修复为无参数
   - MCP SDK 版本已更新为 `mcp>=1.0.0`
   - 代码已提交到 Git 仓库（提交 `d943fcf`）

2. **mymcp 客户端改进**
   - 智能参数传递策略
   - 重试机制（最多 3 次，指数退避）
   - 详细诊断日志

### ⚠️ 问题仍然存在

即使代码已修复，Rainbow MCP 服务仍然返回 "Invalid request parameters" 错误。

## 可能的原因

### 1. uvx 缓存问题

`uvx` 可能缓存了旧版本的 Rainbow MCP 服务代码。即使代码已更新，`uvx` 可能仍在使用缓存的旧版本。

**解决方案：**
- 等待缓存自动过期（通常几小时到一天）
- 手动清除 uvx 缓存（如果支持）
- 在配置中明确指定分支或提交（已添加 `@master`）

### 2. MCP SDK 版本不匹配

Rainbow MCP 服务运行时使用的 MCP SDK 版本可能仍然是旧版本，即使 `pyproject.toml` 中已更新。

**可能的原因：**
- `uvx` 在安装依赖时使用了缓存的旧版本
- 依赖解析时选择了旧版本

**解决方案：**
- 检查 Rainbow MCP 服务实际使用的 MCP SDK 版本
- 强制重新安装依赖

### 3. 协议版本不兼容

即使代码和 SDK 版本都正确，可能存在协议层面的不兼容。

## 排查步骤

### 步骤 1：确认代码已更新

```bash
cd /Users/gzp/Work/rainbow_admin_py_sdk
git log --oneline -3
# 应该看到提交 d943fcf 或 a91c3b3
```

### 步骤 2：检查配置

确认 `~/.cursor/mymcp-config.yaml` 中已指定分支：

```yaml
args:
  - "--from"
  - "git+ssh://git@git.woa.com/elfguan/rainbow_admin_py_sdk.git@master"
  - "rainbow-mcp-server"
```

### 步骤 3：重启 Cursor

完全重启 Cursor，确保：
- 使用最新的 mymcp 代码
- 使用最新的配置
- 重新连接 Rainbow MCP 服务

### 步骤 4：查看日志

```bash
# 查看最新的 Rainbow 服务连接日志
tail -100 ~/.mymcp/mymcp.log | grep -E "rainbow|list_tools" | tail -20

# 查看是否有成功连接
grep "rainbow.*✓.*工具" ~/.mymcp/mymcp.log
```

### 步骤 5：手动测试 Rainbow MCP 服务

如果问题持续，可以手动测试 Rainbow MCP 服务：

```bash
# 使用 uvx 直接运行 Rainbow MCP 服务
uvx --from git+ssh://git@git.woa.com/elfguan/rainbow_admin_py_sdk.git@master rainbow-mcp-server

# 或者使用本地代码
cd /Users/gzp/Work/rainbow_admin_py_sdk
python3 -m mcp_server
```

## 临时解决方案

如果问题持续且急需使用 Rainbow MCP 服务，可以考虑：

1. **暂时禁用 Rainbow 服务**：在配置中设置 `enabled: false`
2. **使用其他方式访问 Rainbow**：直接使用 Rainbow 的 API 或 CLI 工具
3. **等待缓存过期**：等待 uvx 缓存自动过期后重试

## 长期解决方案

1. **版本固定**：在 Rainbow MCP 服务的 `pyproject.toml` 中固定 MCP SDK 版本
2. **CI/CD 验证**：添加自动化测试，确保 Rainbow MCP 服务能够正常连接
3. **监控和告警**：添加监控，及时发现连接问题

## 相关文档

- [MCP 兼容性处理指南](./MCP_COMPATIBILITY.md)
- [Rainbow MCP 修复指南](./RAINBOW_MCP_FIX.md)
- [Rainbow MCP 验证指南](./RAINBOW_MCP_VERIFICATION.md)
- [Rainbow MCP 修复状态](./RAINBOW_MCP_STATUS.md)

