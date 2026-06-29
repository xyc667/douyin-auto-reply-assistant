# 抖音私信自动回复助手（整合版）

> 基于 [Douyin_Spider](https://github.com/cv-cat/Douyin_Spider) 二次开发，集成 **知识库 + AI 大模型 + 真人风格延迟 + 多账号** 的 Windows 桌面助手。

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/nodejs-18%2B-green)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)]()

---

## 免责声明

本项目仅供学习与个人效率工具使用，请遵守抖音平台规则与相关法律法规。  
严禁用于群发骚扰、营销引流、刷量等违规行为。使用所产生的后果由使用者自行承担。

---

## 功能特性

- **整合版 GUI**：登录、启动/停止、知识库、账号管理、实时日志
- **知识库优先**：GUI 管理问答对，命中后直接回复，不消耗 AI 额度
- **AI 智能降级**：知识库未命中时可调用 MiniMax / Anthropic 兼容 / OpenAI 兼容接口
- **真人风格**：可配置随机延迟（默认 8–20 秒）与系统提示词
- **多账号**：每个账号独立 Cookie / WEB_PROTECT / KEYS，支持切换
- **自动登录**：Playwright 扫码登录并写入本地配置

---

## 目录结构

```
.
├── 抖音私信助手_整合版.py      # 主入口
├── 启动私信助手_整合版.bat
├── ai_auto_reply.py
├── account_manager.py / account_gui.py
├── auto_login.py / start_login.bat
├── get_web_protect.js / .html
├── builder/                   # 认证与签名
├── dy_apis/                   # 抖音 API
├── static/                    # Protobuf + JS 签名
├── utils/dy_util.py             # 工具
├── examples/                  # 知识库示例
├── .env.example               # 抖音凭证模板
├── config_ai.env.example      # AI 配置模板
├── pack_integrated.py         # 打包脚本
└── scan_secrets.py            # 敏感信息扫描
```

---

## 快速开始

### 1. 环境要求

| 依赖 | 版本 |
|------|------|
| Python | 3.7+ |
| Node.js | 18+ |
| 系统 | Windows 10/11 |

### 2. 安装依赖

```bash
pip install -r requirements.txt
npm install
playwright install chromium
```

### 3. 配置抖音凭证

```bash
copy .env.example .env
copy config_ai.env.example config_ai.env
```

编辑 `.env`：

| 字段 | 说明 |
|------|------|
| `DY_COOKIES` | 浏览器登录 [douyin.com](https://www.douyin.com) 后复制 Cookie |
| `WEB_PROTECT` | 浏览器控制台运行 `get_web_protect.js` 获取 |
| `KEYS` | 同上 |

### 4. 配置 AI（可选）

编辑 **`config_ai.env`**（与主程序同目录）：

```env
ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
ANTHROPIC_API_KEY=your-api-key-here
AI_MODEL=MiniMax-M2.7
KNOWLEDGE_FIRST=true
AI_FALLBACK=true
MIN_REPLY_DELAY=8
MAX_REPLY_DELAY=20
SYSTEM_PROMPT=你是一个真实的朋友在微信聊天...
```

也可在 `.env` 中设置 `MINIMAX_API_KEY` 作为备用。

### 5. 初始化知识库

```bash
mkdir datas
copy examples\knowledge_base.example.json datas\knowledge_base.json
```

或在 GUI 中点击 **「知识库」** 管理。

### 6. 启动

```bash
python 抖音私信助手_整合版.py
```

或双击 `启动私信助手_整合版.bat`。

---

## 回复逻辑

```
收到私信
  → 黑名单？ → 忽略
  → 知识库命中？ → 直接回复
  → AI_FALLBACK=true？ → 调用 AI
  → 否则静默忽略
```

回复前会随机延迟，模拟真人打字。

---

## 敏感文件说明（切勿提交 Git）

以下文件仅保存在本地，已在 `.gitignore` 中忽略：

| 文件 | 内容 |
|------|------|
| `.env` | 抖音 Cookie、WEB_PROTECT、KEYS |
| `config_ai.env` | AI API Key |
| `accounts.json` | 多账号数据（首次使用后自动生成） |
| `datas/reply_log.txt` | 运行日志 |

打包分发前可运行：

```bash
python pack_integrated.py
python scan_secrets.py
```

---

## 常见问题

**Cookie 失效？**  
重新登录或在 GUI 中使用「自动登录 / 账号管理 → 重新登录」。

**启动报 JSON 解析错误？**  
多为 `KEYS` 格式问题；请重新获取 WEB_PROTECT / KEYS，或使用最新版 `builder/auth.py`。

**AI 不回复？**  
检查 `config_ai.env` 中 `AI_FALLBACK=true` 且 API Key 有效；启动时日志会显示 AI 连接测试结果。

**私信发不出？**  
确认 `WEB_PROTECT` 和 `KEYS` 未过期；整合版会从消息体读取 `conversation_short_id` 用于发送。

---

## 致谢

- [cv-cat/Douyin_Spider](https://github.com/cv-cat/Douyin_Spider) — 抖音协议层
- [MiniMax](https://platform.minimaxi.com) — AI 接口

---

## 许可证

MIT License — 详见 [LICENSE](LICENSE)
