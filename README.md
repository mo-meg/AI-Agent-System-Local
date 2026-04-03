# 🤖 Personal AI OS — Telegram Edition

A fully local, autonomous AI operating system for daily life, running on your machine via [Ollama](https://ollama.com) and controlled through Telegram.

---

## ✨ What's new in this version

| Feature | Details |
|---|---|
| **Persistent memory** | SQLite via SQLAlchemy — tasks, notes, reminders, conversation context all saved across restarts |
| **Intent router** | LLM-based intent classification with keyword fast-paths — no more rigid `if "http" in text` |
| **Reminder agent** | Natural-language time parsing — "remind me in 2 hours to call mom" just works |
| **Voice notes** | Whisper STT transcribes OGG voice messages and routes them through the agent stack |
| **Image understanding** | LLaVA vision model describes photos; captions are combined with description for routing |
| **Daily plan push** | APScheduler sends a personalized morning plan at your configured time |
| **Conversation memory** | Last N turns stored per user, injected as context into the chat agent |
| **Auth guard** | Whitelist Telegram user IDs — no one else can use your bot |
| **Telegram command menu** | `/tasks`, `/notes`, `/plan`, `/clear`, `/help` registered as proper bot commands |
| **Chat agent** | Conversational fallback with full context window (no longer just a classify-and-quit flow) |

---

## 🗂 Project structure

```
ai-agent-system/
├── app/
│   ├── main.py          — entry point
│   └── config.py        — env-driven config
├── agents/
│   ├── capture_agent.py — classify + persist notes/tasks
│   ├── chat_agent.py    — conversational fallback with memory
│   ├── planner_agent.py — personalized daily plan (task-aware)
│   ├── reminder_agent.py— NL time parsing + reminder creation
│   ├── summarizer_agent.py — URL/text summarization
│   └── vision_agent.py  — image description via LLaVA
├── orchestrator/
│   └── router.py        — intent classification + dispatch
├── tools/
│   ├── ollama_client.py — Ollama LLM wrapper (single + multi-turn)
│   ├── scheduler.py     — APScheduler (daily plan + reminder check)
│   ├── web_loader.py    — URL text extraction
│   └── whisper_client.py— Whisper STT (OGG → text)
├── memory/
│   └── store.py         — SQLite ORM (tasks, notes, reminders, context)
├── interfaces/
│   └── telegram_bot.py  — full Telegram bot (text, voice, photo, commands)
├── logs/
├── .env.example
└── requirements.txt
```

---

## 🚀 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For voice note support, also install:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### 2. Pull Ollama models

```bash
ollama pull llama3        # text agent (required)
ollama pull llava         # vision/image agent (optional)
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set TELEGRAM_TOKEN and ALLOWED_USER_IDS
```

Get your Telegram user ID by messaging [@userinfobot](https://t.me/userinfobot).

### 4. Run

```bash
python -m app.main
```

---

## 💬 Usage examples

| You say | What happens |
|---|---|
| `https://example.com/article` | Summarizes the URL |
| `remind me in 30 minutes to take a break` | Sets a reminder, fires a push notification |
| `save note: idea for weekend project` | Classifies + saves to notes DB |
| `add task: review quarterly report` | Saves as a task with normal priority |
| `/tasks` | Lists all pending tasks |
| `done 3` | Marks task #3 as complete |
| `/plan` | Generates a task-aware daily plan |
| 🎤 voice note | Transcribed with Whisper, then routed |
| 🖼 photo | Described by LLaVA, caption routed if present |
| Anything else | Conversational chat with 5-turn memory |

---

## 🔧 Extending

**Add a new agent:**
1. Create `agents/my_agent.py` with a `run(user_id, text) -> str` function
2. Add an intent keyword to `orchestrator/router.py`'s `_fast_route` or the `_INTENT_PROMPT`
3. Add the routing branch in `route_task()`

**Add a new tool:**
1. Create `tools/my_tool.py`
2. Import and call it from any agent

**Swap the LLM:**
Change `OLLAMA_MODEL` in `.env` to any model you've pulled — `mistral`, `gemma3`, `phi3`, etc.

---

## 📦 Dependencies

- `python-telegram-bot` — Telegram async bot framework
- `sqlalchemy` — ORM for SQLite memory layer
- `apscheduler` — background job scheduler
- `openai-whisper` — local speech-to-text
- `pydub` — audio format conversion
- `requests` / `beautifulsoup4` — web scraping
- `loguru` — structured logging
- `python-dotenv` — env file loading
