from google import genai
from google.genai import types
from fastapi import APIRouter
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import os
import json
from .rag_setup import retrieve_relevant_chunks
load_dotenv()

router = APIRouter()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# For outputs of llm
# Simplified schema - only using properties supported by Gemini API
reg_schema = {
    "type": "object",
    "properties": {
        "interviewer_message": {"type": "string", "minLength": 1}
    },
    "required": ["interviewer_message"]
}

grade_schema = {
  "type": "object",
  "properties": {
    "orm_pass": {
      "type": "string",
      "enum": ["Yes", "No"]
    },
    "grade": {
      "type": "integer",
      "minimum": 0,
      "maximum": 10
    },
    "interviewer_message": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": ["orm_pass", "grade", "interviewer_message"]
}

def extract_gemini_text(resp) -> str:
    """
    Extract full text from Gemini response reliably.
    Do NOT trust resp.text (it can be partial in some SDK paths).
    Prefer concatenating candidate content parts.
    """
    candidates = getattr(resp, "candidates", None) or []
    if candidates:
        cand0 = candidates[0]
        content = getattr(cand0, "content", None)
        parts = getattr(content, "parts", None) or []

        joined = "".join((getattr(p, "text", "") or "") for p in parts).strip()
        if joined:
            return joined

    # Fallback only if parts are missing/empty
    text = getattr(resp, "text", None)
    return (text or "").strip()

#Here are all the components/functions i want to make for my llm_service

# 1. set up LLM parameters (only respond in text, dont make pictures, 250 word limit, things like that)
# 2. get context from past messages
# 3. build the LLM prompt. incorporate values from functions (1) and (2), as well as give user input
# 4. generate content (setting the data to chat and getting hte response, then returning the response)

class LLMConfig:
    # Constructor function
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
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
            "IMPORTANT: If this is the first message in the conversation (no past messages), you MUST start by asking the user what their role is within the financial institution.",
            "If you already know their role, begin asking questions to determine if the user is following proper operational risk management practices.",
            "Do NOT create or describe images, diagrams, or markdown tables.",
            "Return JSON only and match the response schema exactly. Do not include extra keys or text outside JSON.",
            "The interviewer_message should contain your feedback or question.",
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
        #contents.append(
        #    {
        #        "role": "user",
        #        "parts": [
        #            {"text": f"System instructions: {config.system_instructions()}"}
        #        ],
        #    }
        #)

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

    def _parse_json_or_none(self, text: str) -> Optional[dict]:
        """
        Try to parse a JSON string. Return dict if valid, otherwise None.
        """
        try:
            return json.loads(text)
        except Exception:
            return None

    def _format_json_response(self, data: dict) -> str:
        """
        Format the JSON response into the desired output format:
        orm_pass: Yes/No
        grade: 0-10
        
        [interviewer_message]
        """
        try:
            if not isinstance(data, dict):
                return json.dumps(data, indent=2)
            
            parts = []
            
            # Extract ORM information (now flat structure)
            if "orm_pass" in data:
                parts.append(f"orm_pass: {data['orm_pass']}")
            if "grade" in data:
                parts.append(f"grade: {data['grade']}")
            
            # Add blank line before feedback
            if parts:
                parts.append("")
            
            # Add interviewer message (feedback)
            if "interviewer_message" in data:
                parts.append(data["interviewer_message"])
            elif "question" in data:
                # Fallback: use "question" field if interviewer_message is missing
                parts.append(data["question"])
            
            return "\n".join(parts)
        except Exception as e:
            print(f"Error formatting JSON response: {e}")
            # Fallback: return the original JSON string
            return json.dumps(data, indent=2)

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

        # Determine which schema to use based on number of assistant responses
        assistant_count = sum(1 for msg in (past_messages or []) if msg.get("role") == "assistant")
        current_schema = reg_schema if assistant_count < 2 else grade_schema

        # Content configuration for llm
        gen_config = types.GenerateContentConfig(
                system_instruction=self.config.system_instructions(),
                response_mime_type="application/json",
                response_schema=current_schema,
                temperature=0.2, # adjust if needed
                max_output_tokens=600,  # adjust if needed
            )

        try:
            # Call Gemini
            try:
                response = self.client.models.generate_content(
                    model=self.config.model,
                    contents=contents,
                    config=gen_config,
                )
            except Exception as api_error:
                print(f"Gemini API call failed: {str(api_error)}")
                print(f"Error type: {type(api_error)}")
                import traceback
                print(traceback.format_exc())
                
                # Check if it's a quota/rate limit error - check the error object directly
                error_str = str(api_error)
                error_repr = repr(api_error)
                
                # Check for quota errors in multiple ways
                is_quota_error = (
                    "429" in error_str or 
                    "RESOURCE_EXHAUSTED" in error_str or 
                    "quota" in error_str.lower() or
                    "429" in error_repr or
                    "RESOURCE_EXHAUSTED" in error_repr
                )
                
                if is_quota_error:
                    print("Detected quota/rate limit error")
                    default_data = {
                        "orm_pass": "No",
                        "grade": 0,
                        "interviewer_message": "I apologize, but the API quota has been exceeded. Please try again later or check your API billing settings."
                    }
                else:
                    # Return a default formatted response for other errors
                    print(f"Non-quota error detected: {error_str[:200]}")
                    default_data = {
                        "orm_pass": "No",
                        "grade": 0,
                        "interviewer_message": f"I apologize, but I encountered an error: {error_str[:100]}. Please try again."
                    }
                return self._format_json_response(default_data)
            
            print("RAG matches:", len(matches))
            print("First chunk:", matches[0] if matches else None)
            print(f"System instructions: {self.config.system_instructions()[:200]}...")
            print(f"Past messages count: {len(past_messages) if past_messages else 0}")
            
            # Extract text from response - handle different response structures
            response_text = None
            try:
                response_text = extract_gemini_text(response)
            except Exception as e:
                print(f"Error extracting text from response: {e}")
            
            if not response_text:
                print("Warning: No text content found in Gemini response")
                print(f"Response object: {response}")
                print(f"Response type: {type(response)}")
                if hasattr(response, 'candidates'):
                    print(f"Response candidates: {response.candidates}")
                print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                # Try to get more info about why there's no text
                if hasattr(response, 'prompt_feedback'):
                    print(f"Prompt feedback: {response.prompt_feedback}")
                default_data = {
                    "orm_pass": "No",
                    "grade": 0,
                    "interviewer_message": "I apologize, but I encountered an error processing the response. Please try again.",
                }
                return self._format_json_response(default_data)
            
            print(f"Response text preview: {response_text[:300]}")
            print(f"Response text length: {len(response_text)}")
            
            # Json payloaddd first try
            data = self._parse_json_or_none(response_text)
            if data is not None:
                # Check if it has the basic structure we need (be lenient)
                if isinstance(data, dict):
                    # Check for reg_schema format (only interviewer_message) or grade_schema format (orm_pass + grade + interviewer_message)
                    has_interviewer_message = "interviewer_message" in data
                    has_orm_pass = "orm_pass" in data
                    has_grade = "grade" in data
                    
                    # Validate based on which schema we're using
                    is_reg_schema = assistant_count < 2
                    if is_reg_schema:
                        # For reg_schema, only need interviewer_message
                        if has_interviewer_message:
                            print("Successfully parsed and validated JSON response (reg_schema)")
                            formatted_response = self._format_json_response(data)
                            return formatted_response
                        else:
                            print(f"JSON parsed but missing interviewer_message. Keys: {data.keys()}")
                    else:
                        # For grade_schema, need orm_pass, grade, and interviewer_message
                        if has_orm_pass and has_grade and has_interviewer_message:
                            print("Successfully parsed and validated JSON response (grade_schema)")
                            formatted_response = self._format_json_response(data)
                            return formatted_response
                        else:
                            print(f"JSON parsed but missing required fields. Has orm_pass: {has_orm_pass}, Has grade: {has_grade}, Has interviewer_message: {has_interviewer_message}")
                else:
                    print(f"JSON parsed but is not a dict. Type: {type(data)}")

            # If JSON parsing failed, try repair
            print("JSON parsing failed, attempting repair...")
            
            # Build repair prompt based on current schema
            is_reg_schema = assistant_count < 2
            if is_reg_schema:
                repair_prompt = (
                    "Your previous output was invalid JSON or did not match the response schema. "
                    "Return ONLY valid JSON with this exact structure: "
                    '{"interviewer_message": "your message"}. '
                    "Do not include any extra text or markdown formatting."
                )
            else:
                repair_prompt = (
                    "Your previous output was invalid JSON or did not match the response schema. "
                    "Return ONLY valid JSON with this exact structure: "
                    '{"orm_pass": "Yes" or "No", "grade": 0-10, '
                    '"interviewer_message": "your message"}. '
                    "Do not include any extra text or markdown formatting."
                )
            
            repair_contents = contents + [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": repair_prompt
                        }
                    ],
                }
            ]

            try:
                response2 = self.client.models.generate_content(
                    model=self.config.model,
                    contents=repair_contents,
                    config=gen_config,
                )
            except Exception as repair_error:
                print(f"Repair API call failed: {repair_error}")
                # Return first response even if not valid JSON
                return response_text

            # Extract text from second response
            response2_text = None
            try:
                response2_text = extract_gemini_text(response2)
            except Exception as e:
                print(f"Error extracting text from repair response: {e}")

            # Try to parse and format the second attempt
            if response2_text:
                data2 = self._parse_json_or_none(response2_text)
                if data2 is not None and isinstance(data2, dict):
                    is_reg_schema = assistant_count < 2
                    has_interviewer_message = "interviewer_message" in data2
                    
                    if is_reg_schema and has_interviewer_message:
                        # Format the JSON into the desired output format
                        formatted_response2 = self._format_json_response(data2)
                        return formatted_response2
                    elif not is_reg_schema:
                        has_orm_pass = "orm_pass" in data2
                        has_grade = "grade" in data2
                        if has_orm_pass and has_grade and has_interviewer_message:
                            # Format the JSON into the desired output format
                            formatted_response2 = self._format_json_response(data2)
                            return formatted_response2
                # Fallback: return raw text if parsing fails
                return response2_text
            else:
                # Fallback: return first response even if not valid
                return response_text
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in generate_reply: {str(e)}")
            print(f"Full traceback:\n{error_trace}")
            # Return a default formatted response instead of raising
            default_data = {
                "orm_pass": "No",
                "grade": 0,
                "interviewer_message": "I apologize, but I encountered an error. Please try again."
            }
            return self._format_json_response(default_data)



# Create and export a singleton instance
llm_service = LLMService(client=client)