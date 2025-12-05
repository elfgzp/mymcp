// 命令相关功能

async function loadCommands() {
    const listEl = document.getElementById('commands-list');
    listEl.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/commands');
        const data = await response.json();
        
        if (data.commands && data.commands.length > 0) {
            listEl.innerHTML = data.commands.map(cmd => {
                const sourceClass = cmd.source === 'mcp' ? 'source-mcp' : 'source-local';
                const sourceText = cmd.source === 'mcp' ? 'MCP 工具' : '本地命令';
                const serviceInfo = cmd.service ? `<div class="command-info-item"><strong>服务:</strong> ${escapeHtml(cmd.service)}</div>` : '';
                
                const paramsHtml = cmd.parameters && cmd.parameters.length > 0 
                    ? `<div class="parameters-list">
                        <strong>参数:</strong>
                        ${cmd.parameters.map(p => `
                            <div class="parameter-item">
                                <span class="parameter-name">${escapeHtml(p.name)}</span>
                                <span class="parameter-type">${escapeHtml(p.type)}</span>
                                ${p.required ? '<span class="parameter-required">必填</span>' : ''}
                                ${p.description ? `<div class="parameter-description">${escapeHtml(p.description)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>`
                    : '<div class="command-info-item"><em>无参数</em></div>';
                
                const deleteBtn = cmd.source === 'local' 
                    ? `<button class="delete-btn" onclick="deleteCommand('${escapeHtml(cmd.name)}')">删除</button>`
                    : '';
                return `
                    <div class="command-card">
                        <div class="command-header">
                            <div>
                                <span class="command-name">${escapeHtml(cmd.name)}</span>
                                <span class="command-source ${sourceClass}">${sourceText}</span>
                            </div>
                            ${deleteBtn ? `<div>${deleteBtn}</div>` : ''}
                        </div>
                        <div class="command-info">
                            <div class="command-info-item"><strong>描述:</strong> ${escapeHtml(cmd.description || '无')}</div>
                            <div class="command-info-item"><strong>类型:</strong> ${escapeHtml(cmd.type)}</div>
                            ${serviceInfo}
                            ${paramsHtml}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            listEl.innerHTML = '<div class="loading">没有配置命令</div>';
        }
    } catch (error) {
        listEl.innerHTML = `<div class="error-message">加载失败: ${escapeHtml(error.message)}</div>`;
    }
}

async function loadAuthConfigs() {
    try {
        const response = await fetch('/api/auth-configs');
        const data = await response.json();
        const select = document.getElementById('http_auth_ref');
        
        // 清空现有选项（保留"无"选项）
        select.innerHTML = '<option value="">无</option>';
        
        if (data.auth_configs && data.auth_configs.length > 0) {
            data.auth_configs.forEach(auth => {
                const option = document.createElement('option');
                option.value = auth.name;
                option.textContent = `${auth.name} (${auth.type})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载鉴权配置失败:', error);
    }
}

async function handleAddCommand(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const command = {
        name: formData.get('name'),
        description: formData.get('description') || '',
        type: formData.get('type'),
        enabled: formData.get('enabled') === 'on'
    };
    
    if (command.type === 'http') {
        const httpConfig = {
            method: formData.get('http_method') || 'GET',
            url: formData.get('http_url')
        };
        
        // 处理鉴权配置
        const authRef = formData.get('http_auth_ref');
        if (authRef) {
            httpConfig.auth = {
                ref: authRef
            };
        }
        
        // 处理自定义请求头
        const headersText = formData.get('http_headers');
        const headers = parseKeyValueText(headersText);
        if (headers) {
            httpConfig.headers = headers;
        }
        
        // 处理 URL 参数
        const paramsText = formData.get('http_params');
        const params = parseKeyValueText(paramsText);
        if (params) {
            httpConfig.params = params;
        }
        
        // 处理请求体
        const bodyText = formData.get('http_body');
        if (bodyText && bodyText.trim()) {
            try {
                // 尝试解析为 JSON
                httpConfig.body = JSON.parse(bodyText);
            } catch (e) {
                // 如果不是 JSON，作为字符串处理
                httpConfig.body = bodyText.trim();
            }
        }
        
        // 超时时间
        const timeout = formData.get('http_timeout');
        if (timeout) {
            httpConfig.timeout = parseInt(timeout);
        }
        
        // 响应格式
        const responseFormat = formData.get('http_response_format');
        if (responseFormat) {
            httpConfig.response_format = responseFormat;
        }
        
        command.http = httpConfig;
    } else if (command.type === 'script') {
        command.script = {
            interpreter: formData.get('script_interpreter') || 'python3',
            path: formData.get('script_path')
        };
    }
    
    command.parameters = [];
    
    try {
        const response = await fetch('/api/commands', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(command)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('命令添加成功');
            closeModal('addCommandModal');
            loadCommands();
        } else {
            alert('添加失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('添加失败: ' + error.message);
    }
}

async function deleteCommand(name) {
    if (!confirm(`确定要删除命令 "${name}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/commands/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('命令已删除');
            loadCommands();
        } else {
            alert('删除失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}



