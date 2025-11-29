"""主入口模块"""

import asyncio
import argparse
import sys
from pathlib import Path

from .mcp_server import run_server


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MyMCP - 轻量级 MCP 自定义命令服务")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)"
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="启动管理端"
    )
    parser.add_argument(
        "--admin-port",
        type=int,
        default=18888,
        help="管理端端口 (默认: 18888)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)"
    )
    
    args = parser.parse_args()
    
    # 检查配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}", file=sys.stderr)
        print(f"提示: 请创建配置文件或使用 --config 指定配置文件路径", file=sys.stderr)
        sys.exit(1)
    
    # 如果启用管理端，需要导入管理端模块
    if args.admin:
        # 延迟导入管理端（按需加载）
        try:
            from .admin.server import run_admin_server
            from .utils.port_check import check_and_warn_port, find_available_port
            
            # 检查端口
            admin_port = args.admin_port
            if not check_and_warn_port(admin_port, "管理端"):
                try:
                    admin_port = find_available_port(admin_port)
                    print(f"警告: 原端口被占用，使用备用端口: {admin_port}", file=sys.stderr)
                except RuntimeError as e:
                    print(f"错误: 无法找到可用端口: {e}", file=sys.stderr)
                    sys.exit(1)
            
            # 在后台运行管理端
            import threading
            admin_thread = threading.Thread(
                target=lambda: asyncio.run(run_admin_server(admin_port)),
                daemon=True
            )
            admin_thread.start()
            print(f"管理端已启动: http://localhost:{admin_port}")
        except ImportError as e:
            print(f"警告: 无法启动管理端: {e}", file=sys.stderr)
    
    # 运行 MCP 服务器
    try:
        asyncio.run(run_server(str(config_path)))
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

