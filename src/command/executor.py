"""命令执行器"""

import asyncio
import subprocess
import json
from typing import Dict, Any, Optional
import httpx

from ..config.models import CommandConfig, Config
from ..auth.manager import AuthManager


class CommandExecutor:
    """命令执行器"""

    def __init__(self, config: Config, auth_manager: AuthManager):
        self.config = config
        self.auth_manager = auth_manager

    async def execute(self, command: CommandConfig, arguments: Dict[str, Any]) -> Any:
        """执行命令"""
        if command.type == "http":
            return await self._execute_http(command, arguments)
        elif command.type == "script":
            return await self._execute_script(command, arguments)
        else:
            raise ValueError(f"未知的命令类型: {command.type}")

    async def _execute_http(self, command: CommandConfig, arguments: Dict[str, Any]) -> Any:
        """执行 HTTP 请求"""
        if not command.http:
            raise ValueError("HTTP 命令配置缺失")

        http_config = command.http
        
        # 准备 URL 和参数
        url = self._replace_variables(http_config.url, arguments)
        params = {}
        if http_config.params:
            # 处理参数，支持可选参数
            for k, v in http_config.params.items():
                # 先尝试从 arguments 获取值
                if k in arguments and arguments[k] is not None and arguments[k] != "":
                    params[k] = str(arguments[k])
                else:
                    # 尝试替换模板变量
                    replaced_value = self._replace_variables(v, arguments)
                    # 如果替换后的值不是原始模板（说明有变量被替换），或者有实际值
                    if replaced_value != v or (replaced_value and replaced_value != ""):
                        # 如果替换后仍然是占位符格式 {key}，说明变量未提供，跳过可选参数
                        if not (replaced_value.startswith("{") and replaced_value.endswith("}")):
                            params[k] = replaced_value
        
        # 准备请求头
        headers = http_config.headers.copy() if http_config.headers else {}
        
        # 准备请求体
        body = None
        if http_config.body:
            body = {k: self._replace_variables(str(v), arguments) for k, v in http_config.body.items()}
        
        # 应用鉴权
        if http_config.auth:
            auth_ref = http_config.auth.get("ref")
            self.auth_manager.apply_auth(auth_ref, headers, params, body)
        
        # 发送请求
        timeout = http_config.timeout or self.config.global_config.default_timeout
        async with httpx.AsyncClient(timeout=timeout) as client:
            if http_config.method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif http_config.method.upper() == "POST":
                response = await client.post(url, params=params, headers=headers, json=body)
            elif http_config.method.upper() == "PUT":
                response = await client.put(url, params=params, headers=headers, json=body)
            elif http_config.method.upper() == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                response = await client.request(
                    http_config.method.upper(), url, params=params, headers=headers, json=body
                )
            
            response.raise_for_status()
            
            # 解析响应
            if http_config.response_format == "json":
                return response.json()
            elif http_config.response_format == "text":
                return response.text
            else:
                return response.content

    async def _execute_script(self, command: CommandConfig, arguments: Dict[str, Any]) -> Any:
        """执行脚本"""
        if not command.script:
            raise ValueError("脚本命令配置缺失")

        script_config = command.script
        
        # 准备参数
        args = [script_config.interpreter, script_config.path]
        if script_config.args:
            args.extend([self._replace_variables(str(arg), arguments) for arg in script_config.args])
        
        # 准备环境变量
        env = {}
        if script_config.env:
            env = {k: self._replace_variables(v, arguments) for k, v in script_config.env.items()}
        
        # 执行脚本
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **env} if env else None
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"脚本执行失败: {stderr.decode()}")
        
        # 尝试解析 JSON，否则返回文本
        output = stdout.decode()
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    @staticmethod
    def _replace_variables(template: str, variables: Dict[str, Any]) -> str:
        """替换模板中的变量"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


# 修复导入
import os

