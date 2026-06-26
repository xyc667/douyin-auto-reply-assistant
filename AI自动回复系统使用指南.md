# 🤖 AI自动回复系统 - 使用指南

## 📋 系统概述

这是一个智能化的抖音私信自动回复系统，具有以下特点：

### ✨ 核心功能

- ✅ **智能AI回复** - 基于大语言模型自动生成回复
- ✅ **知识库问答** - 支持预设常见问题答案
- ✅ **并发处理** - 支持多人同时发消息
- ✅ **人工延迟** - 模拟真实人工回复速度
- ✅ **黑名单管理** - 屏蔽不想回复的用户
- ✅ **完整日志** - 记录所有交互信息
- ✅ **错误重试** - 自动处理API调用失败

---

## 🚀 快速开始

### 1️⃣ 配置API密钥

编辑 `config_ai.env` 文件：

```env
ANTHROPIC_API_KEY=你的API_Key
```

你可以在 MiniMax API 平台获取API密钥：
- 访问 https://platform.minimaxi.com
- 注册并获取API Key

### 2️⃣ 测试系统

```bash
cd d:\下载\DouYin_Spider-master\DouYin_Spider-master
python ai_auto_reply.py
```

如果看到以下输出，说明配置成功：
```
🤖 AI自动回复系统初始化完成！
✅ 系统初始化完成！
```

### 3️⃣ 运行完整系统

```bash
python dy_apis/douyin_recv_ai.py
```

---

## ⚙️ 配置说明

### 基础配置 (config_ai.env)

```env
# API配置
ANTHROPIC_API_KEY=your_api_key_here

# 回复延迟（秒）
MIN_REPLY_DELAY=2    # 最小延迟
MAX_REPLY_DELAY=8    # 最大延迟

# 自动回复开关
AUTO_REPLY_ENABLED=true

# 知识库优先模式
KNOWLEDGE_FIRST=false

# 系统设置
MAX_CONCURRENT=10     # 最大并发数
MAX_RETRY=3          # 最大重试次数
```

### 知识库配置 (datas/knowledge_base.json)

编辑知识库文件，添加常见问题和答案：

```json
{
  "knowledge_base": [
    {
      "question": "你好",
      "answer": "你好呀！有什么可以帮你的吗？"
    },
    {
      "question": "价格",
      "answer": "您好，关于价格请联系我们获取详细报价~"
    }
  ]
}
```

---

## 💡 使用流程

### 方式一：单独运行AI系统

```bash
python ai_auto_reply.py
```

适合测试AI功能，查看日志输出

### 方式二：集成到私信接收系统

系统会自动将收到的私信发送给AI，然后将AI的回复发送出去

### 方式三：完全自动运行

修改 `dy_apis/douyin_recv_ai.py`，启用自动回复模式

---

## 🎯 功能详解

### 1. 智能AI回复

系统会调用AI模型，根据用户消息自动生成回复：

```python
# 系统提示词可以自定义
SYSTEM_PROMPT=你是一个智能客服助手，请用友好、专业的态度回复...
```

### 2. 知识库问答

如果启用知识库优先模式，系统会先在知识库中查找匹配的问题：

```env
KNOWLEDGE_FIRST=true
```

知识库匹配规则：
- 精确匹配：问题完全相同
- 模糊匹配：关键词重叠度超过70%
- 支持编辑 `datas/knowledge_base.json` 自定义知识

### 3. 并发处理

系统使用线程池处理并发请求：

```env
MAX_CONCURRENT=10  # 最大同时处理10个请求
```

### 4. 回复延迟

模拟人工回复，设置随机延迟：

```env
MIN_REPLY_DELAY=2   # 最少2秒
MAX_REPLY_DELAY=8   # 最多8秒
```

### 5. 黑名单管理

编辑 `datas/blacklist.txt`，每行一个用户ID：

```
105228751401
123456789
```

或在代码中动态管理：
```python
system.blacklist.add("user_id")   # 添加到黑名单
system.blacklist.remove("user_id")  # 从黑名单移除
```

### 6. 日志记录

所有交互都会被记录到 `datas/reply_log.txt`：

```json
{"time": "2026-05-23 12:00:00", "level": "INFO", "message": "收到消息", "user_id": "105228751401"}
{"time": "2026-05-23 12:00:05", "level": "INFO", "message": "AI回复成功", "user_id": "105228751401", "reply": "你好呀！"}
```

### 7. 错误重试

如果AI调用失败，系统会自动重试：

```env
MAX_RETRY=3        # 最多重试3次
RETRY_DELAY=5     # 每次重试间隔5秒
```

---

## 📊 日志查看

```bash
# 实时查看日志
tail -f datas/reply_log.txt

# 查看最近的日志
Get-Content datas/reply_log.txt -Tail 50
```

---

## 🔧 故障排查

### 问题1：API调用失败

```bash
# 检查API Key是否正确
cat config_ai.env | grep API_KEY

# 测试API连接
python -c "import requests; print(requests.get('https://api.minimaxi.com/anthropic').status_code)"
```

### 问题2：回复太慢

```env
# 降低延迟时间
MIN_REPLY_DELAY=1
MAX_REPLY_DELAY=3
```

### 问题3：知识库不生效

```env
# 启用知识库优先
KNOWLEDGE_FIRST=true
```

### 问题4：并发数太高

```env
# 降低并发数
MAX_CONCURRENT=5
```

---

## 🎨 自定义配置

### 修改系统提示词

```env
SYSTEM_PROMPT=你是一个专业的销售顾问，熟悉我们的所有产品，请用专业、热情的态度回复客户的问题。
```

### 添加更多知识

```json
{
  "knowledge_base": [
    {"question": "你好", "answer": "你好呀！有什么可以帮你的吗？"},
    {"question": "在吗", "answer": "在的，随时为您服务！"},
    {"question": "价格", "answer": "价格根据产品不同，请告诉我具体产品名称~"}
  ]
}
```

---

## 📞 技术支持

如果遇到问题，可以：

1. 查看日志文件 `datas/reply_log.txt`
2. 检查配置文件 `config_ai.env`
3. 确认API Key是否有效
4. 测试网络连接

---

## ⚠️ 注意事项

1. **API费用** - 使用AI服务会产生费用，请注意监控使用量
2. **回复质量** - AI回复可能不完全准确，建议根据实际情况调整
3. **黑名单** - 定期检查黑名单，避免误屏蔽重要客户
4. **日志清理** - 定期清理日志文件，避免占用过多空间

---

## 🚀 下一步

1. 获取API Key
2. 配置 `config_ai.env`
3. 测试系统
4. 根据需要调整知识库
5. 正式投入使用

祝使用愉快！🎉