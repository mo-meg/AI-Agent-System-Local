import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALLOWED_USER_IDS = [int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x]

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Memory
DB_PATH = os.getenv("DB_PATH", "memory/agent_memory.db")

# Whisper (speech-to-text)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny | base | small | medium

# Scheduler
DAILY_PLAN_HOUR = int(os.getenv("DAILY_PLAN_HOUR", "8"))
DAILY_PLAN_MINUTE = int(os.getenv("DAILY_PLAN_MINUTE", "0"))
