from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import uuid

def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# ********** Temporary Pydantic Models ********** Will make its own folder once backend skeleton done
# 'class' is used since it acts a reusable blueprint for the shape of the data

# Data shape of a message being sent
class Message(BaseModel):
    id: str
    role: str # 'user' Or 'assistant'
    content: str
    createdAt: datetime

# Data shape of a singular chat session
class Session(BaseModel):
    id: str
    createdAt: datetime
    messages: List[Message] # A list of message objects

# Data shape of the users text input
class AnswerRequest(BaseModel):
    userAnswer: str

# Data shape of the LLM's response
class AnswerResponse(BaseModel):
    feedback: str
    messages: List[Message] # Keep the total list of messages to give as context to the llm for the next question

# Summary of all the sessions the user made
class SessionSummary(BaseModel):
    id: str
    createdAt: datetime
    # Add title later 

