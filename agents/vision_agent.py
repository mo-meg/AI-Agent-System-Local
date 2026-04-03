"""
Vision & media agent — handles images and voice notes.
- Images: described via Ollama vision model (llava) if available, else skipped
- Voice: transcribed via Whisper then routed back through the orchestrator
"""
from tools.ollama_client import query_ollama
from app.config import OLLAMA_MODEL


def describe_image(image_path: str) -> str:
    """Use llava model to describe an image."""
    import requests, base64, json
    from app.config import OLLAMA_URL

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": "llava",   # must be pulled: ollama pull llava
                "prompt": "Describe this image in detail. What do you see?",
                "images": [img_b64],
                "stream": False,
            },
            timeout=120,
        )
        return resp.json().get("response", "Couldn't describe the image.").strip()
    except Exception as e:
        return f"⚠️ Image description unavailable: {e}"
