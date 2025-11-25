from fastapi import APIRouter, HTTPException, FastAPI
from datetime import datetime

# Importing schemas
from app.schema.schemas import (
    Message,
    Session,
    AnswerRequest,
    AnswerResponse,
    generate_id,
)

router = APIRouter(
    prefix="/sessions",
    tags=["chats"]
)

# ********** Fake LLM feedback (stub) **********

def get_llm_feedback(user_answer: str) -> str:
    return (
        "Later: replace with a real LLM call (OpenAI/Gemini)."
        "Right now it's just a placeholder so your frontend can talk to something."
    )

# ---------- Routes ----------

@router.get("/")
def get_sessions():
    return {"message": "Sessions route is working!"}
