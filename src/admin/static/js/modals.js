// 模态框相关功能

async function showAddCommandModal() {
    document.getElementById('addCommandModal').style.display = 'block';
    // 加载鉴权配置列表
    await loadAuthConfigs();
}

function showAddServerModal() {
    document.getElementById('addServerModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    document.getElementById(modalId === 'addCommandModal' ? 'addCommandForm' : 'addServerForm').reset();
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// 切换命令类型配置
function toggleCommandType(type) {
    document.getElementById('httpConfig').style.display = type === 'http' ? 'block' : 'none';
    document.getElementById('scriptConfig').style.display = type === 'script' ? 'block' : 'none';
}

// 切换连接类型配置
function toggleConnectionType(type) {
    document.getElementById('stdioConfig').style.display = type === 'stdio' ? 'block' : 'none';
    document.getElementById('sseConfig').style.display = type === 'sse' ? 'block' : 'none';
    document.getElementById('websocketConfig').style.display = type === 'websocket' ? 'block' : 'none';
}



