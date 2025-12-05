"""主入口模块"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

from .mcp_server import run_server, McpServer


def find_default_config() -> Path:
    """查找默认配置文件"""
    # 按优先级查找配置文件
    config_locations = [
        Path("config.yaml"),  # 当前目录
        Path.home() / ".config" / "mymcp" / "config.yaml",  # 用户配置目录
    ]
    
    for config_path in config_locations:
        if config_path.exists():
            return config_path
    
    # 如果都不存在，返回当前目录的 config.yaml（用于创建）
    return Path("config.yaml")


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
    parser.add_argument(
        "--open-admin",
        action="store_true",
        help="启动后自动打开管理端浏览器 (默认: False)"
    )
    
    args = parser.parse_args()
    
    # 检查环境变量
    open_admin = args.open_admin or os.getenv("MYMCP_OPEN_ADMIN", "").lower() in ("true", "1", "yes")
    
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
            import webbrowser
            import time
            
            def start_admin_with_browser():
                """启动管理端并在启动后打开浏览器"""
                import socket
                url = f"http://localhost:{admin_port}"
                
                # 等待管理端启动（最多等待10秒）
                max_wait = 10
                waited = 0
                while waited < max_wait:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', admin_port))
                        sock.close()
                        if result == 0:
                            # 端口已打开，再等待一小段时间确保服务完全启动
                            time.sleep(0.5)
                            break
                    except Exception:
                        pass
                    time.sleep(0.5)
                    waited += 0.5
                
                # 打开浏览器
                if open_admin:
                    try:
                        webbrowser.open(url)
                        print(f"✅ 已自动打开管理端: {url}", file=sys.stderr)
                    except Exception as e:
                        print(f"⚠️  无法自动打开浏览器: {e}", file=sys.stderr)
                        print(f"   请手动访问: {url}", file=sys.stderr)
            
            admin_thread = threading.Thread(
                target=lambda: asyncio.run(run_admin_server(admin_port, str(config_path))),
                daemon=True
            )
            admin_thread.start()
            
            # 如果启用自动打开，启动浏览器线程
            if open_admin:
                browser_thread = threading.Thread(
                    target=start_admin_with_browser,
                    daemon=True
                )
                browser_thread.start()
            
            # 输出到 stderr，避免干扰 MCP 协议的 stdout
            print(f"管理端已启动: http://localhost:{admin_port}", file=sys.stderr)
            if not open_admin:
                print(f"提示: 使用 --open-admin 或设置 MYMCP_OPEN_ADMIN=1 可自动打开浏览器", file=sys.stderr)
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


def start_mcp_server():
    """启动 MCP 服务器（用于 uvx 从 git 仓库运行）"""
    parser = argparse.ArgumentParser(description="MyMCP - 启动 MCP 服务器")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径 (可选，默认自动查找)"
    )
    
    args = parser.parse_args()
    
    # 确定配置文件路径
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = find_default_config()
    
    # 检查配置文件是否存在
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}", file=sys.stderr)
        print(f"提示: 请创建配置文件或使用 --config 指定配置文件路径", file=sys.stderr)
        print(f"示例配置文件位置:", file=sys.stderr)
        print(f"  - 当前目录: ./config.yaml", file=sys.stderr)
        print(f"  - 用户配置: ~/.config/mymcp/config.yaml", file=sys.stderr)
        sys.exit(1)
    
    # 运行 MCP 服务器
    try:
        asyncio.run(run_server(str(config_path)))
    except KeyboardInterrupt:
        print("\n服务器已停止", file=sys.stderr)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

