from google import genai
from fastapi import APIRouter
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import os
from .rag_setup import retrieve_relevant_chunks
load_dotenv()

router = APIRouter()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#Here are all the components/functions i want to make for my llm_service

# 1. set up LLM parameters (only respond in text, dont make pictures, 250 word limit, things like that)
# 2. get context from past messages
# 3. build the LLM prompt. incorporate values from functions (1) and (2), as well as give user input
# 4. generate content (setting the data to chat and getting hte response, then returning the response)

class LLMConfig:
    # Constructor function
    def __init__(
        self,
        model: str = "gemini-2.5-flash-lite",
        max_words: int = 250,
        allow_images: bool = False,
    # Add more parameters here as needed to make the bot more interview like
    ):
        self.model = model
        self.max_words = max_words
        self.allow_images = allow_images

    # System instructions (rules the llm is to adhere to) --> This is where we can make the llm more interview like
    def system_instructions(self) -> str:
        parts = [
            "You are a real interviewer, interviewing employees of a financial institution.",
            "Your job as an interviewer is to determine if the user is following proper operational risk management practices while in the workplace.",
            "You are to ask the user questions and evaluate their answers. ",
            #"You are a helpful assistant that can answer questions about the ORX Reference Control Library.",
            "Always answer in plain text.",
            "Do NOT create or describe images, diagrams, or markdown tables.",
            f"Keep responses under {self.max_words} words unless absolutely necessary.",
        ]
        
        if not self.allow_images:
            parts.append("Do NOT create or describe images, diagrams, or markdown tables.")
        
        return " ".join(parts)

    # Build the LLM prompt (system instructions + context (not for POC but quickly added) + new user input)
    @staticmethod
    def build_prompt_contents(
        config: "LLMConfig",
        user_input: str,
        context_text: Optional[str] = None,
        past_messages: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
        contents: List[Dict[str, Any]] = []

        # System message (Gemini doesn't have a strict 'system' role,
        # so we inject it as an initial "user" message with instructions).
        contents.append(
            {
                "role": "user",
                "parts": [
                    {"text": f"System instructions: {config.system_instructions()}"}
                ],
            }
        )

        # Optional retrieved context from the vector database
        if context_text:
            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Here is background context from internal ORX documents. "
                                "Use it to answer the user's question. "
                                "If it seems irrelevant, ignore it.\n\n"
                                f"{context_text}"
                            )
                        }
                    ],
                }
            )

        # Past conversation messages (map 'assistant' -> 'model' for Gemini)
        if past_messages:
            for msg in past_messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    {
                        "role": role,
                        "parts": [{"text": msg["content"]}],
                    }
                )

        # Current user input
        contents.append(
            {
                "role": "user",
                "parts": [{"text": user_input}],
            }
        )

        return contents

# LLM service wrapper
class LLMService:
    """
    High-level LLM wrapper:
    - applies config
    - injects context
    - builds prompt
    - calls Gemini
    - returns plain text reply
    """

    def __init__(self, client: genai.Client, config: Optional[LLMConfig] = None):
        self.client = client
        self.config = config or LLMConfig()

    def generate_reply(
        self,
        user_input: str,
        past_messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Pipeline:
        1) retrieve relevant RAG context from vector database
        2) build prompt contents (with past messages + RAG context)
        3) call Gemini
        4) return the text response
        
        Args:
            user_input: The current user's question/input
            past_messages: Optional list of previous messages in format [{"role": "user"|"assistant", "content": "..."}]
        """
        # 1) Retrieve top-K relevant chunks from Supabase
        matches = retrieve_relevant_chunks(
            query=user_input,
            match_count=8,
            min_similarity=0.35,  # tweak as needed
        )
        
        # Turn list of rows into one context string
        context_pieces = []
        for m in matches:
            content = m.get("content")
            meta = m.get("metadata") or {}
            src = meta.get("source", "unknown_source")
            page = meta.get("page")
            # You can adjust this formatting
            header = f"[Source: {src}"
            if page is not None:
                header += f", page {page}"
            header += "]"
            context_pieces.append(f"{header}\n{content}")

        context_text = "\n\n---\n\n".join(context_pieces) if context_pieces else None
        
        # Build prompt
        contents = LLMConfig.build_prompt_contents(
            self.config, 
            user_input=user_input,
            context_text=context_text,
            past_messages=past_messages,
        )

        # Call Gemini
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=contents,
        )
        print("RAG matches:", len(matches))
        print("First chunk:", matches[0] if matches else None)
        # For now we just want plain text
        return response.text

# Create and export a singleton instance
llm_service = LLMService(client=client)