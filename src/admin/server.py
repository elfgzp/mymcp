"""管理端服务器"""

import asyncio
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .routes import router
from ..utils.port_check import check_and_warn_port, find_available_port

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(title="MyMCP Admin", version="0.1.0")
    
    # 注册路由
    app.include_router(router, prefix="/api")
    
    # 静态文件和主页
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MyMCP Admin</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                a { color: #007bff; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>MyMCP 管理界面</h1>
            <div class="section">
                <h2>API 端点</h2>
                <ul>
                    <li><a href="/api/commands">命令管理</a></li>
                    <li><a href="/api/mcp-servers">MCP 服务管理</a></li>
                    <li><a href="/api/auth-configs">鉴权配置管理</a></li>
                    <li><a href="/api/config">配置管理</a></li>
                </ul>
            </div>
            <div class="section">
                <h2>API 文档</h2>
                <p><a href="/docs">Swagger UI</a> | <a href="/redoc">ReDoc</a></p>
            </div>
        </body>
        </html>
        """
    
    return app


async def run_admin_server(port: int = 18888) -> None:
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
    
    app = create_app()
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    logger.info(f"管理端服务器启动在端口 {port}")
    await server.serve()


def main(port: int = 18888) -> None:
    """主函数（同步版本）"""
    asyncio.run(run_admin_server(port))

