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
        webhook: {},
        generic_webhook: {},
        wecom: {},
        email: {}
    };

    // 处理表单数据
    formData.forEach((value, key) => {
        const [section, field] = key.split('.');
        if (section === 'monitor') {
            if (key === 'monitor.check_log_markers' || key === 'monitor.check_directory_exclude_keywords' || key === 'monitor.check_directory_action_keywords_text') {
                return;
            } else if (key === 'monitor.timeout') {
                config.monitor[field] = (value === 'None' || value === '') ? null : value.trim();
            } else if (key.includes('enabled')) {
                config.monitor[field] = value === 'on';
            } else if (key.includes('threshold')) {
                config.monitor[field] = parseFloat(value);
            } else if (key === 'monitor.check_gpu_power_consecutive_checks') {
                const num = parseInt(value);
                config.monitor[field] = isNaN(num) ? null : num;
            } else if (field === 'check_http_expected_status' || field === 'check_http_timeout' || field === 'check_api_port') {
                config.monitor[field] = parseInt(value) || 0;
            } else if (field === 'check_http_headers') {
                try {
                    config.monitor[field] = JSON.parse(value || '{}');
                } catch (e) {
                    config.monitor[field] = {};
                }
            } else if (key.includes('interval') || field === 'logprint' || key.includes('delay')) {
                config.monitor[field] = value.trim() || null;
            } else if (key === 'monitor.check_log_mode') {
                config.monitor[field] = value;
            } else {
                config.monitor[field] = value;
            }
        } else if (section === 'webhook') {
            if (field === 'enabled' || field === 'custom_text_enabled') {
                config.webhook[field] = value === 'on';
            } else {
                config.webhook[field] = value;
            }
        } else if (section === 'generic_webhook') {
            if (field === 'enabled') {
                config.generic_webhook[field] = value === 'on';
            } else if (field === 'retry_count' || field === 'timeout') {
                config.generic_webhook[field] = parseInt(value) || 0;
            } else if (field === 'headers') {
                try {
                    config.generic_webhook[field] = JSON.parse(value || '{}');
                } catch (e) {
                    config.generic_webhook[field] = { "Content-Type": "application/json" };
                }
            } else {
                config.generic_webhook[field] = value;
            }
        } else if (section === 'wecom') {
            if (field === 'enabled' || field === 'custom_text_enabled') {
                config.wecom[field] = value === 'on';
            } else {
                config.wecom[field] = value;
            }
        } else if (section === 'email') {
            if (field === 'enabled' || field === 'use_ssl' || field === 'custom_text_enabled') {
                config.email[field] = value === 'on';
            } else if (field === 'smtp_port') {
                config.email[field] = parseInt(value) || 465;
            } else {
                config.email[field] = value;
            }
        }
    });

    config.monitor['check_log_markers'] = collectTagRows('logMarkerRows');
    config.monitor['check_directory_exclude_keywords'] = collectTagRows('excludeKeywordRows');
    config.monitor['check_directory_action_keywords'] = collectActionKeywordRows();
    config.monitor['check_http_expected_keywords'] = collectTagRows('httpKeywordRows');

    // 同步共享配置选项: 将webhook的include_*选项同步到email和wecom
    Object.keys(config.webhook).forEach(key => {
        if (key.startsWith('include_')) {
            config.email[key] = config.webhook[key];
            config.wecom[key] = config.webhook[key];
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
            li.className = 'list-group-item d-flex justify-content-between align-items-center';

            // 配置名称
            const nameSpan = document.createElement('span');
            nameSpan.textContent = filename;
            nameSpan.style.cursor = 'pointer';
            nameSpan.onclick = () => loadConfig(filename);
            li.appendChild(nameSpan);

            // 删除按钮 (不显示默认配置的删除按钮)
            if (filename !== 'default.yaml') {
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn btn-sm btn-outline-danger';
                deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteConfig(filename);
                };
                li.appendChild(deleteBtn);
            }

            configList.appendChild(li);
        });

        const modal = new bootstrap.Modal(document.getElementById('configListModal'));
        modal.show();
    } catch (error) {
        alert('加载配置列表失败：' + error.message);
    }
}

