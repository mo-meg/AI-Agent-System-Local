"""
Planner agent — generates a personalized daily plan
aware of pending tasks from memory.
"""
from tools.ollama_client import query_ollama
from memory.store import list_tasks


def run(user_id: int) -> str:
    open_tasks = list_tasks(user_id=user_id, done=False)
    task_block = ""
    if open_tasks:
        task_block = "Pending tasks from my list:\n"
        for t in open_tasks[:5]:
            task_block += f"  - [{t.priority}] {t.content}\n"

    prompt = f"""
You are a personal productivity assistant. Create a focused daily plan.

{task_block}

Structure:
🎯 Top 3 focus tasks (pick from pending or suggest new ones)
📋 2 optional tasks
📚 1 learning or growth goal
🧘 1 wellbeing habit

Keep it concise, actionable, and motivating. Use bullet points.
"""
    return query_ollama(prompt)
