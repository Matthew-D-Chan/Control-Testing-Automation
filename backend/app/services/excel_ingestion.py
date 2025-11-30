# backend/rag/ingest_excels.py

import os
import pandas as pd
from supabase import create_client
from google import genai
from dotenv import load_dotenv
load_dotenv()

# --------- CONFIG ---------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SECRET_KEY")  # secret server key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

EMBEDDING_MODEL = "models/text-embedding-004"  # or whatever you're using

# Excel file paths (relative to backend/)
EXCEL_FILES = [
    ("data/excel/ORX Reference Control Library May 2022.xlsx",
     "ORX_RCL_2022"),
    ("data/excel/ORX Cause & Impact Taxonomy Reference Taxonomy Data File.xlsx",
     "ORX_Cause_Impact"),
    ("data/excel/Mapping ORX Taxonomy to EBA final taxonomy - September 2025.xlsx",
     "ORX_EBA_Mapping"),
]
# ---------------------------

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
gemini = genai.Client(api_key=GEMINI_API_KEY)

def get_embedding(text: str):
    """Call Gemini embedding API and return a list[float]."""
    res = gemini.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return res.embeddings[0].values

def row_to_text(row: pd.Series) -> str:
    """
    Turn a whole Excel row into one text string.
    Generic: includes all non-null columns as "Column: value".
    Works even if we don't know the column names ahead of time.
    """
    parts = []
    for col, val in row.items():
        if pd.isna(val):
            continue
        parts.append(f"{col}: {val}")
    return " | ".join(parts)

def ingest_excel(path: str, source_name: str, start_index: int = 0) -> int:
    """
    Ingest a single Excel file into the `chunks` table.
    Returns the next chunk_index to use (so indexes can continue across files).
    """
    print(f"\n=== Ingesting {path} as source '{source_name}' ===")

    # Read all sheets
    xls = pd.ExcelFile(path)
    chunk_index = start_index

    for sheet_name in xls.sheet_names:
        print(f"  Sheet: {sheet_name}")
        df = pd.read_excel(xls, sheet_name=sheet_name)

        for row_idx, row in df.iterrows():
            text = row_to_text(row)
            if not text.strip():
                continue

            emb = get_embedding(text)

            # Insert into chunks table
            supabase.table("chunks").insert({
                "chunk_index": int(chunk_index),
                "content": text,
                "metadata": {
                    "source": source_name,
                    "sheet": sheet_name,
                    "row": int(row_idx),
                },
                "embedding": emb,
            }).execute()

            chunk_index += 1

    print(f"Finished {path}. Total chunks so far: {chunk_index - start_index}")
    return chunk_index

def main():
    next_index = 0
    for path, source_name in EXCEL_FILES:
        if not os.path.exists(path):
            print(f"!! File not found: {path} (skipping)")
            continue
        next_index = ingest_excel(path, source_name, start_index=next_index)

    print(f"\nAll done. Last chunk_index used: {next_index - 1}")

if __name__ == "__main__":
    main()
