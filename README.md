# 抖音自动回复助手

> 基于 [Douyin_Spider](https://github.com/cv-cat/Douyin_Spider) 二次开发，集成 **AI 大模型 + 知识库 + 真人风格** 的抖音私信自动回复桌面助手。

<div align="center">

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/nodejs-18%2B-green)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)]()

</div>

---

## ⚠️ 免责声明

> **本项目仅供学习与个人效率工具使用，请遵守抖音平台规则与相关法律法规。**
> 严禁用于：
> - 群发骚扰、营销引流、刷量等违规行为
> - 任何形式的欺诈、违法或侵犯他人权益的行为
> - 绕过平台安全机制从事不正当活动
>
> 使用本项目所产生的任何后果由使用者自行承担。

---

## ✨ 功能特性

### 🤖 AI 智能回复
- 支持 **Anthropic Claude** / **OpenAI** / 任何 OpenAI 兼容接口
- 真人风格系统提示词：语气词、口语化、表情符号、模拟打字停顿
- 随机延迟回复（默认 8–20 秒），更像真人

### 📚 知识库优先
- 内置 GUI 知识库管理界面（增删改查）
- 关键词模糊匹配，命中直接回复，不消耗 AI 额度
- 命中失败时可降级到 AI 回复（可选）

### 👥 多账号管理
- 账号管理 GUI（增删账号、切换活跃账号）
- 每个账号独立保存 Cookie / web_protect / 加密密钥
- 运行时支持热切换账号

### 🎨 桌面 GUI
- Tkinter 原生界面，Windows 免依赖
- 集成：知识库管理、账号管理、实时日志、运行控制
- 启动 / 停止 / 监控 一键操作

### 🔌 抖音协议层
- 复用上游 [Douyin_Spider](https://github.com/cv-cat/Douyin_Spider) 全部能力：
  - 私信 WebSocket 实时收发
  - 直播间弹幕监听
  - 评论、点赞、收藏等互动 API

---

## 📁 目录结构

```
.
├── 抖音私信助手_整合版.py      # ⭐ 主入口（GUI + 自动回复整合）
├── account_manager.py         # 多账号管理逻辑
├── account_gui.py             # 账号管理 GUI 窗口
├── ai_auto_reply.py           # AI 回复核心逻辑
├── auto_login.py              # 扫码登录辅助
├── dy_apis/                   # 抖音 API 封装
│   ├── login_api.py
│   ├── douyin_recv_msg.py
│   └── douyin_recv_ai.py
├── dy_live/                   # 直播间 WebSocket 服务
├── builder/                   # 请求构建（header / params / 签名）
├── static/                    # 抖音 JS / proto 定义
├── utils/                     # 工具函数
├── examples/                  # 示例文件（不包含真实数据）
│   └── knowledge_base.example.json
├── .env.example               # 抖音凭证配置模板
├── config_ai.env.example      # AI 配置模板
├── requirements.txt
└── package.json
```

---

## 🚀 快速开始

### 1. 环境要求

| 依赖 | 版本 |
|---|---|
| Python | 3.7+ |
| Node.js | 18+ |
| 操作系统 | Windows 10/11 |

### 2. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# Node 依赖（用于签名 / 加密）
npm install
```

### 3. 配置抖音凭证

```bash
# 复制模板
cp .env.example .env
cp config_ai.env.example config_ai.env
```

编辑 `.env`，填入三项抖音凭证：

| 字段 | 说明 | 获取方式 |
|---|---|---|
| `DY_COOKIES` | 抖音网页 Cookie | 浏览器登录 [douyin.com](https://www.douyin.com) → F12 → Network → 复制 Cookie |
| `WEB_PROTECT` | 私信签名参数 | 浏览器控制台执行 `get_web_protect.js` |
| `KEYS` | 私信加密密钥对 | 同上 |

> ⚠️ **重要**：请勿将 `.env` 提交到任何 Git 仓库。`.gitignore` 已默认忽略。

### 4. 配置 AI（可选，不配置也能用知识库回复）

编辑 `config_ai.env`，填入你的 API Key：

```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_BASE_URL=https://api.anthropic.com
AI_MODEL=claude-3-5-sonnet-latest
```

### 5. 初始化知识库（可选）

```bash
mkdir -p datas
cp examples/knowledge_base.example.json datas/knowledge_base.json
```

然后在 GUI 中编辑你自己的问答对。

### 6. 启动

```bash
# 一键启动 GUI 助手
python 抖音私信助手_整合版.py

# 或 Windows 用户双击
启动私信助手_整合版.bat
```

启动后界面包含：
- **主控面板**：启动 / 停止监听、查看实时日志
- **知识库管理**：增删改查问答对
- **账号管理**：多账号切换

---

## 🧠 回复逻辑

```
收到私信
   │
   ▼
是否在黑名单？── 是 ──▶ 忽略
   │
   ▼
知识库模糊匹配 ── 命中 ──▶ 直接返回知识库答案
   │                        │
   │ 未命中                 │
   ▼                        ▼
AI_FALLBACK?  ── true ──▶ 调用 AI（带真人风格 prompt + 随机延迟）
   │
  false
   │
   ▼
 静默忽略
```

所有回复自动加入随机延迟（`MIN_REPLY_DELAY` ~ `MAX_REPLY_DELAY` 秒），避免秒回被识别为机器人。

---

## 🛠️ 高级用法

### 自定义回复风格
编辑 `config_ai.env` 的 `SYSTEM_PROMPT`，例如：
- **客服风格**：规范、礼貌、详细
- **朋友风格**：随意、口语化、表情多
- **专家风格**：专业、简洁、术语

### 接入其他 AI 服务
`ai_auto_reply.py` 实现了 OpenAI 兼容协议，只需在 `config_ai.env` 设置：
```env
AI_PROVIDER=openai
OPENAI_BASE_URL=https://your-custom-endpoint.com/v1
OPENAI_API_KEY=xxx
AI_MODEL=your-model
```

### 黑名单
`datas/blacklist.txt` 每行一个用户 ID（抖音 sec_uid），将跳过自动回复。

### 日志清理
`datas/reply_log.txt` 自动保留 `LOG_KEEP_DAYS` 天。

---

## ❓ 常见问题

**Q: Cookie 失效怎么办？**
A: 重新登录 douyin.com，复制新 Cookie 替换 `.env` 中的 `DY_COOKIES`。

**Q: 私信发送失败 `'str' object cannot be interpreted as an integer`？**
A: 多半是 `web_protect` 或 `keys` 过期，重新从浏览器控制台获取。

**Q: 提示 WebSocket 断连？**
A: 正常现象，脚本会自动重连。可检查网络 / 抖音是否更新了协议。

**Q: 如何多账号？**
A: 通过「账号管理」窗口添加，每个账号需独立的 cookies / web_protect / keys。

---

## 🙏 致谢

本项目基于以下开源项目开发：

- [cv-cat/Douyin_Spider](https://github.com/cv-cat/Douyin_Spider) — 抖音协议层核心实现
- [Anthropic Claude](https://www.anthropic.com) — AI 回复能力
- [loguru](https://github.com/Delgan/loguru) — 日志库

---

## 📜 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

## ⭐ Star History

如果这个项目对你有帮助，欢迎点个 Star ⭐ 鼓励一下作者！

<div align="center">
<sub>用 ❤️ 制作</sub>
</div>