# MCP 服务兼容性处理指南

## 问题描述

某些 MCP 服务在调用 `list_tools()` 时可能返回 "Invalid request parameters" 错误，这通常是由于以下原因：

1. **MCP 协议版本不兼容**：不同版本的 MCP SDK 可能有不同的协议实现
2. **服务初始化时间**：某些服务需要额外的初始化时间
3. **参数传递问题**：虽然 `list_tools()` 理论上不需要参数，但某些实现可能有特殊要求

## 通用解决方案

### 1. 延迟等待机制

在连接建立后，等待一小段时间再调用 `list_tools()`，确保服务完全启动：

```python
# 等待服务完全启动
await asyncio.sleep(0.5)
tools = await client.list_tools()
```

### 2. 重试机制

添加重试逻辑，使用指数退避策略：

```python
max_retries = 3
retry_delay = 1.0

for attempt in range(max_retries):
    try:
        tools = await client.list_tools()
        break
    except Exception as e:
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # 指数退避
        else:
            raise
```

### 3. 错误处理和诊断

当遇到 "Invalid request parameters" 错误时，记录详细信息以便诊断：

```python
try:
    result = await self.session.list_tools()
except Exception as e:
    error_msg = str(e)
    if "Invalid request parameters" in error_msg:
        logger.warning("检测到 'Invalid request parameters' 错误，可能是 MCP 协议版本不兼容")
        # 记录服务器 capabilities
        if hasattr(self.session, 'initialize_result'):
            init_result = self.session.initialize_result
            logger.debug(f"服务器 capabilities: {init_result.capabilities}")
    raise
```

### 4. 方法签名检查

检查 `list_tools()` 方法的签名，确保调用方式正确：

```python
import inspect
sig = inspect.signature(self.session.list_tools)
logger.debug(f"list_tools 方法签名: {sig}")

# 根据签名调用
if len(sig.parameters) == 0:
    result = await self.session.list_tools()
else:
    # 处理需要参数的情况
    result = await self.session.list_tools()
```

## 已实现的改进

在 `mymcp` 中，我们已经实现了以下改进：

1. **延迟等待**：在 `McpClientManager.add_server()` 中，连接建立后等待 0.5 秒
2. **重试机制**：最多重试 3 次，使用指数退避（1秒、2秒、4秒）
3. **详细日志**：记录方法签名、错误详情和服务器 capabilities

## 针对特定服务的处理

### Rainbow MCP 服务

Rainbow MCP 服务使用未指定版本的 `mcp` 库，可能导致版本兼容性问题。建议：

1. 确保 Rainbow MCP 服务使用最新版本的 MCP SDK
2. 如果问题持续，考虑在 Rainbow MCP 服务中添加更详细的错误处理

### 其他 MCP 服务

对于其他可能遇到类似问题的 MCP 服务：

1. 检查服务的 MCP SDK 版本
2. 查看服务的错误日志
3. 如果可能，更新服务到最新版本

## 最佳实践

1. **版本管理**：在 `pyproject.toml` 或 `requirements.txt` 中明确指定 MCP SDK 版本
2. **错误处理**：实现健壮的错误处理和重试机制
3. **日志记录**：记录详细的调试信息，便于问题诊断
4. **兼容性测试**：定期测试与不同 MCP 服务的兼容性

## 相关文件

- `src/mcp_client/client.py`：MCP 客户端实现，包含错误处理
- `src/mcp_client/manager.py`：MCP 客户端管理器，包含重试机制
- `src/mcp_client/connection.py`：MCP 连接实现

