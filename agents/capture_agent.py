from tools.ollama_client import query_ollama

def run(text: str) -> str:
    prompt = f"""
    Classify this input into one of:
    - task
    - note
    - article

    Input:
    {text}

    Respond only with category.
    """

    category = query_ollama(prompt).strip().lower()

    return f"Captured as: {category}"