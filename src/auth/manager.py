"""鉴权管理器"""

from typing import Optional, Dict, Any
from ..config.models import AuthConfig, Config


class AuthManager:
    """鉴权管理器"""

    def __init__(self, config: Config):
        self.config = config
        self._auth_cache: Dict[str, AuthConfig] = {}
        self._build_cache()

    def _build_cache(self) -> None:
        """构建鉴权配置缓存"""
        self._auth_cache = {auth.name: auth for auth in self.config.auth_configs}

    def get_auth_config(self, name: str) -> Optional[AuthConfig]:
        """获取鉴权配置"""
        return self._auth_cache.get(name)

    def apply_auth(self, auth_ref: Optional[str], headers: Dict[str, str], 
                   params: Dict[str, str], body: Optional[Dict[str, Any]] = None) -> None:
        """应用鉴权到请求"""
        if not auth_ref:
            return

        auth_config = self.get_auth_config(auth_ref)
        if not auth_config:
            return

        if auth_config.type == "api_key" and auth_config.api_key:
            api_key = auth_config.api_key
            if api_key.location == "header":
                headers[api_key.name] = api_key.value
            elif api_key.location == "query":
                params[api_key.name] = api_key.value
            elif api_key.location == "body" and body is not None:
                body[api_key.name] = api_key.value

        elif auth_config.type == "bearer_token" and auth_config.bearer_token:
            headers["Authorization"] = f"Bearer {auth_config.bearer_token.token}"

        elif auth_config.type == "basic_auth" and auth_config.basic_auth:
            import base64
            credentials = f"{auth_config.basic_auth.username}:{auth_config.basic_auth.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        elif auth_config.type == "custom_header" and auth_config.custom_header:
            headers.update(auth_config.custom_header.headers)

        # OAuth2 需要先获取 token，这里简化处理
        # 实际实现中应该缓存 token 并处理刷新
        elif auth_config.type == "oauth2" and auth_config.oauth2:
            # TODO: 实现 OAuth2 token 获取
            pass

    def reload(self, config: Config) -> None:
        """重新加载配置"""
        self.config = config
        self._build_cache()

