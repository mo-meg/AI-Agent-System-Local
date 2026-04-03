"""
Ollama client — supports single-turn and multi-turn (with context history).
"""
import requests
from loguru import logger
from app.config import OLLAMA_URL, OLLAMA_MODEL


def query_ollama(prompt: str, system: str = "", context: list = None) -> str:
    """
    Single-turn generation. `context` is a list of
    {"role": "user"|"assistant", "content": "..."} dicts
    that get prepended as a conversation history block.
    """
    full_prompt = ""

    if system:
        full_prompt += f"[SYSTEM]\n{system}\n\n"

    if context:
        for msg in context:
            tag = "User" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{tag}: {msg['content']}\n"
        full_prompt += "\n"

    full_prompt += prompt

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        return "⚠️ LLM unavailable — is Ollama running?"
