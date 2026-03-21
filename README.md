<div align="center">
  <h1>NanoData: AI4Science Data Assistant Agent</h1>
  <p><em>Automatically transform multi-source scientific data into AI-Ready data assets</em></p>
  <p>
    <a href="./README_zh.md">简体中文</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/based_on-NanoBot-orange" alt="Based on NanoBot">
  </p>
</div>

**NanoData** is built on top of [HKUDS/NanoBot](https://github.com/HKUDS/NanoBot), specializing in automated processing of multi-source scientific data. It completes the full pipeline of data acquisition, analysis, cleaning, format conversion, and multimodal export. Through integration with the [Easy Dataset](https://github.com/easy-dataset/easy-dataset) MCP server, it exports high-quality SFT fine-tuning datasets ready for use with [LLaMA Factory](https://github.com/hiyouga/LLaMA-Factory).

It also retains NanoBot's core capabilities: persistent memory, multi-platform connections, SubAgent parallel execution, Cron scheduled tasks, and the Skill system.

## Key Differences from NanoBot

| Dimension | NanoBot | NanoData |
|-----------|---------|----------|
| Positioning | General personal AI assistant | AI4Science data engineering agent |
| New Tools | — | `data_profile`, `python_exec`, `file_reader`, `image_generate` |
| New Skills | — | `data-cleaning`, `data-to-text`, `scientific-data-parser`, `sft-dataset`, `multimodal-augmentation` |
| MCP Server | External configuration only | Built-in Easy Dataset MCP Server (676 lines, 18 tools) |
| Agent Role | General assistant | Senior AI Data Engineer |

## Core Pipeline

```
Multi-source scientific data (CSV/Parquet/HDF5/NetCDF/FITS/CIF/PDB/...)
        │
        ▼
  ┌─────────────┐
  │ data_profile │  ← Auto-analyze schema, missing values, data types
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ data-cleaning│  ← Cleaning, type fixing, deduplication, standardization
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ data-to-text │  ← Structured data → Semantic Markdown document
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │ sft-dataset  │  ← Easy Dataset MCP → QA pair generation → Alpaca/ShareGPT export
  └──────┬──────┘
         ▼
  ┌──────────────────────┐
  │ multimodal-augmentation│  ← SubAgent parallel image generation → Multimodal dataset
  └──────────┬───────────┘
             ▼
    LLaMA Factory / Other training frameworks
```

## Installation

```bash
git clone https://github.com/oNya685/NanoData.git
cd nanobot
pip install -e .
```

## Quick Start

### 1. Initialize Configuration

```bash
nanodata onboard
```

### 2. Configure API Key (`~/.nanodata/config.json`)

```json
{
  "providers": {
    "openrouter": { "apiKey": "sk-or-v1-xxx" }
  },
  "agents": {
    "defaults": { "model": "openrouter/claude-opus-4-6" }
  }
}
```

### 3. Start Agent

```bash
nanodata agent
```

### 4. Example Conversation

```
> Help me analyze the data quality of experiments.csv
> Clean the data and export as Parquet
> Convert the cleaned data into an experiment report document
> Use Easy Dataset to generate SFT training data, export in Alpaca format
```

## New Tools Detail

### `data_profile` — Dataset Analysis

Automatically identifies CSV/Excel/Parquet/JSON/JSONL formats, outputs schema, missing value ratios, data type distributions, and sample data. Supports automatic multi-encoding detection (UTF-8, GBK, Latin1, etc.).

### `python_exec` — Sandboxed Python Execution

Executes Python scripts in isolated subprocesses for pandas/numpy data processing. Each call is completely isolated with configurable timeout (default 60s, max 300s). Returns full traceback on failure for Agent self-correction.

### `file_reader` — Multi-format File Reading

Supports reading text files by line range, automatically detects binary files and prompts for use of specialized libraries (h5py, netCDF4, etc.). Used for preliminary exploration of scientific data formats.

### `image_generate` — Image Generation

Calls OpenAI-compatible APIs to generate images, supports batch concurrent requests (configurable `max_parallel`), automatically saves to disk. Used for multimodal dataset augmentation.

## New Skills Detail

### `data-cleaning` — Data Cleaning SOP

Standardized data cleaning workflow: Profile → Diagnosis → Script Generation → Execution & Verification → Data Card Generation. Follows immutability principle (never overwrites original files), prefers Parquet output to preserve type information.

### `data-to-text` — Structured Data to Text

Converts tabular data into semantic natural language documents. Includes four phases: semantic inference, template design, script generation, and quality check. Outputs AI-Ready Markdown documents ready for RAG, knowledge bases, or SFT dataset generation.

### `scientific-data-parser` — Scientific Data Parsing

Handles specialized scientific formats: HDF5, NetCDF, FITS, CIF, PDB, etc. Follows zero-data-loss principle, automatically detects unparsed content and emits `[UNPARSED_WARNING]`, iteratively refines until complete extraction.

### `sft-dataset` — SFT Dataset Generation

Implements complete SFT dataset generation pipeline via built-in Easy Dataset MCP Server:
1. Create project → Configure model → Upload documents
2. Semantic chunking → Generate questions → Generate answers
3. Data cleaning → Quality evaluation → Export

Supports Alpaca, ShareGPT, and multilingual-thinking format exports. Includes Cron async polling orchestration template for automatic long-running task scheduling.

### `multimodal-augmentation` — Multimodal Data Augmentation

Based on SubAgent parallel architecture: dataset sharding → multiple SubAgents parallel image generation → merge output. Adds `image_description`, `image_prompt`, and `image_path` fields to each QA pair.

## Easy Dataset MCP Server

Built-in MCP Server (`nanodata/mcp_servers/easy_dataset_server.py`), providing 18 tools:

| Tool | Function |
|------|----------|
| `create_project` / `list_projects` / `delete_project` | Project management |
| `upload_file` / `list_files` / `delete_file` | File management |
| `split_text` / `list_chunks` | Semantic chunking |
| `generate_questions` / `list_questions` | Question generation |
| `generate_answer` / `generate_answers_batch` | Answer generation |
| `clean_data` | Data cleaning |
| `evaluate_datasets` | Quality evaluation |
| `list_datasets` / `export_dataset` | Dataset management & export |
| `configure_model` / `list_model_configs` | Model configuration |

Auto-injected on startup, no manual configuration needed. Supports automatic selection of available model configurations.

## Retained NanoBot Capabilities

- **Persistent Memory**: `memory/MEMORY.md` + `memory/HISTORY.md`
- **Multi-platform Support**: Telegram, Discord, WhatsApp, Feishu, Slack, Email, QQ, DingTalk, Mochat
- **SubAgent**: Background parallel task execution
- **Cron Scheduled Tasks**: Supports cron expressions and interval scheduling
- **Heartbeat**: Auto-wakes every 30 minutes to execute periodic tasks
- **Skill System**: Defined with Markdown + YAML frontmatter, dynamically loaded
- **Multi LLM Provider**: OpenRouter, Anthropic, OpenAI, DeepSeek, Gemini, vLLM, etc.
- **MCP Protocol**: Supports both Stdio and HTTP transport modes

## Project Structure

```
nanodata/
├── agent/
│   ├── loop.py              # Agent main loop (register new tools)
│   ├── context.py           # Prompt building (inject data engineering instructions)
│   ├── memory.py            # Persistent memory
│   ├── subagent.py          # SubAgent management (supports multimodal tasks)
│   └── tools/
│       ├── data_profile.py  # [NEW] Dataset analysis (235 lines)
│       ├── python_exec.py   # [NEW] Sandboxed Python execution (134 lines)
│       ├── file_reader.py   # [NEW] Multi-format file reading (123 lines)
│       ├── image_generate.py# [NEW] Image generation (239 lines)
│       ├── mcp.py           # MCP tool integration (enhanced type hints)
│       └── ...              # Original tools (shell, filesystem, web, spawn, cron)
├── skills/
│   ├── data-cleaning/       # [NEW] Data cleaning skill
│   ├── data-to-text/        # [NEW] Data-to-text skill
│   ├── scientific-data-parser/ # [NEW] Scientific data parsing skill
│   ├── sft-dataset/         # [NEW] SFT dataset generation skill
│   ├── multimodal-augmentation/ # [NEW] Multimodal augmentation skill
│   └── ...                  # Original skills (github, weather, tmux, summarize, clawhub)
├── mcp_servers/
│   └── easy_dataset_server.py # [NEW] Easy Dataset MCP Server (676 lines)
├── templates/
│   ├── AGENTS.md            # [REWRITTEN] Data engineering agent instructions
│   └── TOOLS.md             # [REWRITTEN] Tool usage documentation
├── config/
│   └── loader.py            # [MODIFIED] Auto-inject built-in MCP Server
├── channels/                # Multi-platform support (retained)
├── providers/               # LLM Provider (retained)
└── ...
```

## Code Statistics

Changes from NanoBot to NanoData:

- **New Code**: ~3,500 lines
- **New Tools**: 4 (`data_profile`, `python_exec`, `file_reader`, `image_generate`)
- **New Skills**: 5 (including script templates and reference docs)
- **New MCP Server**: 1 (18 tools, 676 lines)
- **Modified Files**: 114
- **Package Refactoring**: `nanobot.*` → `nanodata.*`

## Docker Deployment

```bash
docker build -t nanodata .
docker run -v ~/.nanodata:/root/.nanodata -p 18790:18790 nanodata gateway
```

## Acknowledgments

- [HKUDS/NanoBot](https://github.com/HKUDS/NanoBot) — Base framework
- [Easy Dataset](https://github.com/easy-dataset/easy-dataset) — SFT dataset generation
- [LiteLLM](https://github.com/BerriAI/litellm) — Multi-provider support
- [Model Context Protocol](https://modelcontextprotocol.io/) — Tool extension protocol

## License

MIT
