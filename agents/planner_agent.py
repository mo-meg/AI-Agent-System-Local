from tools.ollama_client import query_ollama

def run() -> str:
    prompt = """
    Create a simple productive daily plan in arabic language:
    - 3 main tasks
    - 2 optional tasks
    - 1 learning goal
    """

    return query_ollama(prompt)