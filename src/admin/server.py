"""管理端服务器"""

import asyncio
import logging
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from ..utils.port_check import check_and_warn_port, find_available_port

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    from .routes import router
    from pathlib import Path
    
    app = FastAPI(title="MyMCP Admin", version="0.1.0")
    
    # 注册路由
    app.include_router(router, prefix="/api")
    
    # 静态文件服务
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # 主页
    @app.get("/", response_class=HTMLResponse)
    async def index():
        """返回管理界面 HTML"""
        # 获取模板文件路径
        template_path = Path(__file__).parent / "templates" / "index.html"
        
        if not template_path.exists():
            return HTMLResponse(
                content="<h1>错误</h1><p>模板文件不存在: " + str(template_path) + "</p>",
                status_code=500
            )
        
        # 读取 HTML 文件
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
    
    return app


async def run_admin_server(port: int = 18888, config_path: Optional[str] = None, mcp_server_getter=None) -> None:
    """运行管理端服务器"""
    # 检查端口是否可用
    if not check_and_warn_port(port, "管理端"):
        # 尝试查找可用端口
        try:
            port = find_available_port(port)
            logger.info(f"使用备用端口: {port}")
        except RuntimeError as e:
            logger.error(f"无法找到可用端口: {e}")
            raise
    
    # 设置管理端上下文
    if config_path:
        from .routes import set_admin_context
        # mcp_server_getter 是一个函数，用于获取当前的 mcp_server 实例
        set_admin_context(config_path, mcp_server_getter)
    
    app = create_app()
    # 将 uvicorn 日志重定向到 stderr，避免干扰 MCP 协议的 stdout
    import sys
    import logging
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(logging.INFO)
    
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        log_config=None  # 禁用默认日志配置
    )
    server = uvicorn.Server(config)
    logger.info(f"管理端服务器启动在端口 {port}")
    await server.serve()


def main(port: int = 18888) -> None:
    """主函数（同步版本）"""
    asyncio.run(run_admin_server(port))

