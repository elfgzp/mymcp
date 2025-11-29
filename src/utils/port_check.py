"""端口检查工具"""

import socket
import logging

logger = logging.getLogger(__name__)


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 18888, max_attempts: int = 100) -> int:
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    raise RuntimeError(f"无法在 {start_port}-{start_port + max_attempts} 范围内找到可用端口")


def check_and_warn_port(port: int, service_name: str = "服务") -> bool:
    """检查端口并警告"""
    if not is_port_available(port):
        logger.warning(f"{service_name} 端口 {port} 已被占用，可能导致启动失败")
        return False
    return True

