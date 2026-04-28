// 显示保存配置对话框
function showSaveConfigModal() {
    const modal = new bootstrap.Modal(document.getElementById('saveConfigModal'));
    modal.show();
}

// 获取表单数据（用于保存配置）
function getFormData() {
    const config = collectFormData();

    // 同步共享配置选项: 将webhook的include_*选项同步到email和wecom
    Object.keys(config.webhook || {}).forEach(key => {
        if (key.startsWith('include_')) {
            if (config.email) config.email[key] = config.webhook[key];
            if (config.wecom) config.wecom[key] = config.webhook[key];
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
            // 移除旧克隆卡片
            document.querySelectorAll('[data-instance]').forEach(el => el.remove());

            // 分离基础字段和额外实例字段
            const instanceSuffixes = new Set();
            const allSections = ['monitor', 'webhook', 'generic_webhook', 'wecom', 'email'];
            allSections.forEach(sec => {
                if (!config[sec]) return;
                Object.keys(config[sec]).forEach(k => {
                    const m = k.match(/__(\d+)$/);
                    if (m) instanceSuffixes.add(m[0]);
                });
            });

            // 为额外实例创建克隆卡片
            const suffixToType = {};
            if (config.monitor) {
                instanceSuffixes.forEach(suffix => {
                    const types = ['file_check', 'log_check', 'gpu_check', 'directory_check', 'http_check', 'api_trigger'];
                    types.forEach(t => {
                        const probe = t === 'gpu_check' ? 'check_gpu_power_enabled' : t === 'api_trigger' ? 'check_api_enabled' : `check_${t.replace('_check','').replace('_trigger','')}_enabled`;
                        const enabledKey = probe.replace('check_file_check', 'check_file').replace('check_log_check', 'check_log')
                            .replace('check_directory_check', 'check_directory').replace('check_http_check', 'check_http');
                        if (config.monitor[enabledKey + suffix] !== undefined) {
                            addModuleCard(t);
                        }
                    });
                });
            }
            ['webhook', 'generic_webhook', 'wecom', 'email'].forEach(sec => {
                if (!config[sec]) return;
                instanceSuffixes.forEach(suffix => {
                    if (config[sec]['enabled' + suffix] !== undefined) {
                        addModuleCard(sec);
                    }
                });
            });

            // 填充所有字段值（包括 __N 后缀的克隆字段）
            _loadSectionFields(config, 'monitor', (key, value) => {
                const baseKey = _stripInstanceSuffix(key);
                if (baseKey === 'check_http_headers' && value && typeof value === 'object') return JSON.stringify(value);
                if (value === null) return 'None';
                return value;
            });
            _loadSectionFields(config, 'webhook');
            _loadSectionFields(config, 'generic_webhook', (key, value) => {
                const baseKey = _stripInstanceSuffix(key);
                if (baseKey === 'headers' && value && typeof value === 'object') return JSON.stringify(value, null, 2);
                return value;
            });
            _loadSectionFields(config, 'wecom');
            _loadSectionFields(config, 'email');

            toggleCustomTextArea('webhook');
            toggleCustomTextArea('wecom');
            toggleCustomTextArea('email');

            // 填充 tag rows
            _loadTagRows('logMarkerRows', config.monitor, 'check_log_markers');
            _loadTagRows('excludeKeywordRows', config.monitor, 'check_directory_exclude_keywords');
            _loadTagRows('httpKeywordRows', config.monitor, 'check_http_expected_keywords');
            _loadActionKeywordRows('actionKeywordRows', config.monitor, 'check_directory_action_keywords');

            // 克隆实例的 tag rows
            instanceSuffixes.forEach(suffix => {
                _loadTagRows('logMarkerRows' + suffix, config.monitor, 'check_log_markers' + suffix);
                _loadTagRows('excludeKeywordRows' + suffix, config.monitor, 'check_directory_exclude_keywords' + suffix);
                _loadTagRows('httpKeywordRows' + suffix, config.monitor, 'check_http_expected_keywords' + suffix);
                _loadActionKeywordRows('actionKeywordRows' + suffix, config.monitor, 'check_directory_action_keywords' + suffix);
            });

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

function _stripInstanceSuffix(s) {
    return s.replace(/__\d+$/, '');
}

function _loadSectionFields(config, section, transform) {
    if (!config[section]) return;
    Object.entries(config[section]).forEach(([key, value]) => {
        const input = document.querySelector(`[name="${section}.${key}"]`);
        if (!input) return;
        if (input.type === 'checkbox') {
            input.checked = !!value;
        } else {
            input.value = transform ? (transform(key, value) ?? '') : (value ?? '');
        }
    });
}

function _loadTagRows(containerId, data, dataKey) {
    const container = document.getElementById(containerId);
    if (!container || !data) return;
    container.innerHTML = '';
    const values = data[dataKey];
    if (Array.isArray(values)) {
        values.forEach(v => addTagRow(containerId, v));
    }
}

function _loadActionKeywordRows(containerId, data, dataKey) {
    const container = document.getElementById(containerId);
    if (!container || !data) return;
    container.innerHTML = '';
    const ak = data[dataKey];
    if (ak && typeof ak === 'object' && !Array.isArray(ak)) {
        Object.entries(ak).forEach(([action, keywords]) => {
            const fn = containerId === 'actionKeywordRows' ? addActionKeywordRow :
                (a, k) => {
                    const row = document.createElement('div');
                    row.className = 'input-group input-group-sm mb-1 tag-input-row';
                    row.innerHTML = `
                        <input type="text" class="form-control" placeholder="建议内容" value="${escapeHtml(a)}" style="max-width:35%;">
                        <input type="text" class="form-control" placeholder="关键词（逗号分隔）" value="${escapeHtml(k)}">
                        <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">
                            <i class="bi bi-x-lg"></i>
                        </button>`;
                    container.appendChild(row);
                };
            const kwStr = Array.isArray(keywords) ? keywords.join(', ') : keywords;
            if (containerId === 'actionKeywordRows') {
                addActionKeywordRow(action, kwStr);
            } else {
                fn(action, kwStr);
            }
        });
    }
}

function collectFormData() {
    const config = {
        monitor: {},
        webhook: {},
        generic_webhook: {},
        wecom: {},
        email: {}
    };

    document.querySelectorAll('input, select, textarea').forEach(input => {
        if (!input.name) return;

        const nameParts = input.name.split('.');
        if (nameParts.length !== 2) return;
        const [sectionRaw, field] = nameParts;
        const section = _stripInstanceSuffix(sectionRaw);
        const baseField = _stripInstanceSuffix(field);
        let value = input.type === 'checkbox' ? input.checked : input.value;

        if (section === 'monitor') {
            if (baseField === 'check_log_markers' || baseField === 'check_directory_exclude_keywords' || baseField === 'check_directory_action_keywords_text') {
                return;
            } else if (baseField.includes('enabled') || baseField.includes('detect_') || baseField === 'check_directory_include_folders' || baseField === 'check_directory_continuous_mode' || baseField === 'double_check') {
                value = input.checked;
            } else if (baseField.includes('threshold')) {
                value = parseFloat(value);
            } else if (baseField === 'check_gpu_power_consecutive_checks') {
                const num = parseInt(value);
                value = isNaN(num) ? null : num;
            } else if (baseField === 'check_http_expected_status' || baseField === 'check_http_timeout' || baseField === 'check_api_port') {
                value = parseInt(value) || 0;
            } else if (baseField === 'check_http_headers') {
                try { value = JSON.parse(value || '{}'); } catch (e) { value = {}; }
            } else if (baseField.includes('interval') || baseField === 'logprint' || baseField.includes('delay') || baseField === 'timeout') {
                value = value.trim() || null;
            } else if (baseField === 'check_log_mode') {
                value = input.value;
            }
        } else if (section === 'webhook') {
            if (baseField === 'enabled' || baseField === 'custom_text_enabled' || (baseField.startsWith('include_') && !baseField.endsWith('_title'))) {
                value = input.checked;
            }
        } else if (section === 'generic_webhook') {
            if (baseField === 'enabled') {
                value = input.checked;
            } else if (baseField === 'retry_count' || baseField === 'timeout') {
                value = parseInt(value) || 0;
            } else if (baseField === 'headers') {
                try { value = JSON.parse(value || '{}'); } catch (e) { value = { "Content-Type": "application/json" }; }
            } else if (baseField === 'builtin_template') {
                value = value || null;
            }
        } else if (section === 'wecom') {
            if (baseField === 'enabled' || baseField === 'custom_text_enabled') {
                value = input.checked;
            }
        } else if (section === 'email') {
            if (baseField === 'enabled' || baseField === 'use_ssl' || baseField === 'custom_text_enabled') {
                value = input.checked;
            } else if (baseField === 'smtp_port') {
                value = parseInt(value) || 465;
            }
        }

        if (!config[section]) config[section] = {};
        config[section][field] = value;
    });

    config.monitor['check_log_markers'] = collectTagRows('logMarkerRows');
    config.monitor['check_directory_exclude_keywords'] = collectTagRows('excludeKeywordRows');
    config.monitor['check_directory_action_keywords'] = collectActionKeywordRows();
    config.monitor['check_http_expected_keywords'] = collectTagRows('httpKeywordRows');

    // tag rows from cloned instances
    document.querySelectorAll('[id^="logMarkerRows__"]').forEach(c => {
        config.monitor['check_log_markers' + c.id.replace('logMarkerRows', '')] = collectTagRows(c.id);
    });
    document.querySelectorAll('[id^="excludeKeywordRows__"]').forEach(c => {
        config.monitor['check_directory_exclude_keywords' + c.id.replace('excludeKeywordRows', '')] = collectTagRows(c.id);
    });
    document.querySelectorAll('[id^="httpKeywordRows__"]').forEach(c => {
        config.monitor['check_http_expected_keywords' + c.id.replace('httpKeywordRows', '')] = collectTagRows(c.id);
    });
    document.querySelectorAll('[id^="actionKeywordRows__"]').forEach(c => {
        const suffix = c.id.replace('actionKeywordRows', '');
        const result = {};
        c.querySelectorAll('.tag-input-row').forEach(row => {
            const inputs = row.querySelectorAll('input[type="text"]');
            const action = inputs[0].value.trim();
            const kw = inputs[1].value.trim();
            if (action && kw) result[action] = kw.split(/[,，]/).map(k => k.trim()).filter(k => k);
        });
        config.monitor['check_directory_action_keywords' + suffix] = result;
    });

    return config;
}

function toggleCustomTextArea(channel) {
    const checkbox = document.getElementById(channel + '_custom_text_switch');
    const area = document.getElementById(channel + '_custom_text_area');
    if (checkbox && area) {
        area.style.display = checkbox.checked ? 'block' : 'none';
    }
}

// === 模块卡片管理（支持多实例） ===

let _moduleInstanceCounter = 0;

function addModuleCard(moduleType) {
    const allCards = document.querySelectorAll(`[data-module-type="${moduleType}"]`);
    const templateCard = allCards[0];
    if (!templateCard) return;

    if (templateCard.style.display === 'none') {
        templateCard.style.display = '';
        const sw = templateCard.querySelector('.form-check-input');
        if (sw) sw.checked = true;
        return;
    }

    _moduleInstanceCounter++;
    const suffix = '__' + _moduleInstanceCounter;
    const clone = templateCard.cloneNode(true);

    clone.id = templateCard.id + suffix;
    clone.setAttribute('data-instance', _moduleInstanceCounter);
    clone.removeAttribute('style');

    clone.querySelectorAll('[id]').forEach(el => {
        el.id = el.id + suffix;
    });
    clone.querySelectorAll('[for]').forEach(label => {
        label.setAttribute('for', label.getAttribute('for') + suffix);
    });
    clone.querySelectorAll('[name]').forEach(input => {
        input.setAttribute('name', input.getAttribute('name') + suffix);
    });

    clone.querySelectorAll('input[type="text"], input[type="number"], input[type="password"], input[type="url"]').forEach(input => {
        input.value = '';
    });
    clone.querySelectorAll('textarea').forEach(ta => { ta.value = ''; });
    clone.querySelectorAll('select').forEach(sel => { sel.selectedIndex = 0; });
    clone.querySelectorAll('.tag-input-row').forEach(row => row.remove());

    const sw = clone.querySelector('.form-check-input');
    if (sw) sw.checked = true;

    const removeBtn = clone.querySelector('.module-remove-btn');
    if (removeBtn) {
        removeBtn.setAttribute('onclick', 'removeModuleCard(this)');
    }

    const lastCard = allCards[allCards.length - 1];
    lastCard.after(clone);
}

function removeModuleCard(btnEl) {
    const card = btnEl.closest('[data-module-type]');
    if (!card) return;
    const moduleType = card.getAttribute('data-module-type');
    const isClone = card.hasAttribute('data-instance');

    if (isClone) {
        card.remove();
    } else {
        card.style.display = 'none';
        const sw = card.querySelector('.form-check-input');
        if (sw) sw.checked = false;
    }
}

function initModuleVisibility() {
    document.querySelectorAll('[data-module-type]').forEach(card => {
        if (card.hasAttribute('data-instance')) return;
        const sw = card.querySelector('.form-check-input');
        if (card && sw) {
            card.style.display = sw.checked ? '' : 'none';
        }
    });
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