#!/usr/bin/env python3
"""测试 tapd MCP 服务连接

使用方法:
    uvx --from . python scripts/test_tapd_connection.py
    或者
    python scripts/test_tapd_connection.py  # 需要先安装依赖
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("错误: 无法导入 mcp 模块")
    print("请使用以下方式运行:")
    print("  uvx --from . python scripts/test_tapd_connection.py")
    sys.exit(1)


async def test_tapd_connection():
    """测试 tapd 连接"""
    print("=" * 60)
    print("测试 tapd MCP 服务连接")
    print("=" * 60)
    
    # 检查环境变量
    print("\n1. 检查环境变量:")
    env_vars = {
        'TAPD_ACCESS_TOKEN': os.getenv('TAPD_ACCESS_TOKEN', ''),
        'TAPD_API_BASE_URL': os.getenv('TAPD_API_BASE_URL', ''),
        'TAPD_BASE_URL': os.getenv('TAPD_BASE_URL', ''),
        'BOT_URL': os.getenv('BOT_URL', ''),
        'CURRENT_USER_NICK': os.getenv('CURRENT_USER_NICK', ''),
    }
    
    for key, value in env_vars.items():
        if value:
            # 隐藏敏感信息
            if 'TOKEN' in key or 'PASSWORD' in key:
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✓ {key} = {display_value}")
        else:
            print(f"  ✗ {key} = (未设置)")
    
    # 准备环境变量
    process_env = {**os.environ}
    filtered_env = {k: v for k, v in env_vars.items() if v}
    if filtered_env:
        process_env.update(filtered_env)
        print(f"\n  使用 {len(filtered_env)} 个环境变量")
    
    # 创建服务器参数
    print("\n2. 创建服务器参数...")
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-tapd"],
        env=process_env
    )
    print("  ✓ 服务器参数创建成功")
    
    # 测试连接
    print("\n3. 建立 stdio 连接...")
    stdio_transport_context = stdio_client(server_params)
    
    try:
        print("  等待 stdio 传输建立...")
        read_stream, write_stream = await asyncio.wait_for(
            stdio_transport_context.__aenter__(),
            timeout=60
        )
        print("  ✓ stdio 传输已建立")
        
        # 创建会话
        print("\n4. 创建 ClientSession...")
        session = ClientSession(read_stream, write_stream)
        print("  ✓ ClientSession 创建成功")
        
        # 测试初始化方式 1: 使用 __aenter__
        print("\n5. 测试初始化方式 1: 使用 session.__aenter__()...")
        try:
            init_result = await asyncio.wait_for(
                session.__aenter__(),
                timeout=30
            )
            print(f"  ✓ session.__aenter__() 成功")
            print(f"    返回类型: {type(init_result)}")
            
            # 检查会话状态
            if hasattr(session, '_initialized'):
                print(f"    session._initialized: {session._initialized}")
            if hasattr(session, '_server_info'):
                print(f"    session._server_info: {session._server_info}")
            
            # 测试是否可以直接调用 list_tools
            print("\n6. 测试直接调用 list_tools()（不调用 initialize()）...")
            try:
                result = await asyncio.wait_for(
                    session.list_tools(),
                    timeout=10
                )
                print(f"  ✓ list_tools() 成功！")
                print(f"    工具数量: {len(result.tools)}")
                if result.tools:
                    print(f"    前 3 个工具:")
                    for tool in result.tools[:3]:
                        print(f"      - {tool.name}: {tool.description[:50] if tool.description else 'N/A'}...")
                return True
            except Exception as e:
                print(f"  ✗ list_tools() 失败: {type(e).__name__}: {e}")
                
                # 如果失败，尝试调用 initialize()
                print("\n7. 测试调用 initialize() 后再次调用 list_tools()...")
                try:
                    init_result2 = await asyncio.wait_for(
                        session.initialize(),
                        timeout=10
                    )
                    print(f"  ✓ initialize() 成功")
                    if hasattr(init_result2, 'serverInfo'):
                        print(f"    服务器信息: {init_result2.serverInfo}")
                    
                    # 再次尝试 list_tools
                    result = await asyncio.wait_for(
                        session.list_tools(),
                        timeout=10
                    )
                    print(f"  ✓ list_tools() 成功！")
                    print(f"    工具数量: {len(result.tools)}")
                    return True
                except Exception as e2:
                    print(f"  ✗ initialize() 或 list_tools() 失败: {type(e2).__name__}: {e2}")
                    import traceback
                    traceback.print_exc()
                    return False
                    
        except Exception as e:
            print(f"  ✗ session.__aenter__() 失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 清理
            try:
                await session.__aexit__(None, None, None)
            except Exception as e:
                print(f"  警告: 清理 session 时出错: {e}")
            try:
                await stdio_transport_context.__aexit__(None, None, None)
            except Exception as e:
                print(f"  警告: 清理 stdio 传输时出错: {e}")
                
    except asyncio.TimeoutError:
        print("  ✗ stdio 传输建立超时（60秒）")
        return False
    except Exception as e:
        print(f"  ✗ 建立连接失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tapd_without_initialize():
    """测试不调用 initialize() 的情况"""
    print("\n" + "=" * 60)
    print("测试 2: 不调用 initialize()，直接使用 __aenter__ 的结果")
    print("=" * 60)
    
    process_env = {**os.environ}
    env_vars = {
        'TAPD_ACCESS_TOKEN': os.getenv('TAPD_ACCESS_TOKEN', ''),
        'TAPD_API_BASE_URL': os.getenv('TAPD_API_BASE_URL', ''),
        'TAPD_BASE_URL': os.getenv('TAPD_BASE_URL', ''),
    }
    filtered_env = {k: v for k, v in env_vars.items() if v}
    if filtered_env:
        process_env.update(filtered_env)
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-tapd"],
        env=process_env
    )
    
    stdio_transport_context = stdio_client(server_params)
    
    try:
        read_stream, write_stream = await asyncio.wait_for(
            stdio_transport_context.__aenter__(),
            timeout=60
        )
        
        async with ClientSession(read_stream, write_stream) as session:
            print("  ✓ 使用 async with ClientSession 成功")
            
            # 直接调用 list_tools
            try:
                result = await asyncio.wait_for(
                    session.list_tools(),
                    timeout=10
                )
                print(f"  ✓ list_tools() 成功！")
                print(f"    工具数量: {len(result.tools)}")
                return True
            except Exception as e:
                print(f"  ✗ list_tools() 失败: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"  ✗ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await stdio_transport_context.__aexit__(None, None, None)
        except:
            pass


async def main():
    """主函数"""
    print("\n开始测试 tapd MCP 服务连接...\n")
    
    # 测试 1: 详细测试
    result1 = await test_tapd_connection()
    
    # 测试 2: 使用 async with 方式
    result2 = await test_tapd_without_initialize()
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)
    print(f"  测试 1 (详细测试): {'✓ 成功' if result1 else '✗ 失败'}")
    print(f"  测试 2 (async with): {'✓ 成功' if result2 else '✗ 失败'}")
    
    if result1 or result2:
        print("\n✓ 至少有一种方式可以成功连接")
    else:
        print("\n✗ 所有测试都失败，请检查:")
        print("  1. 环境变量是否正确设置")
        print("  2. mcp-server-tapd 是否正确安装")
        print("  3. 网络连接是否正常")


if __name__ == "__main__":
    asyncio.run(main())

