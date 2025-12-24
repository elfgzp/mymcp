#!/usr/bin/env python3
"""
检查 MCP SDK 版本的辅助脚本
可以通过 uvx 运行：uvx --from . check_mcp_version
"""

try:
    import mcp
    version = getattr(mcp, '__version__', 'unknown')
    print(f"✅ MCP SDK 版本: {version}")
    
    # 检查关键模块
    try:
        from mcp import ClientSession, StdioServerParameters
        print("✅ ClientSession 和 StdioServerParameters 可用")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    
    try:
        from mcp.server import Server
        print("✅ Server 可用")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        
except ImportError as e:
    print(f"❌ MCP SDK 未安装: {e}")
    print("提示: mymcp 通过 uvx 运行，MCP SDK 安装在 uvx 的虚拟环境中")

