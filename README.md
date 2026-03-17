<div align="center">
  <h1>NanoData: AI4Science Data Assistant Agent</h1>
  <p><em>将多源科学数据自动转化为 AI-Ready 数据资产</em></p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/based_on-NanoBot-orange" alt="Based on NanoBot">
  </p>
</div>

**NanoData** 基于 [HKUDS/NanoBot](https://github.com/HKUDS/NanoBot) 开发，专注于多源科学数据的自动化处理。它能够完成数据获取、分析、清洗、格式转换和多模态导出的全流程，并通过集成 [Easy Dataset](https://github.com/easy-dataset/easy-dataset) MCP 服务器，导出可直接用于 [LLaMA Factory](https://github.com/hiyouga/LLaMA-Factory) 训练的高质量 SFT 微调数据集。

同时保留了 NanoBot 的持久化记忆、多通讯平台连接、SubAgent 并行执行、Cron 定时任务和 Skill 技能系统等核心能力。

## 与 NanoBot 的主要差异

| 维度 | NanoBot | NanoData |
|------|---------|----------|
| 定位 | 通用个人 AI 助手 | AI4Science 数据工程 Agent |
| 新增工具 | — | `data_profile`, `python_exec`, `file_reader`, `image_generate` |
| 新增技能 | — | `data-cleaning`, `data-to-text`, `scientific-data-parser`, `sft-dataset`, `multimodal-augmentation` |
| MCP 服务器 | 仅外部配置 | 内置 Easy Dataset MCP Server (676 行，18 个工具) |
| Agent 角色 | 通用助手 | Senior AI Data Engineer |

## 核心流程

```
多源科学数据 (CSV/Parquet/HDF5/NetCDF/FITS/CIF/PDB/...)
        │
        ▼
  ┌─────────────┐
  │ data_profile │  ← 自动分析 schema、缺失值、数据类型
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ data-cleaning│  ← 清洗、类型修复、去重、标准化
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ data-to-text │  ← 结构化数据 → 语义化 Markdown 文档
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ sft-dataset  │  ← Easy Dataset MCP → QA 对生成 → Alpaca/ShareGPT 导出
  └──────┬──────┘
         ▼
  ┌──────────────────────┐
  │ multimodal-augmentation│  ← SubAgent 并行生成图像 → 多模态数据集
  └──────────┬───────────┘
             ▼
    LLaMA Factory / 其他训练框架
```

## 安装

```bash
git clone <repo-url>
cd nanobot
pip install -e .
```

## 快速开始

### 1. 初始化配置

```bash
nanodata onboard
```

### 2. 配置 API Key (`~/.nanodata/config.json`)

```json
{
  "providers": {
    "openrouter": { "apiKey": "sk-or-v1-xxx" }
  },
  "agents": {
    "defaults": { "model": "anthropic/claude-opus-4-5" }
  }
}
```

### 3. 启动 Agent

```bash
nanodata agent
```

### 4. 示例对话

```
> 帮我分析 experiments.csv 的数据质量
> 清洗数据并导出为 Parquet
> 将清洗后的数据转换为实验报告文档
> 用 Easy Dataset 生成 SFT 训练数据，导出 Alpaca 格式
```

## 新增工具详解

### `data_profile` — 数据集分析

自动识别 CSV/Excel/Parquet/JSON/JSONL 格式，输出 schema、缺失值比例、数据类型分布、样本数据。支持多编码自动检测 (UTF-8, GBK, Latin1 等)。

### `python_exec` — 沙箱 Python 执行

在独立子进程中执行 Python 脚本，用于 pandas/numpy 数据处理。每次调用完全隔离，超时可配置 (默认 60s，最大 300s)。失败时返回完整 traceback 供 Agent 自我修正。

### `file_reader` — 多格式文件读取

支持按行范围读取文本文件，自动检测二进制文件并提示使用专用库 (h5py, netCDF4 等)。用于科学数据格式的初步探索。

### `image_generate` — 图像生成

调用 OpenAI 兼容 API 生成图像，支持批量并发请求 (`max_parallel`)，自动保存到磁盘。用于多模态数据集增强。

## 新增技能详解

### `data-cleaning` — 数据清洗 SOP

标准化数据清洗流程：Profile → 诊断 → 脚本生成 → 执行验证 → 生成 Data Card。遵循不可变原则（不覆盖原始文件），优先输出 Parquet 保留类型信息。

### `data-to-text` — 结构化数据转文本

将表格数据转换为语义化自然语言文档。包含语义推断、模板设计、脚本生成、质量检查四个阶段。输出 AI-Ready Markdown 文档，可直接用于 RAG、知识库或 SFT 数据集生成。

### `scientific-data-parser` — 科学数据解析

处理 HDF5、NetCDF、FITS、CIF、PDB 等专业科学格式。遵循零数据丢失原则，自动检测未解析内容并发出 `[UNPARSED_WARNING]`，迭代修正直到完全提取。

### `sft-dataset` — SFT 数据集生成

通过内置 Easy Dataset MCP Server 实现完整的 SFT 数据集生成流程：
1. 创建项目 → 配置模型 → 上传文档
2. 语义分块 → 生成问题 → 生成答案
3. 数据清洗 → 质量评估 → 导出

支持 Alpaca、ShareGPT、multilingual-thinking 格式导出。包含 Cron 异步轮询编排模板，支持长时间任务自动调度。

### `multimodal-augmentation` — 多模态数据增强

基于 SubAgent 并行架构：数据集分片 → 多 SubAgent 并发生成图像 → 合并输出。为每条 QA 对添加 `image_description`、`image_prompt`、`image_path` 字段。

## Easy Dataset MCP Server

内置 MCP Server (`nanodata/mcp_servers/easy_dataset_server.py`)，提供 18 个工具：

| 工具 | 功能 |
|------|------|
| `create_project` / `list_projects` / `delete_project` | 项目管理 |
| `upload_file` / `list_files` / `delete_file` | 文件管理 |
| `split_text` / `list_chunks` | 语义分块 |
| `generate_questions` / `list_questions` | 问题生成 |
| `generate_answer` / `generate_answers_batch` | 答案生成 |
| `clean_data` | 数据清洗 |
| `evaluate_datasets` | 质量评估 |
| `list_datasets` / `export_dataset` | 数据集管理与导出 |
| `configure_model` / `list_model_configs` | 模型配置 |

启动时自动注入，无需手动配置。支持自动选择可用模型配置。

## 保留的 NanoBot 能力

- **持久化记忆**: `memory/MEMORY.md` + `memory/HISTORY.md`
- **多通讯平台**: Telegram, Discord, WhatsApp, Feishu, Slack, Email, QQ, DingTalk, Mochat
- **SubAgent**: 后台并行任务执行
- **Cron 定时任务**: 支持 cron 表达式和间隔调度
- **Heartbeat**: 每 30 分钟自动唤醒执行周期任务
- **Skill 系统**: Markdown + YAML frontmatter 定义，动态加载
- **多 LLM Provider**: OpenRouter, Anthropic, OpenAI, DeepSeek, Gemini, vLLM 等
- **MCP 协议**: 支持 Stdio 和 HTTP 两种传输模式

## 项目结构

```
nanodata/
├── agent/
│   ├── loop.py              # Agent 主循环（注册新工具）
│   ├── context.py           # Prompt 构建（注入数据工程指令）
│   ├── memory.py            # 持久化记忆
│   ├── subagent.py          # SubAgent 管理（支持多模态任务）
│   └── tools/
│       ├── data_profile.py  # [新增] 数据集分析 (235 行)
│       ├── python_exec.py   # [新增] 沙箱 Python 执行 (134 行)
│       ├── file_reader.py   # [新增] 多格式文件读取 (123 行)
│       ├── image_generate.py# [新增] 图像生成 (239 行)
│       ├── mcp.py           # MCP 工具集成（增强类型提示）
│       └── ...              # 原有工具 (shell, filesystem, web, spawn, cron)
├── skills/
│   ├── data-cleaning/       # [新增] 数据清洗技能
│   ├── data-to-text/        # [新增] 数据转文本技能
│   ├── scientific-data-parser/ # [新增] 科学数据解析技能
│   ├── sft-dataset/         # [新增] SFT 数据集生成技能
│   ├── multimodal-augmentation/ # [新增] 多模态增强技能
│   └── ...                  # 原有技能 (github, weather, tmux, summarize, clawhub)
├── mcp_servers/
│   └── easy_dataset_server.py # [新增] Easy Dataset MCP Server (676 行)
├── templates/
│   ├── AGENTS.md            # [重写] 数据工程 Agent 指令
│   └── TOOLS.md             # [重写] 工具使用文档
├── config/
│   └── loader.py            # [修改] 自动注入内置 MCP Server
├── channels/                # 多通讯平台（保留）
├── providers/               # LLM Provider（保留）
└── ...
```

## 代码统计

从 NanoBot 到 NanoData 的变更：

- **新增代码**: ~3,500 行
- **新增工具**: 4 个 (`data_profile`, `python_exec`, `file_reader`, `image_generate`)
- **新增技能**: 5 个 (含脚本模板和参考文档)
- **新增 MCP Server**: 1 个 (18 个工具，676 行)
- **修改文件**: 114 个
- **包名重构**: `nanobot.*` → `nanodata.*`

## Docker 部署

```bash
docker build -t nanodata .
docker run -v ~/.nanodata:/root/.nanodata -p 18790:18790 nanodata gateway
```

## 致谢

- [HKUDS/NanoBot](https://github.com/HKUDS/NanoBot) — 基础框架
- [Easy Dataset](https://github.com/easy-dataset/easy-dataset) — SFT 数据集生成
- [LiteLLM](https://github.com/BerriAI/litellm) — 多 Provider 支持
- [Model Context Protocol](https://modelcontextprotocol.io/) — 工具扩展协议

## License

MIT
