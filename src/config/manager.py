"""配置管理器"""

import yaml
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .models import Config


class ConfigWatcher(FileSystemEventHandler):
    """配置文件监控器"""

    def __init__(self, config_manager: "ConfigManager"):
        self.config_manager = config_manager

    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory and event.src_path == str(self.config_manager.config_path):
            self.config_manager.reload_config()


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Optional[Config] = None
        self.observer: Optional[Observer] = None
        self.on_config_changed = None  # 回调函数

    def load_config(self) -> Config:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.config = Config(**data)
        self.config.resolve_env_vars()
        return self.config

    def save_config(self, config: Config) -> None:
        """保存配置文件"""
        # 转换为字典（排除环境变量解析后的值）
        data = config.model_dump(exclude_none=True, by_alias=True)
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # 重新加载以触发变更检测
        self.reload_config()

    def reload_config(self) -> None:
        """重新加载配置"""
        old_config = self.config
        self.config = self.load_config()
        
        if self.on_config_changed and old_config:
            # 如果回调是协程，需要异步执行
            import asyncio
            import inspect
            if inspect.iscoroutinefunction(self.on_config_changed):
                # 创建任务异步执行
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.on_config_changed(old_config, self.config))
                    else:
                        loop.run_until_complete(self.on_config_changed(old_config, self.config))
                except RuntimeError:
                    # 如果没有事件循环，创建新的
                    asyncio.run(self.on_config_changed(old_config, self.config))
            else:
                # 同步回调
                self.on_config_changed(old_config, self.config)

    def start_watching(self) -> None:
        """开始监控配置文件"""
        if not self.config_path.exists():
            return

        self.observer = Observer()
        event_handler = ConfigWatcher(self)
        self.observer.schedule(
            event_handler,
            str(self.config_path.parent),
            recursive=False
        )
        self.observer.start()

    def stop_watching(self) -> None:
        """停止监控配置文件"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def get_config(self) -> Config:
        """获取当前配置"""
        if self.config is None:
            self.load_config()
        return self.config

