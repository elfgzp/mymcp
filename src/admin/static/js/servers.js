// MCP 服务相关功能

async function loadServers() {
    const listEl = document.getElementById('servers-list');
    listEl.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/mcp-servers');
        const data = await response.json();
        
        if (data.servers && data.servers.length > 0) {
            listEl.innerHTML = data.servers.map(server => `
                <div class="server-card">
                    <div class="server-header">
                        <div>
                            <span class="server-name">${escapeHtml(server.name)}</span>
                            <span class="server-status status-${getStatusClass(server.connection_status)}">
                                ${getStatusText(server.connection_status)}
                            </span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <label class="toggle-switch">
                                <input type="checkbox" ${server.enabled ? 'checked' : ''} 
                                       onchange="toggleServer('${escapeHtml(server.name)}', this.checked)">
                                <span class="slider"></span>
                            </label>
                            <button class="delete-btn" onclick="deleteServer('${escapeHtml(server.name)}')">删除</button>
                        </div>
                    </div>
                    <div class="server-info">
                        <div class="server-info-item"><strong>描述:</strong> ${escapeHtml(server.description || '无')}</div>
                        <div class="server-info-item"><strong>前缀:</strong> ${escapeHtml(server.prefix || '无')}</div>
                        <div class="server-info-item"><strong>连接类型:</strong> ${escapeHtml(server.connection.type)}</div>
                        ${server.connection_error ? `<div class="error-message">错误: ${escapeHtml(server.connection_error)}</div>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            listEl.innerHTML = '<div class="loading">没有配置 MCP 服务</div>';
        }
    } catch (error) {
        listEl.innerHTML = `<div class="error-message">加载失败: ${error.message}</div>`;
    }
}

async function toggleServer(name, enabled) {
    try {
        const response = await fetch(`/api/mcp-servers/${encodeURIComponent(name)}/toggle`, {
            method: 'PATCH'
        });
        const data = await response.json();
        
        if (response.ok) {
            // 重新加载列表
            setTimeout(() => loadServers(), 500);
        } else {
            alert('操作失败: ' + (data.detail || '未知错误'));
            // 恢复开关状态
            loadServers();
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
        loadServers();
    }
}

async function deleteServer(name) {
    if (!confirm(`确定要删除 MCP 服务 "${name}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/mcp-servers/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('MCP 服务已删除');
            loadServers();
        } else {
            alert('删除失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

async function handleAddServer(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    const connectionType = formData.get('connection_type');
    const connection = {
        type: connectionType
    };
    
    if (connectionType === 'stdio') {
        connection.command = formData.get('stdio_command') || 'uvx';
        const argsText = formData.get('stdio_args');
        connection.args = argsText ? argsText.split('\n').filter(line => line.trim()) : [];
    } else if (connectionType === 'sse') {
        connection.url = formData.get('sse_url');
    } else if (connectionType === 'websocket') {
        connection.url = formData.get('websocket_url');
    }
    
    const server = {
        name: formData.get('name'),
        description: formData.get('description') || '',
        enabled: formData.get('enabled') === 'on',
        connection: connection,
        prefix: formData.get('prefix') || null,
        timeout: parseInt(formData.get('timeout') || '30'),
        retry_on_failure: true,
        auto_reconnect: true
    };
    
    try {
        const response = await fetch('/api/mcp-servers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(server)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('MCP 服务添加成功');
            closeModal('addServerModal');
            loadServers();
        } else {
            alert('添加失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('添加失败: ' + error.message);
    }
}


