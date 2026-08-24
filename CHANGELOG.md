# 更新日志

本文件记录 ShadowAgent 的主要版本变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [Unreleased]

### 新增

- **潜意识地图**：侧边栏实时展示意象对应、阴影、阿尼姆斯/阿尼玛、情结等荣格维度状态
- 每次分析师回复后自动更新地图；删除梦境或结束解析时同步重建
- **单条记忆删除**：梦境列表每条记录旁增加 🗑 按钮，带二次确认
- `CHANGELOG.md`、`README.md` 项目文档

### 变更

- 删除梦境后会重建潜意识地图，避免残留已删记忆的影响

---

## [0.3.0] - 2026-05-26

### 变更

- **对话体验**：用户发送消息后，文字立即显示，再在下方单独显示「分析师在思考…」，避免消息被 spinner 顶掉
- **档案输入框**：人生背景、近期压力、解析偏好等字段按内容自动计算高度，尽量一次显示全部文字
- **分析师 Prompt**：不再固定每条回复末尾抛 1–2 个编号问题；改为「留白」，把思考空间留给用户
- 禁止「1. 2.」列举式追问和「可继续探索的问题」模板

### 移除

- 「载入示例梦境」按钮
- 数据库中的测试梦境记录（如 `test`、前男友示例等）

---

## [0.2.0] - 2026-05-25

### 移除

- **梦境视觉复原**功能（`services/image.py`、生成梦境画面按钮）
- SiliconFlow FLUX 图像模型依赖（模型已停用，`Model disabled` 报错）
- `requests`、`IMAGE_MODEL` 等绘图相关配置

### 变更

- 分析师 Prompt 禁止输出绘图 prompt 与视觉化段落
- API Key 迁移至 `.env`，代码中零硬编码
- 新增 `.streamlit/config.toml`：`toolbarMode = "viewer"`，减少误触「清空缓存」确认框
- 新增 `run.ps1` / `stop.ps1` 启动与停止脚本

### 修复

- Ctrl+C 停止服务时 IDE 弹出缓存确认的问题（推荐用 `.\stop.ps1` 停止）

---

## [0.1.0] - 2026-05-25 — Phase 0

### 新增

- **Phase 0 完整架构**：从单文件 `main.py` 重构为模块化项目
- **多轮对话**：`st.chat_input` + 荣格分析师 persona（追问优先、延迟定论）
- **个人档案**：称呼、人生背景、近期压力、解析偏好，持久化至 SQLite
- **梦境历史**：侧边栏列表，可切换继续旧梦
- **跨梦关联**：最近 5 条梦的摘要注入每次 LLM 调用
- **分析师笔记**：「结束本次解析」生成 80–150 字摘要，供下次关联
- **本地存储**：SQLite 三表（`profile` / `dream_sessions` / `messages`）
- 环境变量配置：`.env` + `.env.example`

### 项目结构

```
app.py              # Streamlit 入口
config.py           # 配置与 .env 读取
prompts/analyst.py  # 荣格分析师 Prompt
services/llm.py     # 大模型调用
storage/            # SQLite 持久层
```

### 移除

- 原 `main.py` 单次输入 + 固定三段式报告流程

---

## [0.0.1] - 初始原型

### 新增

- `main.py` 单文件 Streamlit 应用「ShadowAgent - 潜意识沙盒」
- 基于荣格心理学 / 八维的梦境解析 Prompt
- 单次梦境输入 → 大模型解析 → FLUX 梦境图像生成
- SiliconFlow API（DeepSeek-V3 + FLUX.1-schnell）
