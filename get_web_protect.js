// ============================================
// 获取抖音 web_protect 参数的浏览器脚本
// ============================================
// 
// 使用方法：
// 1. 打开 https://www.douyin.com
// 2. 确保已登录
// 3. 按 F12 打开开发者工具
// 4. 切换到 Console（控制台）标签
// 5. 复制此文件的全部内容
// 6. 粘贴到控制台并按 Enter
// 7. 查看输出结果
//
// ============================================

console.log('========================================');
console.log('🔍 开始查找 web_protect 相关参数...');
console.log('========================================');
console.log('');

// ============================================
// 方法 1: 检查 localStorage
// ============================================
console.log('📦 方法 1: 检查 localStorage');
console.log('----------------------------------------');
let foundInLocalStorage = false;
for (let i = 0; i < localStorage.length; i++) {
    let key = localStorage.key(i);
    let value = localStorage.getItem(key);
    if (value && (value.includes('ticket') || value.includes('ts_sign') || value.includes('client_cert') || value.includes('ec_privateKey'))) {
        console.log('✅ 找到可能的键:', key);
        console.log('值:', value);
        console.log('');
        foundInLocalStorage = true;
    }
}
if (!foundInLocalStorage) {
    console.log('❌ localStorage 中未找到相关参数');
}
console.log('');

// ============================================
// 方法 2: 检查 sessionStorage
// ============================================
console.log('📦 方法 2: 检查 sessionStorage');
console.log('----------------------------------------');
let foundInSessionStorage = false;
for (let i = 0; i < sessionStorage.length; i++) {
    let key = sessionStorage.key(i);
    let value = sessionStorage.getItem(key);
    if (value && (value.includes('ticket') || value.includes('ts_sign') || value.includes('client_cert') || value.includes('ec_privateKey'))) {
        console.log('✅ 找到可能的键:', key);
        console.log('值:', value);
        console.log('');
        foundInSessionStorage = true;
    }
}
if (!foundInSessionStorage) {
    console.log('❌ sessionStorage 中未找到相关参数');
}
console.log('');

// ============================================
// 方法 3: 检查 window 对象
// ============================================
console.log('🌐 方法 3: 检查 window 对象');
console.log('----------------------------------------');
let windowProps = ['web_protect', 'webProtect', 'webProtectParams', 'securityParams', 'encryptParams', '__SECURITY__', '__WEB_PROTECT__'];
let foundInWindow = false;
windowProps.forEach(prop => {
    if (window[prop]) {
        console.log('✅ 找到 window.' + prop + ':', window[prop]);
        foundInWindow = true;
    }
});
if (!foundInWindow) {
    console.log('❌ window 对象中未找到相关参数');
}
console.log('');

// ============================================
// 方法 4: 设置网络请求拦截器
// ============================================
console.log('📡 方法 4: 设置网络请求拦截器');
console.log('----------------------------------------');
console.log('正在拦截网络请求...');
console.log('请尝试：发送一条私信 或 刷新页面');
console.log('');

// 拦截 fetch 请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    
    return originalFetch.apply(this, args).then(response => {
        const clonedResponse = response.clone();
        
        clonedResponse.text().then(text => {
            if (text && (text.includes('ticket') || text.includes('ts_sign') || text.includes('client_cert') || text.includes('ec_privateKey'))) {
                console.log('🎉 找到包含目标参数的响应！');
                console.log('URL:', url);
                console.log('响应内容:', text);
                console.log('');
            }
        });
        
        return response;
    });
};

// 拦截 XMLHttpRequest
const originalXHROpen = XMLHttpRequest.prototype.open;
const originalXHRSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._url = url;
    return originalXHROpen.apply(this, [method, url, ...rest]);
};

XMLHttpRequest.prototype.send = function(...args) {
    this.addEventListener('load', function() {
        const response = this.responseText;
        if (response && (response.includes('ticket') || response.includes('ts_sign') || response.includes('client_cert') || response.includes('ec_privateKey'))) {
            console.log('🎉 找到包含目标参数的 XHR 响应！');
            console.log('URL:', this._url);
            console.log('响应内容:', response);
            console.log('');
        }
    });
    return originalXHRSend.apply(this, args);
};

console.log('✅ 拦截器已设置！');
console.log('');

// ============================================
// 总结
// ============================================
console.log('========================================');
console.log('📋 总结');
console.log('========================================');
if (foundInLocalStorage || foundInSessionStorage || foundInWindow) {
    console.log('✅ 已找到一些参数！');
    console.log('请复制上面的输出内容');
} else {
    console.log('⚠️  未在存储中找到参数');
    console.log('');
    console.log('💡 建议：');
    console.log('1. 尝试发送一条私信');
    console.log('2. 或刷新页面');
    console.log('3. 查看拦截器是否捕获到相关请求');
    console.log('');
    console.log('如果仍然找不到，可能需要：');
    console.log('- 查看 Network 标签中的请求');
    console.log('- 搜索关键词: ticket, ts_sign, client_cert');
}
console.log('========================================');
