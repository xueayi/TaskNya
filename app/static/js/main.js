// 显示保存配置对话框
function showSaveConfigModal() {
    const modal = new bootstrap.Modal(document.getElementById('saveConfigModal'));
    modal.show();
}

// 获取表单数据
function getFormData() {
    const form = document.getElementById('configForm');
    const formData = new FormData(form);
    const config = {
        monitor: {},
        webhook: {}
    };

    // 处理表单数据
    formData.forEach((value, key) => {
        const [section, field] = key.split('.');
        if (section === 'monitor') {
            if (key === 'monitor.check_log_markers') {
                config.monitor[field] = value.split('\n').filter(line => line.trim());
            } else if (key === 'monitor.timeout') {
                config.monitor[field] = value === 'None' ? null : parseInt(value);
            } else if (key.includes('enabled')) {
                config.monitor[field] = value === 'on';
            } else if (key.includes('threshold')) {
                config.monitor[field] = parseFloat(value);
            } else if (key.includes('interval') || key.includes('checks') || field === 'logprint') {
                // 确保logprint也被转换为整数
                const num = parseInt(value);
                config.monitor[field] = isNaN(num) ? null : num;
            } else {
                config.monitor[field] = value;
            }
        } else if (section === 'webhook') {
            if (key.includes('enabled')) {
                config.webhook[field] = value === 'on';
            } else {
                config.webhook[field] = value;
            }
        }
    });

    return config;
}

// 保存配置（显示对话框）
function saveConfig() {
    showSaveConfigModal();
}

// 保存配置（带自定义名称）
async function saveConfigWithName() {
    const configName = document.getElementById('configName').value.trim();
    if (!configName) {
        alert('请输入配置名称');
        return;
    }

    // 获取配置数据
    const config = getFormData();

    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: configName,
                config: config
            })
        });

        const result = await response.json();
        if (result.status === 'success') {
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('saveConfigModal'));
            modal.hide();
            alert('配置已保存');
        } else {
            alert('保存失败：' + result.message);
        }
    } catch (error) {
        alert('保存失败：' + error.message);
    }
}

// 加载配置列表
async function loadConfigList() {
    try {
        const response = await fetch('/api/configs');
        const configs = await response.json();
        
        const configList = document.getElementById('configList');
        configList.innerHTML = '';
        
        configs.forEach(filename => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = filename;
            li.onclick = () => loadConfig(filename);
            configList.appendChild(li);
        });
        
        const modal = new bootstrap.Modal(document.getElementById('configListModal'));
        modal.show();
    } catch (error) {
        alert('加载配置列表失败：' + error.message);
    }
}

// 加载指定配置
async function loadConfig(filename) {
    try {
        const response = await fetch(`/api/config/load/${filename}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const config = result.config;
            
            // 更新表单值
            Object.entries(config.monitor).forEach(([key, value]) => {
                const input = document.querySelector(`[name="monitor.${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = value;
                    } else if (key === 'check_log_markers' && Array.isArray(value)) {
                        input.value = value.join('\n');
                    } else {
                        input.value = value === null ? 'None' : value;
                    }
                }
            });
            
            Object.entries(config.webhook).forEach(([key, value]) => {
                const input = document.querySelector(`[name="webhook.${key}"]`);
                if (input) {
                    if (input.type === 'checkbox') {
                        input.checked = value;
                    } else if (key.endsWith('_title')) {
                        // 处理标题字段
                        input.value = value || '';
                    } else {
                        input.value = value;
                    }
                }
            });
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('configListModal'));
            modal.hide();
            
            appendLog('配置已加载');
        } else {
            appendLog('加载配置失败：' + result.message);
        }
    } catch (error) {
        appendLog('加载配置失败：' + error);
    }
}

// WebSocket连接
let ws = null;

// 初始化WebSocket连接
function initWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'log') {
            appendLog(data.message);
        } else if (data.type === 'status') {
            updateMonitorStatus(data.data.status);
        }
    };
    
    ws.onclose = function() {
        console.log('WebSocket连接已关闭');
        setTimeout(initWebSocket, 3000); // 3秒后尝试重连
    };
    
    ws.onerror = function(err) {
        console.error('WebSocket错误:', err);
    };
}

// 添加日志到面板
function appendLog(message) {
    const logPanel = document.getElementById('logPanel');
    const logEntry = document.createElement('div');
    logEntry.textContent = message;
    logPanel.appendChild(logEntry);
    logPanel.scrollTop = logPanel.scrollHeight;
}

// 清空日志
function clearLogs() {
    const logPanel = document.getElementById('logPanel');
    logPanel.innerHTML = '';
}