// 删除配置
async function deleteConfig(filename) {
    if (!confirm(`确定要删除配置 "${filename}" 吗？`)) {
        return;
    }

    try {
        const response = await fetch(`/api/config/delete/${filename}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.status === 'success') {
            appendLog(`配置 ${filename} 已删除`);
            // 刷新配置列表
            loadConfigList();
        } else {
            alert('删除失败：' + result.message);
        }
    } catch (error) {
        alert('删除失败：' + error.message);
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
                    } else if (key === 'check_http_headers' && value && typeof value === 'object') {
                        input.value = JSON.stringify(value);
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
                        input.value = value || '';
                    } else {
                        input.value = value;
                    }
                }
            });
            toggleCustomTextArea('webhook');

            if (config.generic_webhook) {
                Object.entries(config.generic_webhook).forEach(([key, value]) => {
                    const input = document.querySelector(`[name="generic_webhook.${key}"]`);
                    if (input) {
                        if (input.type === 'checkbox') {
                            input.checked = value;
                        } else if (key === 'headers') {
                            input.value = JSON.stringify(value, null, 2);
                        } else {
                            input.value = value || '';
                        }
                    }
                });
            }

            if (config.wecom) {
                Object.entries(config.wecom).forEach(([key, value]) => {
                    const input = document.querySelector(`[name="wecom.${key}"]`);
                    if (input) {
                        if (input.type === 'checkbox') {
                            input.checked = value;
                        } else {
                            input.value = value || '';
                        }
                    }
                });
                toggleCustomTextArea('wecom');
            }

            if (config.email) {
                Object.entries(config.email).forEach(([key, value]) => {
                    const input = document.querySelector(`[name="email.${key}"]`);
                    if (input) {
                        if (input.type === 'checkbox') {
                            input.checked = value;
                        } else {
                            input.value = value || '';
                        }
                    }
                });
                toggleCustomTextArea('email');
            }

            // 填充+号输入行
            const lr = document.getElementById('logMarkerRows');
            if (lr) {
                lr.innerHTML = '';
                if (Array.isArray(config.monitor.check_log_markers)) {
                    config.monitor.check_log_markers.forEach(v => addTagRow('logMarkerRows', v));
                }
            }
            const er = document.getElementById('excludeKeywordRows');
            if (er) {
                er.innerHTML = '';
                if (Array.isArray(config.monitor.check_directory_exclude_keywords)) {
                    config.monitor.check_directory_exclude_keywords.forEach(v => addTagRow('excludeKeywordRows', v));
                }
            }
            const ar = document.getElementById('actionKeywordRows');
            if (ar) {
                ar.innerHTML = '';
                const ak = config.monitor.check_directory_action_keywords;
                if (ak && typeof ak === 'object') {
                    Object.entries(ak).forEach(([action, keywords]) => {
                        addActionKeywordRow(action, Array.isArray(keywords) ? keywords.join(', ') : keywords);
                    });
                }
            }
            const hr = document.getElementById('httpKeywordRows');
            if (hr) {
                hr.innerHTML = '';
                if (Array.isArray(config.monitor.check_http_expected_keywords)) {
                    config.monitor.check_http_expected_keywords.forEach(v => addTagRow('httpKeywordRows', v));
                }
            }
            initModuleVisibility();
            if (typeof updateFeishuPreview === 'function') updateFeishuPreview();
            if (typeof updateWecomPreview === 'function') updateWecomPreview();

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

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === 'log') {
            appendLog(data.message);
        } else if (data.type === 'status') {
            updateMonitorStatus(data.data.status);
        }
    };

    ws.onclose = function () {
        console.log('WebSocket连接已关闭');
        setTimeout(initWebSocket, 3000); // 3秒后尝试重连
    };

    ws.onerror = function (err) {
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
document.addEventListener('DOMContentLoaded', function () {
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
        webhook: {},
        generic_webhook: {},
        wecom: {},
        email: {}
    };

    // 收集所有input元素的值
    document.querySelectorAll('input, select, textarea').forEach(input => {
        if (!input.name) return;

        const [section, field] = input.name.split('.');
        let value = input.type === 'checkbox' ? input.checked : input.value;

        // 根据字段名和类型进行数据转换
        if (section === 'monitor') {
            if (field === 'check_log_markers' || field === 'check_directory_exclude_keywords' || field === 'check_directory_action_keywords_text') {
                return;
            } else if (field.includes('enabled')) {
                value = input.checked;
            } else if (field.includes('threshold')) {
                value = parseFloat(value);
            } else if (field === 'check_gpu_power_consecutive_checks') {
                const num = parseInt(value);
                value = isNaN(num) ? null : num;
            } else if (field === 'check_http_expected_status' || field === 'check_http_timeout' || field === 'check_api_port') {
                value = parseInt(value) || 0;
            } else if (field === 'check_http_headers') {
                try {
                    value = JSON.parse(value || '{}');
                } catch (e) {
                    value = {};
                }
            } else if (field.includes('interval') || field === 'logprint' || field.includes('delay') || field === 'timeout') {
                // 时间字段保留原始字符串，后端支持 "1h30m" 等格式
                value = value.trim() || null;
            } else if (field === 'check_log_mode') {
                // 保持日志检测模式的字符串值
                value = input.value;
            }
        } else if (section === 'webhook') {
            if (field === 'enabled' || field === 'custom_text_enabled' || (field.startsWith('include_') && !field.endsWith('_title'))) {
                value = input.checked;
            }
        } else if (section === 'generic_webhook') {
            // 处理 generic_webhook 配置段
            if (field === 'enabled') {
                value = input.checked;
            } else if (field === 'retry_count' || field === 'timeout') {
                value = parseInt(value) || 0;
            } else if (field === 'headers') {
                // 尝试解析 JSON
                try {
                    value = JSON.parse(value || '{}');
                } catch (e) {
                    value = { "Content-Type": "application/json" };
                }
            } else if (field === 'builtin_template') {
                // 空字符串转换为 null
                value = value || null;
            }
        } else if (section === 'wecom') {
            if (field === 'enabled' || field === 'custom_text_enabled') {
                value = input.checked;
            }
        } else if (section === 'email') {
            if (field === 'enabled' || field === 'use_ssl' || field === 'custom_text_enabled') {
                value = input.checked;
            } else if (field === 'smtp_port') {
                value = parseInt(value) || 465;
            }
        }

        // 设置值到配置对象
        if (section === 'monitor') {
            config.monitor[field] = value;
        } else if (section === 'webhook') {
            config.webhook[field] = value;
        } else if (section === 'generic_webhook') {
            config.generic_webhook[field] = value;
        } else if (section === 'wecom') {
            config.wecom[field] = value;
        } else if (section === 'email') {
            config.email[field] = value;
        }
    });

    config.monitor['check_log_markers'] = collectTagRows('logMarkerRows');
    config.monitor['check_directory_exclude_keywords'] = collectTagRows('excludeKeywordRows');
    config.monitor['check_directory_action_keywords'] = collectActionKeywordRows();
    config.monitor['check_http_expected_keywords'] = collectTagRows('httpKeywordRows');

    return config;
}

function toggleCustomTextArea(channel) {
    const checkbox = document.getElementById(channel + '_custom_text_switch');
    const area = document.getElementById(channel + '_custom_text_area');
    if (checkbox && area) {
        area.style.display = checkbox.checked ? 'block' : 'none';
    }
}

// === 模块卡片显示/隐藏 ===

function showModuleCard(cardId, switchId) {
    const card = document.getElementById(cardId);
    if (card) {
        card.style.display = 'block';
        const switchEl = document.getElementById(switchId);
        if (switchEl) switchEl.checked = true;
    }
    updateDropdownMenus();
}

function removeModuleCard(cardId, switchId) {
    const card = document.getElementById(cardId);
    if (card) {
        card.style.display = 'none';
        const switchEl = document.getElementById(switchId);
        if (switchEl) switchEl.checked = false;
    }
    updateDropdownMenus();
}

function updateDropdownMenus() {
    // 更新检测方法下拉菜单
    const detectionCards = [
        {cardId: 'card_file_check', menuText: '单文件感知'},
        {cardId: 'card_log_check', menuText: '日志检查'},
        {cardId: 'card_gpu_check', menuText: 'GPU功耗检查'},
        {cardId: 'card_directory_check', menuText: '多文件感知'},
        {cardId: 'card_http_check', menuText: 'HTTP轮询检测'},
        {cardId: 'card_api_trigger', menuText: 'API被动触发'},
    ];
    const detDropdown = document.getElementById('detectionDropdown');
    if (detDropdown) {
        detDropdown.querySelectorAll('.dropdown-item').forEach((item, i) => {
            const card = document.getElementById(detectionCards[i].cardId);
            if (card) {
                item.style.display = card.style.display === 'none' ? '' : 'none';
            }
        });
    }

    // 更新通知渠道下拉菜单
    const notifCards = [
        {cardId: 'card_webhook', menuText: '飞书机器人'},
        {cardId: 'card_email', menuText: '邮件通知'},
        {cardId: 'card_wecom', menuText: '企业微信'},
        {cardId: 'card_generic_webhook', menuText: '通用 Webhook'},
    ];
    const notifDropdown = document.getElementById('notificationDropdown');
    if (notifDropdown) {
        notifDropdown.querySelectorAll('.dropdown-item').forEach((item, i) => {
            const card = document.getElementById(notifCards[i].cardId);
            if (card) {
                item.style.display = card.style.display === 'none' ? '' : 'none';
            }
        });
    }
}

function initModuleVisibility() {
    // 检测方法
    const detectionModules = [
        {cardId: 'card_file_check', switchId: 'file_check_switch'},
        {cardId: 'card_log_check', switchId: 'log_check_switch'},
        {cardId: 'card_gpu_check', switchId: 'gpu_check_switch'},
        {cardId: 'card_directory_check', switchId: 'directory_check_switch'},
        {cardId: 'card_http_check', switchId: 'check_http_enabled_switch'},
        {cardId: 'card_api_trigger', switchId: 'check_api_enabled_switch'},
    ];
    detectionModules.forEach(m => {
        const card = document.getElementById(m.cardId);
        const sw = document.getElementById(m.switchId);
        if (card && sw) {
            card.style.display = sw.checked ? 'block' : 'none';
        }
    });

    // 通知渠道
    const notifModules = [
        {cardId: 'card_webhook', switchId: 'webhook_switch'},
        {cardId: 'card_email', switchId: 'email_switch'},
        {cardId: 'card_wecom', switchId: 'wecom_switch'},
        {cardId: 'card_generic_webhook', switchId: 'generic_webhook_switch'},
    ];
    notifModules.forEach(m => {
        const card = document.getElementById(m.cardId);
        const sw = document.getElementById(m.switchId);
        if (card && sw) {
            card.style.display = sw.checked ? 'block' : 'none';
        }
    });

    updateDropdownMenus();
}

// === +号输入行管理 ===

function addTagRow(containerId, value) {
    value = value || '';
    const container = document.getElementById(containerId);
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'input-group input-group-sm mb-1 tag-input-row';
    row.innerHTML = `
        <input type="text" class="form-control" value="${escapeHtml(value)}">
        <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">
            <i class="bi bi-x-lg"></i>
        </button>
    `;
    container.appendChild(row);
}

function addActionKeywordRow(action, keywords) {
    action = action || '';
    keywords = keywords || '';
    const container = document.getElementById('actionKeywordRows');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'input-group input-group-sm mb-1 tag-input-row';
    row.innerHTML = `
        <input type="text" class="form-control" placeholder="建议内容" value="${escapeHtml(action)}" style="max-width:35%;">
        <input type="text" class="form-control" placeholder="关键词（逗号分隔）" value="${escapeHtml(keywords)}">
        <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">
            <i class="bi bi-x-lg"></i>
        </button>
    `;
    container.appendChild(row);
}

function collectTagRows(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    const values = [];
    container.querySelectorAll('.tag-input-row input[type="text"]').forEach(input => {
        const v = input.value.trim();
        if (v) values.push(v);
    });
    return values;
}

function collectActionKeywordRows() {
    const container = document.getElementById('actionKeywordRows');
    if (!container) return {};
    const result = {};
    container.querySelectorAll('.tag-input-row').forEach(row => {
        const inputs = row.querySelectorAll('input[type="text"]');
        const action = inputs[0].value.trim();
        const keywordsStr = inputs[1].value.trim();
        if (action && keywordsStr) {
            result[action] = keywordsStr.split(/[,，]/).map(k => k.trim()).filter(k => k);
        }
    });
    return result;
}