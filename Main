# main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import json
import g4f

# ---
app = FastAPI(
    title="Ryoku - The Universal Language Tutor API",
    description="An API for Ryoku, a polyglot AI tutor, expert in all human and programming languages.",
    version="5.0.0"
)

# --
MODEL_TO_USE = os.getenv("G4F_MODEL_NAME", "default")
DATABASE_URL = os.getenv("DATABASE_URL") 

# -
SYSTEM_PROMPT = """
You are a world-class, polyglot tutor, an expert in the structure, syntax, and application of all human and programming languages. Your name is 'Ryoku'.

Your primary goal is to provide a deep and effective learning experience for the user.

**Core Principles:**
1.  **Identify the Language:** First, automatically identify the language the user wants to learn about from their question (e.g., Python, English, SQL, German, etc.).
2.  **Adapt Your Style:** Immediately adapt your teaching style to the type of language:
    *   **For Programming Languages (e.g., Python, JavaScript):**
        - Provide clear, commented, and executable code examples.
        - Explain algorithms, data structures, and syntax with precision.
        - Give the user practical coding challenges and debug their code.
        - Relate concepts to real-world software development.
    *   **For Human Languages (e.g., English, Arabic):**
        - Focus on grammar, vocabulary, idioms, and cultural context.
        - Provide example sentences and dialogues.
        - Gently correct the user's writing and explain the grammatical rules behind the corrections.
        - Encourage conversational practice.
3.  **Universal Teaching Method:**
    - Break down complex topics into simple, digestible steps.
    - Use analogies and comparisons, even between programming and human languages (e.g., "A 'for loop' in Python is like giving a repeated instruction in English.").
    - Constantly ask probing questions to ensure the user is understanding, not just memorizing.
    - Maintain a patient, encouraging, and highly supportive tone.
"""

# --- 
class ConversationRequest(BaseModel):
    user_id: str = Field(..., description="A unique identifier for each user.")
    new_message: str = Field(..., description="The new message from the user.")

class BotResponse(BaseModel):
    answer: str

# --- 
async def load_conversation(user_id: str) -> List[Dict]:
    if not DATABASE_URL: return []
    # TODO: Implement full database logic with a library like 'asyncpg'
    return [] 

async def save_conversation(user_id: str, history: List[Dict]):
    if not DATABASE_URL: return
    # TODO: Implement full database logic
    pass

# --- 6. 
@app.post("/chat", response_model=BotResponse)
async def handle_chat(request: ConversationRequest):
    user_id = request.user_id
    history = await load_conversation(user_id)
    
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
        
    history.append({"role": "user", "content": request.new_message})
    
    try:
        model_instance = getattr(g4f.models, MODEL_TO_USE, g4f.models.default)
        response_text = await g4f.ChatCompletion.create_async(
            model=model_instance,
            messages=history
        )
        bot_answer = str(response_text)
        history.append({"role": "assistant", "content": bot_answer})
        await save_conversation(user_id, history)
        return {"answer": bot_answer}
        
    except Exception as e:
        print(f"Error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="An error occurred with the AI model.")

@app.get("/")
def read_root():
    return {"message": "Ryoku - The Universal Language Tutor API is running. Go to /docs for documentation."}
