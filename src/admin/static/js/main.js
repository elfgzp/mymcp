// 主逻辑

function showTab(tabName) {
    // 隐藏所有标签页内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 显示选中的标签页
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    if (tabName === 'servers') {
        loadServers();
    } else if (tabName === 'commands') {
        loadCommands();
    }
}

// 页面加载时自动加载服务列表
document.addEventListener('DOMContentLoaded', function() {
    loadServers();
    
    // 每 5 秒自动刷新一次服务列表
    setInterval(loadServers, 5000);
});


