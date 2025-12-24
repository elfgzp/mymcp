"""配置数据模型"""

from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field
import os


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 0  # MCP 服务器使用 stdio，不需要端口
    admin_port: int = 18888  # 管理端端口，使用不常用的端口避免冲突


class HttpCommandConfig(BaseModel):
    """HTTP 命令配置"""
    method: str = "GET"
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, str]] = None  # {"ref": "auth_config_name"}
    timeout: Optional[int] = None
    response_format: str = "json"  # json, xml, text


class ScriptCommandConfig(BaseModel):
    """脚本命令配置"""
    interpreter: str = "python3"  # python3, bash, node, etc.
    path: str
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None


class ParameterConfig(BaseModel):
    """参数配置"""
    name: str
    type: str = "string"  # string, number, boolean, array, object
    required: bool = True
    description: Optional[str] = None
    default: Optional[Any] = None


class CommandConfig(BaseModel):
    """命令配置"""
    name: str
    description: str
    type: Literal["http", "script"]
    enabled: bool = True
    http: Optional[HttpCommandConfig] = None
    script: Optional[ScriptCommandConfig] = None
    parameters: List[ParameterConfig] = Field(default_factory=list)


class ApiKeyAuthConfig(BaseModel):
    """API Key 鉴权配置"""
    location: Literal["header", "query", "body"] = "header"
    name: str = "api_key"
    value: str


class BearerTokenAuthConfig(BaseModel):
    """Bearer Token 鉴权配置"""
    token: str


class BasicAuthConfig(BaseModel):
    """Basic Auth 鉴权配置"""
    username: str
    password: str


class OAuth2AuthConfig(BaseModel):
    """OAuth2 鉴权配置"""
    client_id: str
    client_secret: str
    token_url: str
    scope: Optional[str] = None


class CustomHeaderAuthConfig(BaseModel):
    """自定义 Header 鉴权配置"""
    headers: Dict[str, str]


class AuthConfig(BaseModel):
    """鉴权配置"""
    name: str
    type: Literal["api_key", "bearer_token", "basic_auth", "oauth2", "custom_header"]
    api_key: Optional[ApiKeyAuthConfig] = None
    bearer_token: Optional[BearerTokenAuthConfig] = None
    basic_auth: Optional[BasicAuthConfig] = None
    oauth2: Optional[OAuth2AuthConfig] = None
    custom_header: Optional[CustomHeaderAuthConfig] = None


class McpServerConnectionConfig(BaseModel):
    """MCP 服务连接配置"""
    type: Literal["stdio", "sse", "websocket"] = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = Field(default_factory=list)
    url: Optional[str] = None  # 用于 sse 和 websocket


class McpServerConfig(BaseModel):
    """MCP 服务配置"""
    name: str
    description: str
    enabled: bool = True
    connection: McpServerConnectionConfig
    prefix: Optional[str] = None
    timeout: int = 30
    retry_on_failure: bool = True
    auto_reconnect: bool = True


class ToolProxyConfig(BaseModel):
    """工具代理配置"""
    enable_search: bool = True
    enable_execute: bool = True
    enable_list_services: bool = True
    search_limit: int = 20


class GlobalConfig(BaseModel):
    """全局配置"""
    default_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    log_level: str = "INFO"
    log_file: Optional[str] = None
    hot_reload: bool = True
    hot_reload_interval: int = 2
    tool_proxy_mode: bool = False  # 启用工具代理模式
    tool_proxy: ToolProxyConfig = Field(default_factory=ToolProxyConfig)


class Config(BaseModel):
    """完整配置"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    commands: List[CommandConfig] = Field(default_factory=list)
    mcp_servers: List[McpServerConfig] = Field(default_factory=list)
    auth_configs: List[AuthConfig] = Field(default_factory=list)
    global_config: GlobalConfig = Field(default_factory=GlobalConfig, alias="global")

    class Config:
        populate_by_name = True

    def resolve_env_vars(self) -> None:
        """解析环境变量"""
        # 解析 auth_configs 中的环境变量
        for auth in self.auth_configs:
            if auth.api_key:
                auth.api_key.value = self._resolve_env(auth.api_key.value)
            if auth.bearer_token:
                auth.bearer_token.token = self._resolve_env(auth.bearer_token.token)
            if auth.basic_auth:
                auth.basic_auth.username = self._resolve_env(auth.basic_auth.username)
                auth.basic_auth.password = self._resolve_env(auth.basic_auth.password)
            if auth.oauth2:
                auth.oauth2.client_id = self._resolve_env(auth.oauth2.client_id)
                auth.oauth2.client_secret = self._resolve_env(auth.oauth2.client_secret)
            if auth.custom_header:
                for key, value in auth.custom_header.headers.items():
                    auth.custom_header.headers[key] = self._resolve_env(value)

        # 解析命令配置中的环境变量
        for cmd in self.commands:
            if cmd.script and cmd.script.env:
                for key, value in cmd.script.env.items():
                    cmd.script.env[key] = self._resolve_env(value)

    @staticmethod
    def _resolve_env(value: str) -> str:
        """解析环境变量，支持 ${VAR} 格式"""
        if not isinstance(value, str):
            return value
        
        import re
        pattern = r'\$\{([^}]+)\}'
        
        def replace(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        
        return re.sub(pattern, replace, value)

