#!/usr/bin/env python3
"""基础功能测试脚本"""

import asyncio
import sys
import yaml
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.manager import ConfigManager
from config.models import Config
from command.manager import CommandManager
from auth.manager import AuthManager


async def test_config_loading():
    """测试配置加载"""
    print("=" * 50)
    print("测试 1: 配置加载")
    print("=" * 50)
    
    # 创建测试配置
    test_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 0,
            "admin_port": 18888
        },
        "commands": [
            {
                "name": "test_command",
                "description": "测试命令",
                "type": "http",
                "enabled": True,
                "http": {
                    "method": "GET",
                    "url": "https://httpbin.org/get",
                    "params": {
                        "test": "{param}"
                    }
                },
                "parameters": [
                    {
                        "name": "param",
                        "type": "string",
                        "required": True,
                        "description": "测试参数"
                    }
                ]
            }
        ],
        "auth_configs": [],
        "mcp_servers": [],
        "global": {
            "default_timeout": 30,
            "log_level": "INFO"
        }
    }
    
    # 写入临时配置文件
    config_path = Path("test_config.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(test_config, f, allow_unicode=True)
    
    try:
        # 测试加载
        config_manager = ConfigManager(str(config_path))
        config = config_manager.load_config()
        
        print(f"✓ 配置加载成功")
        print(f"  - 服务器端口: {config.server.port}")
        print(f"  - 管理端端口: {config.server.admin_port}")
        print(f"  - 命令数量: {len(config.commands)}")
        print(f"  - MCP 服务数量: {len(config.mcp_servers)}")
        
        # 测试命令管理器
        auth_manager = AuthManager(config)
        command_manager = CommandManager(config, auth_manager)
        tools = command_manager.get_all_tools()
        
        print(f"✓ 命令管理器初始化成功")
        print(f"  - 工具数量: {len(tools)}")
        if tools:
            print(f"  - 工具名称: {tools[0].name}")
            print(f"  - 工具描述: {tools[0].description}")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理
        if config_path.exists():
            config_path.unlink()


async def test_env_variable_resolution():
    """测试环境变量解析"""
    print("\n" + "=" * 50)
    print("测试 2: 环境变量解析")
    print("=" * 50)
    
    import os
    os.environ["TEST_API_KEY"] = "test_key_12345"
    
    test_config = {
        "auth_configs": [
            {
                "name": "test_auth",
                "type": "api_key",
                "api_key": {
                    "location": "header",
                    "name": "X-API-Key",
                    "value": "${TEST_API_KEY}"
                }
            }
        ]
    }
    
    config_path = Path("test_config_env.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(test_config, f, allow_unicode=True)
    
    try:
        config_manager = ConfigManager(str(config_path))
        config = config_manager.load_config()
        
        auth_config = config.auth_configs[0]
        if auth_config.api_key:
            resolved_value = auth_config.api_key.value
            print(f"✓ 环境变量解析成功")
            print(f"  - 原始值: ${{TEST_API_KEY}}")
            print(f"  - 解析后: {resolved_value}")
            
            if resolved_value == "test_key_12345":
                print(f"✓ 解析结果正确")
                return True
            else:
                print(f"✗ 解析结果错误，期望: test_key_12345, 实际: {resolved_value}")
                return False
        else:
            print(f"✗ 未找到 API Key 配置")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if config_path.exists():
            config_path.unlink()
        os.environ.pop("TEST_API_KEY", None)


async def main():
    """主测试函数"""
    print("\n开始基础功能测试...\n")
    
    results = []
    
    # 测试 1: 配置加载
    results.append(await test_config_loading())
    
    # 测试 2: 环境变量解析
    results.append(await test_env_variable_resolution())
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

