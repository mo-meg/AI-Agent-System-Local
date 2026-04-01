# AI Agent System (Local)

## Features
- Telegram bot interface
- Local LLM (Ollama)
- Multi-agent system (basic)
- Summarization + capture + planning

## Setup

### 1. Install Ollama
https://ollama.com

```bash
ollama run llama3

uv init
uv venv

uv venv --python 3.11

source .venv/bin/activate

uv pip install -r requirements.txt

python -m app.main