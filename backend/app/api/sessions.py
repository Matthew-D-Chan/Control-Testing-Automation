from fastapi import APIRouter, HTTPException, FastAPI
from datetime import datetime
from typing import List

# Importing schemas
from app.schema.schemas import (
    Message,
    Session,
    AnswerRequest,
    AnswerResponse,
    generate_id,
    SessionSummary
)

# Importing supabase client
from data.database import supabase

router = APIRouter(
    prefix="/sessions",
    tags=["chats"]
)

# ********** Fake LLM feedback ********** Making a separate file for this later

def get_llm_feedback(user_answer: str) -> str:
    return (
        "Later: replace with a real LLM call (OpenAI/Gemini)."
        "Right now it's just a placeholder so your frontend can talk to something."
    )

# ********** Routes **********

# ***** Menu of all sessions *****
@router.get("/", response_model=List[SessionSummary])
async def list_sessions():
    # Return all chat sessions, which can be found in chat_sessions
    # Later, you can filter by user_id once auth is added.
    result = (
        supabase
        .table("chat_sessions")
        .select("*")
        .order("created_at", desc=True)   # newest first, like ChatGPT sidebar
        .execute()
    )

    # If there are no sessions yet, just return an empty list
    if not result.data:
        return []

    return [
        SessionSummary(
            id=row["id"], # Iterate through all ids to return a list of all sessions in SessionSummary format
            createdAt=row["created_at"],
        )
        for row in result.data
    ]

# ***** Create a new session *****
@router.post("/", response_model=SessionSummary, status_code=201)
async def create_session():
    # (A) Generate a new session id
    new_session_id = generate_id("sess")

    # (B) Insert a new row into chat_sessions
    insert_payload = {
        "id": new_session_id,
        # "user_id": current_user_id  # Later if I made the auth
        # Create at will be auto made 
    }

    result = (
        supabase
        .table("chat_sessions")
        .insert(insert_payload)
        .execute()
    )

    if not result.data:
        # Something went wrong with the insert
        raise HTTPException(status_code=500, detail="Failed to create session")

    # 3) Grab the row Supabase just created
    session_row = result.data[0]

    # 4) Return it in the shape of SessionSummary
    return SessionSummary(
        id=session_row["id"],
        createdAt=session_row["created_at"],
    )

# ***** Get a specific chat session and all of its messages *****
@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str):

    # (A) Look to the correct table in database
    session_result = (
        supabase
        .table("chat_sessions") # Look at the chat_session table (this is what we want to work with)
        .select("*")            # Select all columns 
        .eq("id", session_id)   # Find the column with the id we have provided (in fn params)
        .execute()              # Finally, Execute the query
    )

    if not session_result.data:
        raise HTTPException (status_code=404, detail="Session not found")

    # Store the specific chat session
    session_row = session_result.data[0] # supabase returns a dict. session_result.data is a list. We use [0] to get the first row of the list, which is the info of 1 session

    # (B) Fetch all the messages from the session that are in the database
    messages_result = (
        supabase
        .table("chat_messages")          # Look at the chat_messages table 
        .select("*")                     # Take all columns 
        .eq("session_id", session_id)    # Grab the specific session 
        .order("created_at", desc=False) # Sort oldest to newset 
        .execute()
    )

    # Converting the database rows into pydantic models (because there was initially some descrepincy)
    messages = [
        Message(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            createdAt=m["created_at"],
        )
        for m in messages_result.data
    ]

    # need to return some supabase version
    return Session(
        id=session_row["id"],
        createdAt=session_row["created_at"],
        messages=messages # The array from above of the properly converted pydantic schema messages 
    )

# ***** UserInput and Chatbot response *****
# - After submission, we store the users message (inbound payload)
# - Generate LLM feedback
# - Store feedback as assistant message
# - Return both messages
@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def post_answer(session_id: str, payload: AnswerRequest):
    # (A) Confirm the session exists
    session_result = (
        supabase
        .table("chat_sessions")
        .select("id")
        .eq("id", session_id)
        .execute()
    )
    
    if not session_result.data:
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
        createdAt=now
    )

    # (D) Save user and assistant messages to database
    insert_payload = [
        {
            "id": user_msg.id,
            "session_id": session_id,
            "role": user_msg.role,
            "content": user_msg.content,
            # Convert datetime to ISO 8601 string for JSON serialization
            "created_at": user_msg.createdAt.isoformat(),
        },
        {
            "id": assistant_msg.id,
            "session_id": session_id,
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            # Convert datetime to ISO 8601 string for JSON serialization
            "created_at": assistant_msg.createdAt.isoformat(),
        },
    ]

    # Just execute table insert, leave it up to supabase for error trapping
    supabase.table("chat_messages").insert(insert_payload).execute()

    
    # (E) Return both messages (user request and LLM answer) !!! Now we can shoot it to the frontend
    return AnswerResponse(
        feedback=feedback_text,
        messages=[user_msg, assistant_msg]
    )

@router.delete("/{session_id}")
async def delete_session(session_id : str):
    # Query chat_sessions tabe in supabase, find desired id to delete, and delete it 
    result = (
        supabase
        .table("chat_sessions")
        .delete()
        .eq("id", session_id)
        .execute()
    )
    # If no rows were deleted, the session didn't exist
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return

# PATCH /api/chat_sessions/{id} → rename a session. Still Need to implement this!! After POC