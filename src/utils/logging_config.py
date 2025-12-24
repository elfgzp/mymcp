"""日志配置工具"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_max_bytes: int = 10 * 1024 * 1024,
    log_backup_count: int = 5
) -> None:
    """配置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径，如果为 None 则只输出到 stderr
        log_max_bytes: 单个日志文件最大大小（字节），默认 10MB
        log_backup_count: 保留的日志文件数量，默认 5 个
    """
    # 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 添加 stderr 处理器（始终输出到 stderr，因为 MCP 协议使用 stdout）
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)
    
    # 如果配置了日志文件，添加文件处理器（滚动日志）
    if log_file:
        # 扩展 ~ 为用户主目录
        log_file_expanded = os.path.expanduser(log_file)
        log_path = Path(log_file_expanded)
        # 确保日志目录存在
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建滚动文件处理器
        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        logging.info(f"日志文件已配置: {log_path} (最大 {log_max_bytes // 1024 // 1024}MB, 保留 {log_backup_count} 个备份)")

