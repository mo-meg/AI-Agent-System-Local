"""
Capture agent — classifies input and persists it to the memory layer.
Categories: task | note | article | idea
"""
from tools.ollama_client import query_ollama
from memory import store

_CLASSIFY_PROMPT = """
Classify this input into exactly one of: task, note, article, idea
Also extract tags (comma-separated keywords, max 3).

Input: {text}

Reply ONLY in this format:
CATEGORY: <category>
TAGS: <tags>
SUMMARY: <one short sentence summary>
"""


def run(user_id: int, text: str) -> str:
    raw = query_ollama(_CLASSIFY_PROMPT.format(text=text))

    category, tags, summary = "note", "", text[:120]
    for line in raw.splitlines():
        if line.startswith("CATEGORY:"):
            category = line.split(":", 1)[1].strip().lower()
        elif line.startswith("TAGS:"):
            tags = line.split(":", 1)[1].strip()
        elif line.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()

    if category == "task":
        store.add_task(user_id=user_id, content=summary)
        return f"✅ Task saved: _{summary}_\nTags: {tags}"
    else:
        store.add_note(user_id=user_id, content=summary, tags=tags)
        return f"📝 {category.capitalize()} saved: _{summary}_\nTags: {tags}"
