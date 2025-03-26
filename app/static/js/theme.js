// 主题切换功能
(function() {
    // 主题列表
    const themes = [
        { name: 'light', icon: 'sun', label: '亮色主题' },
        { name: 'dark', icon: 'moon', label: '暗色主题' },
        { name: 'green', icon: 'tree', label: '翠绿主题' },
        { name: 'blue', icon: 'water', label: '深蓝主题' }
    ];
    
    // 初始化主题
    function initTheme() {
        // 从本地存储获取主题，如果没有则使用默认主题
        const savedTheme = localStorage.getItem('tasknya-theme') || 'light';
        setTheme(savedTheme);
        
        // 创建主题选择器
        createThemeSelector();
    }
    
    // 设置主题
    function setTheme(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('tasknya-theme', themeName);
        
        // 更新导航栏中的主题按钮
        const themeBtns = document.querySelectorAll('.theme-btn');
        if (themeBtns.length > 0) {
            themeBtns.forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-theme') === themeName) {
                    btn.classList.add('active');
                }
            });
        }
    }
    
    // 创建主题选择器
    function createThemeSelector() {
        const themeSelector = document.createElement('div');
        themeSelector.className = 'theme-selector';
        
        themes.forEach(theme => {
            const themeBtn = document.createElement('div');
            themeBtn.className = `theme-btn theme-${theme.name}`;
            themeBtn.setAttribute('data-theme', theme.name);
            themeBtn.setAttribute('title', theme.label);
            themeBtn.onclick = () => setTheme(theme.name);
            
            // 如果是当前主题，添加active类
            if (localStorage.getItem('tasknya-theme') === theme.name) {
                themeBtn.classList.add('active');
            }
            
            themeSelector.appendChild(themeBtn);
        });
        
        document.body.appendChild(themeSelector);
    }
    
    // 当DOM加载完成后初始化主题
    document.addEventListener('DOMContentLoaded', initTheme);
})(); 