// 更新监控状态
function updateMonitorStatus(status) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    // 获取当前状态
    const currentStatus = startBtn.disabled ? 'running' : 'stopped';
    
    // 只有状态发生变化时才更新
    if (status !== currentStatus) {
        if (status === 'running') {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            appendLog('监控程序已启动');
        } else if (status === 'stopped') {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            appendLog('监控程序已停止');
        }
    }
}

// 开始监控
async function startMonitor() {
    try {
        const response = await fetch('/api/monitor/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            updateMonitorStatus('running');
        } else {
            alert('启动失败：' + result.message);
        }
    } catch (error) {
        alert('启动失败：' + error.message);
    }
}

// 停止监控
async function stopMonitor() {
    try {
        const stopBtn = document.getElementById('stopBtn');
        const startBtn = document.getElementById('startBtn');
        
        // 显示停止中状态
        stopBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> 停止中...';
        appendLog('正在停止监控程序...');
        
        const response = await fetch('/api/monitor/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            updateMonitorStatus('stopped');
            stopBtn.innerHTML = '<i class="bi bi-stop-fill"></i> 停止检测';
        } else {
            appendLog('停止失败：' + result.message);
            stopBtn.innerHTML = '<i class="bi bi-stop-fill"></i> 停止检测';
            alert('停止失败：' + result.message);
        }
    } catch (error) {
        appendLog('停止失败：' + error);
        document.getElementById('stopBtn').innerHTML = '<i class="bi bi-stop-fill"></i> 停止检测';
        alert('停止失败：' + error);
    }
}

// 页面加载完成后初始化WebSocket
document.addEventListener('DOMContentLoaded', function() {
    initWebSocket();
});

function applyCurrentConfig() {
    // 获取按钮元素
    const applyBtn = document.getElementById('applyConfigBtn');
    // 禁用按钮并改变文本
    applyBtn.disabled = true;
    applyBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> 应用中...';
    
    // 获取所有配置输入
    const config = collectFormData();
    
    // 发送到后端
    fetch('/api/config/apply', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ config: config })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            appendLog('配置已应用');
            // 显示成功图标
            applyBtn.innerHTML = '<i class="bi bi-check-lg"></i> 已应用';
            setTimeout(() => {
                applyBtn.innerHTML = '应用当前配置';
                applyBtn.disabled = false;
            }, 2000);
        } else {
            appendLog('应用配置失败: ' + data.message);
            // 显示错误图标
            applyBtn.innerHTML = '<i class="bi bi-x-lg"></i> 应用失败';
            setTimeout(() => {
                applyBtn.innerHTML = '应用当前配置';
                applyBtn.disabled = false;
            }, 2000);
        }
    })
    .catch(error => {
        appendLog('应用配置失败: ' + error);
        // 显示错误图标
        applyBtn.innerHTML = '<i class="bi bi-x-lg"></i> 应用失败';
        setTimeout(() => {
            applyBtn.innerHTML = '应用当前配置';
            applyBtn.disabled = false;
        }, 2000);
    });
}

function collectFormData() {
    const config = {
        monitor: {},
        webhook: {}
    };
    
    // 收集所有input元素的值
    document.querySelectorAll('input, select, textarea').forEach(input => {
        if (!input.name) return;
        
        const [section, field] = input.name.split('.');
        let value = input.type === 'checkbox' ? input.checked : input.value;
        
        // 根据字段名和类型进行数据转换
        if (section === 'monitor') {
            if (field === 'check_log_markers' && input.tagName.toLowerCase() === 'textarea') {
                value = value.split('\n').filter(line => line.trim());
            } else if (field === 'timeout') {
                value = value === 'None' ? null : parseInt(value);
            } else if (field.includes('enabled')) {
                value = input.checked;
            } else if (field.includes('threshold')) {
                value = parseFloat(value);
            } else if (field.includes('interval') || field.includes('checks') || field === 'logprint') {
                const num = parseInt(value);
                value = isNaN(num) ? null : num;
            }
        } else if (section === 'webhook') {
            if (field.includes('enabled') || (field.startsWith('include_') && !field.endsWith('_title'))) {
                // 只有enabled和include_xxx（不包括_title结尾）的字段才转换为布尔值
                value = input.checked;
            }
            // 其他webhook字段（包括_title结尾的）保持原始值
        }

        // 设置值到配置对象
        if (section === 'monitor') {
            config.monitor[field] = value;
        } else if (section === 'webhook') {
            config.webhook[field] = value;
        }
    });
    
    return config;
} 