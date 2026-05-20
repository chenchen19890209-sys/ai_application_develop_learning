# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Overview

This is a **24-day AI LLM application development tutorial** (5 phases: Python → LLM → Agent → RAG → Capstone). The curriculum emphasizes **native SDK patterns** and **MCP protocol** over framework lock-in (no LangChain dependency).

## Architecture

```
ai_develop_learning_claude/
├── config.py                    # Shared config for all days
├── .env.example                 # Environment variable template
├── phase1_fundamentals/         # Phase 1: Python basics (5 days)
├── phase2_llm_core/             # Phase 2: LLM core capabilities (5 days)
├── phase3_agent/                # Phase 3: Agent deep dive (6 days)
├── phase4_rag/                  # Phase 4: RAG practice (5 days)
└── phase5_capstone/             # Phase 5: Capstone project (3 days)
```

## Common Commands

```bash
# Install per-day dependencies
cd phaseX_*/dayXX_*
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# Run a specific day's main code
python phase2_llm_core/day06_llm_basics/first_llm_call.py
```

## Per-day File Structure

Every `dayXX_*` directory must contain:
- `tutorial.md` — learning tutorial (objectives, concepts with analogies, exercises)
- `requirements.txt` — pinned Python dependencies
- Python code files — production-grade, every line commented in Chinese, single file ≤500 lines

For complex days, split into modules:
```
dayXX_主题/
├── tutorial.md
├── requirements.txt
├── config.py          # Local config (imports from project root config.py)
├── models.py          # Data models
├── example.py         # Runnable example
└── utils.py           # Shared helpers
```

## Import Pattern for Day Code Files

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
```

## Key Technical Constraints

- **Python**: 3.11+
- **LLM SDK**: `openai` (native OpenAI-compatible SDK, NOT LangChain)
- **LLM API**: DeepSeek V4 Flash (`deepseek-v4-flash`) via `https://api.deepseek.com/v1`
- **Vector DB**: ChromaDB (native SDK, not LangChain wrapper)
- **Embedding model**: `BAAI/bge-small-zh-v1.5` via HuggingFace mirror
- **API keys**: Managed via `.env` file; **never hardcode** — always use `os.getenv()` or import from `config.py`
- **Web UI**: Streamlit

## Code Standards

- Every line of code must have detailed Chinese comments
- Use `os.getenv()` for API keys (never hardcode)
- Use native `openai` SDK (never LangChain)
- File header with multi-line docstring (功能 + 学习目标)
- `main()` function wrapped in try/except
- Single file ≤500 lines; split into modules beyond that
- Set `os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"` before importing sentence-transformers

## Tutorial Format

Each tutorial.md follows a 9-section structure:
1. 学习目标 (blockquote)
2. 前一天知识回顾
3. 新知识讲解 (concept + analogy + principle)
4. 实例演示 (code snippet references, not full code)
5. 练习题 (basic/advanced/challenge tiers)
6. 后一天知识展望
7. 今日总结
8. 下一步
9. 参考资料

## Design Principles

1. **Protocol over framework**: native `openai` SDK + MCP protocol, not LangChain wrappers
2. **Context over prompt**: teach context engineering, not prompt tricks
3. **Agent first, RAG second**: Agent is the core paradigm; RAG is a tool within it
4. **Lean RAG**: 5 days covering what's actually used in production
5. **MCP as infrastructure**: introduced early (Day 10) as the tool standard
6. **Learn by building**: mini-projects at each phase end, full capstone at the end
