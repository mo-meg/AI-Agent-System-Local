from tools.ollama_client import query_ollama
from tools.web_loader import extract_text_from_url

def run(input_text: str) -> str:
    content = extract_text_from_url(input_text)

    prompt = f"""
    Summarize the following content clearly:

    {content}
    """

    return query_ollama(prompt)