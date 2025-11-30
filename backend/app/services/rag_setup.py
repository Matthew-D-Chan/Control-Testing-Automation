from google import genai
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "models/text-embedding-004"

# Create a separate client for embeddings to avoid circular import
embedding_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text: str) -> list[float]:
    # You can also strip/normalize text here
    res = embedding_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return res.embeddings[0].values

def chunk_text(text: str, max_chars: int = 800, overlap: int = 200) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)

    return chunks