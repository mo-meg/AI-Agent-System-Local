"""
Chat agent — conversational fallback with persistent context window.
Stores and retrieves last N turns per user.
"""
from tools.ollama_client import query_ollama
from memory.store import append_context, get_context

_SYSTEM = """You are a helpful personal AI assistant integrated into Telegram.
Be concise, warm, and practical. You help with daily tasks, thinking, and productivity.
If the user wants to save a note or task, guide them to do so."""


def run(user_id: int, text: str) -> str:
    context = get_context(user_id=user_id, max_turns=5)
    response = query_ollama(
        prompt=f"User: {text}\nAssistant:",
        system=_SYSTEM,
        context=context,
    )
    # Persist both turns
    append_context(user_id, "user", text)
    append_context(user_id, "assistant", response)
    return response
