
# 获取 web_protect 参数完整指南

## 简介

为了使用私信发送功能，我们需要获取两个关键参数：
- `web_protect_str` - 包含加密通信所需的 ticket、ts_sign、client_cert
- `keys_str` - 包含 ec_privateKey 私钥

---

## 方法一：使用浏览器脚本获取（推荐）

### 步骤 1：打开抖音网页版

访问: https://www.douyin.com

确保你已登录！

### 步骤 2：打开开发者工具

按 `F12` 或 `Ctrl+Shift+I`（Windows）或 `Cmd+Opt+I`（Mac）打开开发者工具

### 步骤 3：切换到 Console（控制台）标签

### 步骤 4：复制并运行下面的脚本

```javascript
// ============================================
// 获取 web_protect 和 keys 参数的脚本
// ============================================

console.log('🔍 开始查找相关参数...');

// 尝试从 localStorage/sessionStorage 查找
console.log('📦 检查 localStorage:');
for (let i = 0; i &lt; localStorage.length; i++) {
    let key = localStorage.key(i);
    let value = localStorage.getItem(key);
    if (value &amp;&amp; (value.includes('ticket') || value.includes('ts_sign') || value.includes('client_cert') || value.includes('ec_privateKey'))) {
        console.log(`找到可能的键: ${key}`);
        console.log(value);
    }
}

console.log('📦 检查 sessionStorage:');
for (let i = 0; i &lt; sessionStorage.length; i++) {
    let key = sessionStorage.key(i);
    let value = sessionStorage.getItem(key);
    if (value &amp;&amp; (value.includes('ticket') || value.includes('ts_sign') || value.includes('client_cert') || value.includes('ec_privateKey'))) {
        console.log(`找到可能的键: ${key}`);
        console.log(value);
    }
}

// 尝试查找全局变量
console.log('🌐 检查 window 对象:');
let windowProps = ['web_protect', 'webProtect', 'webProtectParams', 'securityParams', 'encryptParams'];
windowProps.forEach(prop =&gt; {
    if (window[prop]) {
        console.log(`找到 window.${prop}:`, window[prop]);
    }
});

console.log('✅ 检查完成！');
console.log('');
console.log('💡 如果上面没有找到，请看方法二！');
```

---

## 方法二：通过网络请求获取（如果方法一失败）

### 步骤 1：打开开发者工具 → Network（网络）标签

### 步骤 2：刷新页面或进行一些互动（发送私信）

### 步骤 3：在 Network 中搜索相关请求

搜索以下关键词：
- `web_protect`
- `ticket`
- `ts_sign`
- `client_cert`
- `ec_privateKey`
- `security`
- `encrypt`

### 步骤 4：查看请求和响应

点击找到的请求，查看：
1. **请求参数（Query String Parameters）**
2. **响应内容（Response）**

---

## 方法三：使用专门的浏览器脚本拦截

如果上面的方法都不行，我们可以使用专门的拦截脚本：

### 在 Console 中运行这个脚本：

```javascript
// ============================================
// 拦截网络请求查找 web_protect
// ============================================

console.log('🔍 开始监听网络请求...');

// 保存原始的 fetch
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const url = args[0];
    console.log('📤 请求:', url);
    
    if (typeof args[1] === 'object' &amp;&amp; args[1].body) {
        console.log('📦 请求体:', args[1].body);
    }
    
    return originalFetch.apply(this, args).then(response =&gt; {
        // 克隆响应以便我们可以读取它
        const clonedResponse = response.clone();
        
        clonedResponse.text().then(text =&gt; {
            if (text.includes('ticket') || text.includes('ts_sign') || text.includes('client_cert') || text.includes('ec_privateKey')) {
                console.log('🎉 找到包含目标参数的响应！');
                console.log('URL:', url);
                console.log('响应内容:', text);
            }
        });
        
        return response;
    });
};

console.log('✅ 监听器已设置！现在请尝试：');
console.log('  1. 发送一条私信');
console.log('  2. 或刷新页面');
console.log('  3. 查看控制台输出');
```

运行后，在网页上进行一些互动，比如刷新页面或尝试发送消息，然后查看控制台输出！

---

## 方法四：查找特定的 API 端点

抖音可能会通过以下端点提供这些参数：

在 Network 中查找这些请求：
- `/webcast/im/fetch/` - 私信相关
- `/security/` - 安全相关
- `/encrypt/` - 加密相关

---

## 获取到参数后，如何配置？

一旦获取到：

### 1. web_protect_str 格式
它应该是一个 JSON 字符串（可能被双重编码），包含：
```json
{
  "data": "{\"ticket\":\"...\",\"ts_sign\":\"...\",\"client_cert\":\"...\"}"
}
```

### 2. keys_str 格式
```json
{
  "data": "{\"ec_privateKey\":\"...\"}"
}
```

### 3. 在代码中使用

修改 `.env` 文件，添加：
```env
# （可选，如果你获取到了这些）
WEB_PROTECT=你的web_protect_str
KEYS=你的keys_str
```

或者在运行时传入：
```python
from builder.auth import DouyinAuth

auth = DouyinAuth()
auth.perepare_auth(
    cookies_str, 
    web_protect_str,  # 从浏览器获取
    keys_str          # 从浏览器获取
)
```

---

## 🎯 临时方案：先用接收功能

如果获取 web_protect 参数太复杂，可以：

1. ✅ 使用**私信接收功能** - 这已经完美工作
2. ✅ 使用**数据爬取功能** - 这完全可用
3. 在浏览器中手动发送回复，程序接收

---

## 💡 提示

- web_protect 参数有时效性，可能需要定期更新
- 这些参数通常在页面加载或首次发送私信时获取
- 查看相关的 JavaScript 文件（在 Sources 标签中）

---

## 📞 如果需要帮助

如果按照上面的方法仍然无法获取，可以：
1. 查看项目 Issues
2. 联系项目作者
3. 先用接收功能！
