# backend/rag/ingest_pdfs.py
import os
from typing import List

import pandas as pd  # not strictly needed here, but fine if shared env
from supabase import create_client
from google import genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader  # pip install PyPDF2

load_dotenv()

# --------- CONFIG ---------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SECRET_KEY")  # secret server key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

EMBEDDING_MODEL = "models/text-embedding-004"  # same as Excel ingestion

# List of PDFs to ingest: (file_path, source_name)
# Paths are relative to backend/
PDF_FILES = [
    ("data/pdf/ORX Reference Control Library Study – Initial Results Report December 2021.pdf", "ORX_Results_Report_DEC_PDF"),
    ("data/pdf/ORX Reference Control Library Report.pdf", "ORX_LIBRARY_REPORT_PDF"),
    ("data/pdf/ORX Reference Control Library Guidance.pdf", "ORX_GUIDANCE_PDF"),
    ("data/pdf/ORX Event Type Reference Taxonomy 2019.pdf", "ORX_EVENT_TYPE_REFERENCE_TAXONOMY_2019_PDF"),
    ("data/pdf/ORX Controls Practices Paper – Control Optimisation, Monitoring & Testing, and Automation April 5.pdf","ORX_CONTROLS_PRACTICES_PAPER_PDF"),
    ("data/pdf/Full report - ORX Cause & Impacts Reference Taxonomy 2020.pdf","ORX_CAUSE_IMPACTS_REFERENCE_TAXONOMY_2020_PDF")
]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
gemini = genai.Client(api_key=GEMINI_API_KEY)


def get_embedding(text: str) -> List[float]:
    """Call Gemini embedding API and return a list[float]."""
    res = gemini.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return res.embeddings[0].values


def clean_text(text: str) -> str:
    """Basic cleanup: collapse whitespace and strip."""
    if not text:
        return ""
    # Turn newlines / multiple spaces into single spaces
    return " ".join(text.split())


def split_text_into_chunks(
    text: str,
    max_chars: int = 1200,
    overlap: int = 200,
):
    """
    Split a long string into overlapping chunks of ~max_chars length.
    Simple character-based splitter (good enough for most PDFs).
    Yields chunks one at a time to avoid memory issues with large texts.
    """
    text = text.strip()
    if not text:
        return

    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        
        # If we've reached the end, break
        if end >= text_len:
            break
        
        # move start forward with some overlap, ensuring we always advance
        new_start = end - overlap
        if new_start <= start:
            # Ensure we always move forward by at least 1 character
            new_start = start + 1
        
        start = new_start


def get_next_chunk_index() -> int:
    """
    Look at the existing chunks table and find the next available chunk_index.
    That way, Excel chunks and PDF chunks share one continuous index space.
    """
    result = (
        supabase.table("chunks")
        .select("chunk_index")
        .order("chunk_index", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        # No rows yet
        return 0

    max_idx = int(result.data[0]["chunk_index"])
    return max_idx + 1


def ingest_pdf(path: str, source_name: str, start_index: int = 0) -> int:
    """
    Ingest a single PDF into the `chunks` table.
    Each PDF page is turned into 1+ text chunks depending on length.
    Returns the next chunk_index to use.
    """
    print(f"\n=== Ingesting {path} as source '{source_name}' ===")

    reader = PdfReader(path)
    num_pages = len(reader.pages)
    chunk_index = start_index

    for page_num in range(num_pages):
        page = reader.pages[page_num]
        raw_text = page.extract_text() or ""
        page_text = clean_text(raw_text)

        if not page_text:
            print(f"  Page {page_num + 1}/{num_pages} has no extractable text, skipping.")
            continue

        # Process chunks incrementally to avoid memory issues
        page_chunks = split_text_into_chunks(page_text)
        chunk_count = 0

        for chunk_text in page_chunks:
            emb = get_embedding(chunk_text)

            supabase.table("chunks").insert({
                "chunk_index": int(chunk_index),
                "content": chunk_text,
                "metadata": {
                    "source": source_name,
                    "page": int(page_num),
                    "chunk_in_page": int(chunk_count),
                },
                "embedding": emb,
            }).execute()

            chunk_index += 1
            chunk_count += 1

        if chunk_count > 0:
            print(f"  Page {page_num + 1}/{num_pages}: processed {chunk_count} chunks")

    print(f"Finished {path}. Total chunks from this PDF: {chunk_index - start_index}")
    return chunk_index


def main():
    # Start AFTER whatever is already in the chunks table (Excel rows etc.)
    next_index = get_next_chunk_index()
    print(f"Starting chunk_index from: {next_index}")

    for path, source_name in PDF_FILES:
        if not os.path.exists(path):
            print(f"!! File not found: {path} (skipping)")
            continue

        next_index = ingest_pdf(path, source_name, start_index=next_index)

    if next_index == 0:
        print("\nNo PDFs ingested.")
    else:
        print(f"\nAll done. Last chunk_index used: {next_index - 1}")


if __name__ == "__main__":
    main()
