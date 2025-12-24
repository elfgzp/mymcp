# Rainbow MCP 服务兼容性问题修复指南

## 问题描述

Rainbow MCP 服务在调用 `list_tools()` 时返回 "Invalid request parameters" 错误。

## 根本原因

从日志分析，问题可能是：

1. **MCP SDK 版本不兼容**：Rainbow MCP 服务使用的 MCP SDK 版本较旧，不支持新的分页参数（`cursor` 和 `params`）
2. **协议版本差异**：MCP 客户端库（mymcp 使用）支持新的分页参数，但 Rainbow MCP 服务不支持

## 解决方案

### 方案 1：更新 Rainbow MCP 服务的 MCP SDK（推荐）

在 Rainbow MCP 服务的 `pyproject.toml` 或 `requirements.txt` 中，明确指定最新版本的 MCP SDK：

```toml
# pyproject.toml
dependencies = [
    "mcp>=1.0.0",  # 使用最新版本
    # ... 其他依赖
]
```

或者：

```txt
# requirements.txt
mcp>=1.0.0
```

然后重新安装依赖：

```bash
cd /Users/gzp/Work/rainbow_admin_py_sdk
pip install -U mcp
# 或者
uv pip install -U mcp
```

### 方案 2：在 Rainbow MCP 服务中添加分页支持

如果 Rainbow MCP 服务需要保持旧版本兼容性，可以在 `mcp_server.py` 中修改 `list_tools()` 方法，添加对分页参数的支持：

```python
@server.list_tools()
async def list_tools(cursor: str | None = None, params: Any = None) -> list[Tool]:
    """列出所有可用的工具（支持分页参数以兼容新版本 MCP SDK）"""
    # 忽略分页参数，返回所有工具
    return get_tools()
```

### 方案 3：在 mymcp 中添加兼容性处理（已实现）

mymcp 已经实现了以下兼容性处理：

1. **延迟等待**：连接建立后等待 0.5 秒
2. **重试机制**：最多重试 3 次，使用指数退避
3. **参数处理**：正确处理可选参数，尝试使用默认值
4. **错误诊断**：记录详细的错误信息和服务器 capabilities

## 当前状态

- ✅ mymcp 已实现通用兼容性处理
- ⚠️ Rainbow MCP 服务需要更新 MCP SDK 版本或添加分页支持
- ⚠️ 问题可能需要在 Rainbow MCP 服务端修复

## 建议操作

1. **立即操作**：更新 Rainbow MCP 服务的 MCP SDK 到最新版本
2. **如果无法更新**：在 Rainbow MCP 服务中添加分页参数支持（即使不使用）
3. **验证**：重启 Cursor，查看日志确认问题是否解决

## 相关文件

- Rainbow MCP 服务：`/Users/gzp/Work/rainbow_admin_py_sdk/mcp_server.py`
- mymcp 客户端：`/Users/gzp/Github/mymcp/src/mcp_client/client.py`
- 兼容性文档：`/Users/gzp/Github/mymcp/docs/development/MCP_COMPATIBILITY.md`

