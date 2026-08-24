# ShadowAgent · 潜意识沙盒

基于荣格心理学的个人化解梦对话工具。不是符号查表，而是会追问、会记住、会随时间建立心理档案的潜意识伙伴。

![Streamlit](https://img.shields.io/badge/Streamlit-1.57+-FF4B4B)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![License](https://img.shields.io/badge/License-Private-lightgrey)

---

## 亮点

### 像心理医生一样对话，而不是一次性报告

- **多轮追问**：信息不足时先倾听、再追问，不急于下结论
- **留白式解析**：不固定每条回复末尾抛两个问题，把思考空间留给你
- **荣格立场**：从情结、阴影、补偿机制理解梦，而非预言或符号词典

### 个人化记忆

- **潜意识档案**：人生背景、近期压力、解析偏好持久保存
- **梦境历史**：每条梦独立存档，可随时切换继续聊
- **跨梦关联**：新梦会自动参考最近 5 条历史与分析师笔记
- **单条删除**：每条记忆旁可单独删除，带二次确认

### 潜意识地图（实时更新）

侧边栏自动维护一张 evolving 的心理地图：

| 维度 | 说明 |
|------|------|
| 🌑 阴影 | 当前主题与状态变化（压抑 / 浮现 / 对峙 / 整合） |
| ⚡ 阿尼姆斯 / 阿尼玛 | 极性与关系动态（投射 / 整合 / 对抗等） |
| 🔮 意象对应 | 重复符号、个人意义、关联主题、强度 |
| 🧵 情结 | 名称、触发场景、活跃状态 |

每次对话后自动刷新；删除记忆或结束解析时同步重建。

### 隐私优先

- 数据默认存在本地 SQLite（`data/shadow.db`）
- API Key 放在 `.env`，不入 Git
- 无账号、无云端同步（单用户本地使用）

---

## 快速开始

### 1. 安装依赖

```powershell
cd dreamAnalysisAgent
pip install -r requirements.txt
```

### 2. 配置 API

复制模板并填入密钥：

```powershell
copy .env.example .env
```

编辑 `.env`：

```env
SILICONFLOW_API_KEY=你的密钥
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
CHAT_MODEL=deepseek-ai/DeepSeek-V3
```

### 3. 启动

```powershell
.\run.ps1
```

浏览器打开：**http://localhost:8501**

停止服务：

```powershell
.\stop.ps1
```

---

## 使用流程

1. **填写个人档案**（左侧）— 人生背景与近期压力，分析师会据此个性化对话
2. **输入梦境**（右侧聊天框）— 描述越具体越好
3. **多轮对话** — 回答追问，逐步深入
4. **结束本次解析** — 生成分析师笔记，更新潜意识地图
5. **查看地图与历史** — 左侧侧边栏浏览意象、阴影变化与过往梦境

---

## 项目结构

```
dreamAnalysisAgent/
├── app.py                 # Streamlit 入口：聊天、侧边栏、地图
├── config.py              # 环境变量与路径
├── prompts/
│   ├── analyst.py         # 荣格分析师 Prompt
│   └── psyche_map.py      # 潜意识地图提取 Prompt
├── services/
│   ├── llm.py             # 大模型调用
│   └── psyche_map.py      # 地图解析与更新
├── storage/
│   ├── database.py        # SQLite 建表与迁移
│   ├── models.py          # 数据结构
│   └── repository.py      # 档案 / 梦境 / 消息 CRUD
├── data/shadow.db         # 本地数据库（自动生成）
├── .streamlit/config.toml # Streamlit 配置
├── run.ps1 / stop.ps1     # 启动 / 停止脚本
├── CHANGELOG.md           # 更新日志
└── requirements.txt
```

---

## 技术栈

- **UI**：Streamlit
- **LLM**：OpenAI 兼容 API（默认 SiliconFlow + DeepSeek-V3）
- **存储**：SQLite（标准库）
- **配置**：`.env` 本地加载

---

## 边界说明

ShadowAgent 是**自我探索与反思工具**，不是临床诊断，不能替代心理咨询或医疗。若出现自伤、他伤等危机情况，请寻求专业帮助。

---

## 更新记录

详见 [CHANGELOG.md](./CHANGELOG.md)。
