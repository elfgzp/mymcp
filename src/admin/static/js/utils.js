// 工具函数

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getStatusClass(status) {
    if (!status || status === 'unknown') return 'unknown';
    if (status.startsWith('error:')) return 'error';
    return status;
}

function getStatusText(status) {
    if (!status || status === 'unknown') return '未知';
    if (status === 'connecting') return '连接中';
    if (status === 'connected') return '已连接';
    if (status === 'disconnected') return '已断开';
    if (status.startsWith('error:')) return '错误';
    return status;
}

// 解析键值对文本（每行一个，格式：key: value）
function parseKeyValueText(text) {
    if (!text || !text.trim()) return null;
    const result = {};
    const lines = text.split('\n');
    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        const colonIndex = trimmed.indexOf(':');
        if (colonIndex > 0) {
            const key = trimmed.substring(0, colonIndex).trim();
            const value = trimmed.substring(colonIndex + 1).trim();
            if (key) {
                result[key] = value;
            }
        }
    }
    return Object.keys(result).length > 0 ? result : null;
}






