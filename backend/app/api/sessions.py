from fastapi import APIRouter, HTTPException, FastAPI
from datetime import datetime

# Importing schemas
from app.schema.schemas import (
    Message,
    Session,
    AnswerRequest,
    AnswerResponse,
    generate_id,
    sessions
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

# --- Get a specific chat session and all of its messages ---
@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException (status_code=404, detail="Session not found")

    session_data = sessions[session_id]

    return Session(
        id=session_id,
        createdAt=session_data["createdAt"],
        messages=session_data["messages"]
    )

# --- Submits an answer to this specific chat session
# - After submission, we store the users message (inbound payload)
# - Generate LLM feedback
# - Store feedback as assistant message
# - Return both messages
@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def post_answer(session_id: str, payload: AnswerRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now()

    # (A) The user message (an instance of the mydantic model 'Message')
    user_msg = Message(
        id=generate_id("msg_user"),
        role="user",
        # Taking out a piece of the pydantic model (userAnswer is a var inside the payload, AnswerRequest).
        # It looks generic because the payload is going to by dynamic based on what the user submits
        content=payload.userAnswer, 
        createdAt=now,
    )

    # (B) The LLM Feedback
    feedback_text = get_llm_feedback(payload.userAnswer) # Currently does nothing with the input

    # (C) Assistant feedback message
    assistant_msg = Message(
        id=generate_id("msg_assistant"),
        role="assistant",
        content=feedback_text, # Taken directly from the LLM feedback,
        createdAt = now
    )

    # (D) Save to the temp fake database
    sessions[session_id]["messages"].append(user_msg)
    sessions[session_id]["messages"].append(assistant_msg)

    # (E) Return both messages (user request and LLM answer)
    return AnswerResponse(
        feedback=feedback_text,
        messages=[user_msg, assistant_msg]
    )