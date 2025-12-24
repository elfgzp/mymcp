#!/usr/bin/env python3
"""
测试 Rainbow MCP 服务连接的脚本
用于调试 "Invalid request parameters" 错误
"""

import asyncio
import logging
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

async def test_rainbow_connection():
    """测试 Rainbow MCP 服务连接"""
    logger.info("=" * 60)
    logger.info("开始测试 Rainbow MCP 服务连接")
    logger.info("=" * 60)
    
    # 使用与 mymcp 相同的配置
    server_params = StdioServerParameters(
        command="uvx",
        args=[
            "--from",
            "git+ssh://git@git.woa.com/elfguan/rainbow_admin_py_sdk.git@master",
            "rainbow-mcp-server"
        ],
        env={
            "RAINBOW_AUTO_REFRESH_COOKIE": "true",
            "RAINBOW_BASE_URL": "http://rainbow.oa.com",
            "RAINBOW_DISABLE_CONNECTION_REUSE": "true"
        }
    )
    
    try:
        logger.info("创建 stdio_client...")
        stdio_transport_context = stdio_client(server_params)
        
        logger.info("等待 stdio 传输建立...")
        read_stream, write_stream = await stdio_transport_context.__aenter__()
        logger.info("✓ stdio 传输已建立")
        
        logger.info("创建 ClientSession...")
        session = ClientSession(read_stream, write_stream)
        
        logger.info("初始化会话（调用 __aenter__）...")
        init_result = await session.__aenter__()
        logger.info(f"✓ 会话初始化成功，结果类型: {type(init_result)}")
        
        # 检查 session 状态
        if hasattr(session, '_initialized'):
            logger.info(f"session._initialized: {session._initialized}")
        if hasattr(session, '_server_info'):
            logger.info(f"session._server_info: {session._server_info}")
        
        # 等待一下，确保初始化完成
        logger.info("等待 1 秒，确保初始化完成...")
        await asyncio.sleep(1.0)
        
        logger.info("调用 list_tools()...")
        try:
            # 检查方法签名
            import inspect
            sig = inspect.signature(session.list_tools)
            logger.info(f"list_tools 方法签名: {sig}")
            
            # 调用 list_tools
            result = await session.list_tools()
            logger.info(f"✓ 成功获取 {len(result.tools)} 个工具")
            
            # 显示前 5 个工具名称
            if result.tools:
                tool_names = [tool.name for tool in result.tools[:5]]
                logger.info(f"工具列表（前5个）: {tool_names}")
            
            logger.info("=" * 60)
            logger.info("✓ 测试成功！")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"✗ 调用 list_tools 失败: {type(e).__name__}: {str(e)}")
            logger.error("=" * 60, exc_info=True)
            return False
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ 连接失败: {type(e).__name__}: {str(e)}")
        logger.error("=" * 60, exc_info=True)
        return False
    finally:
        try:
            if 'stdio_transport_context' in locals():
                await stdio_transport_context.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"清理资源时出错: {e}")

if __name__ == "__main__":
    success = asyncio.run(test_rainbow_connection())
    sys.exit(0 if success else 1)

