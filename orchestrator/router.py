"""
Orchestrator — classifies intent and routes to the correct agent.
Uses LLM-based intent detection for ambiguous inputs,
with keyword fast-paths for speed on clear cases.
"""
import re
from loguru import logger
from tools.ollama_client import query_ollama
from agents import (
    summarizer_agent,
    capture_agent,
    planner_agent,
    reminder_agent,
    chat_agent,
)
from memory.store import list_tasks, list_notes, complete_task

_INTENT_PROMPT = """
Classify this message into ONE of these intents:
- summarize   (has a URL or asks to summarize something)
- plan        (asks for a daily plan, schedule, agenda)
- capture     (wants to save a task, note, idea, article)
- remind      (wants a reminder or alert set)
- list_tasks  (wants to see their tasks)
- list_notes  (wants to see their notes)
- done        (marking a task as complete, e.g. "done 3" or "finished task 2")
- chat        (general conversation, question, or anything else)

Message: {text}

Reply with ONLY the intent word.
"""


def _fast_route(text_lower: str):
    """Keyword shortcuts to skip LLM classification for obvious cases."""
    if re.search(r'https?://', text_lower):
        return "summarize"
    if re.search(r'\b(plan|schedule|agenda|daily plan)\b', text_lower):
        return "plan"
    if re.search(r'\b(remind me|set a reminder|reminder)\b', text_lower):
        return "remind"
    if re.search(r'\b(list tasks|show tasks|my tasks|pending tasks)\b', text_lower):
        return "list_tasks"
    if re.search(r'\b(list notes|show notes|my notes)\b', text_lower):
        return "list_notes"
    if re.search(r'\b(done|finished|completed|mark done)\s+\d+', text_lower):
        return "done"
    return None


def _classify_intent(text: str) -> str:
    intent = query_ollama(_INTENT_PROMPT.format(text=text)).strip().lower()
    # Sanitize to known intents
    known = {"summarize", "plan", "capture", "remind", "list_tasks", "list_notes", "done", "chat"}
    return intent if intent in known else "chat"


def route_task(user_id: int, text: str) -> str:
    text_lower = text.lower().strip()

    intent = _fast_route(text_lower) or _classify_intent(text)
    logger.info(f"user={user_id} intent={intent} text={text[:60]}")

    if intent == "summarize":
        url_match = re.search(r'https?://\S+', text)
        url = url_match.group() if url_match else text
        return summarizer_agent.run(url)

    elif intent == "plan":
        return planner_agent.run(user_id=user_id)

    elif intent == "capture":
        return capture_agent.run(user_id=user_id, text=text)

    elif intent == "remind":
        return reminder_agent.run(user_id=user_id, text=text)

    elif intent == "list_tasks":
        tasks = list_tasks(user_id=user_id, done=False)
        if not tasks:
            return "✅ No pending tasks — you're all clear!"
        lines = [f"{t.id}. [{t.priority}] {t.content}" for t in tasks]
        return "📋 **Pending tasks:**\n" + "\n".join(lines)

    elif intent == "list_notes":
        notes = list_notes(user_id=user_id, limit=8)
        if not notes:
            return "📭 No notes yet."
        lines = [f"• {n.content[:80]}" for n in notes]
        return "📝 **Recent notes:**\n" + "\n".join(lines)

    elif intent == "done":
        m = re.search(r'\d+', text_lower)
        if m:
            task_id = int(m.group())
            success = complete_task(task_id)
            return f"✅ Task {task_id} marked done!" if success else f"⚠️ Task {task_id} not found."
        return "Please say which task number, e.g. 'done 3'"

    else:  # chat
        return chat_agent.run(user_id=user_id, text=text)
