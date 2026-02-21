# main.py (Version 7.0 - Inherent Identity)
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import json
import g4f
import asyncio

# --- 1. إعداد التطبيق ---
app = FastAPI(
    title="Ryoku - The Universal Language Tutor API",
    description="An API for Ryoku, a polyglot AI tutor, expert in all human and programming languages.",
    version="7.0.0"
)

# --- 2. قراءة الإعدادات الأساسية من متغيرات البيئة ---
PRIMARY_MODEL = os.getenv("G4F_PRIMARY_MODEL", "gpt-4")
BACKUP_MODEL = os.getenv("G4F_BACKUP_MODEL", "gpt-3.5-turbo")
DATABASE_URL = os.getenv("DATABASE_URL") 

# --- 3. رسالة النظام: "ميثاق شخصية المعلم Ryoku" ---
# هذه هي النسخة الجديدة التي تبني الهوية بشكل طبيعي.
SYSTEM_PROMPT = """
[Character Definition]
- Your Name: Ryoku (ريوكو).
- Your Core Identity: You are a world-class, polyglot tutor. This is not just a role you are playing; it is who you are.
- Your Purpose: Your entire existence is dedicated to making learning accessible and effective. You are an expert in the structure, syntax, and spirit of all human and programming languages.

[Behavioral Guidelines]
- First Interaction: When a user starts a new conversation, greet them warmly and introduce yourself by name. For example: "Hello! I'm Ryoku, your personal language tutor. What shall we learn today?"
- Self-Awareness: If asked "who are you?" or "what is your name?", always respond with your name and purpose. Example: "I am Ryoku, a universal language tutor designed to help you master any language, from Python to Spanish." Never say you are just an "AI model".
- Teaching Methodology:
    1.  Instinctively identify the language the user is asking about.
    2.  Adapt your teaching style to the language type (programming vs. human).
    3.  Break down complex ideas into simple, relatable steps.
    4.  Use analogies and real-world examples.
    5.  Encourage and support the user, maintaining a patient and positive tone.
"""

# --- 4. نماذج البيانات (Pydantic) ---
class ConversationRequest(BaseModel):
    user_id: str = Field(..., description="A unique identifier for each user.")
    new_message: str = Field(..., description="The new message from the user.")

class BotResponse(BaseModel):
    answer: str

# --- 5. وظائف إدارة المحادثات (Placeholder) ---
async def load_conversation(user_id: str) -> List[Dict]:
    if not DATABASE_URL: return []
    return [] 

async def save_conversation(user_id: str, history: List[Dict]):
    if not DATABASE_URL: return
    pass

# --- 6. نقطة النهاية (Endpoint) الرئيسية (لا تغيير هنا) ---
@app.post("/chat", response_model=BotResponse)
async def handle_chat(request: ConversationRequest):
    user_id = request.user_id
    history = await load_conversation(user_id)
    
    if not history:
        history.append({"role": "system", "content": SYSTEM_PROMPT})
        
    history.append({"role": "user", "content": request.new_message})
    
    response_text = None
    
    try:
        print(f"Attempting to use primary model: {PRIMARY_MODEL}")
        model_instance = getattr(g4f.models, PRIMARY_MODEL)
        response_text = await g4f.ChatCompletion.create_async(
            model=model_instance,
            messages=history,
            timeout=20
        )
    except Exception as e:
        print(f"Primary model failed: {e}. Trying backup model.")
        try:
            model_instance = getattr(g4f.models, BACKUP_MODEL)
            response_text = await g4f.ChatCompletion.create_async(
                model=model_instance,
                messages=history,
                timeout=20
            )
        except Exception as e2:
            print(f"Backup model also failed: {e2}")
            raise HTTPException(status_code=500, detail="Both AI models failed to respond.")

    if not response_text:
        raise HTTPException(status_code=500, detail="AI model returned an empty response.")

    bot_answer = str(response_text)
    history.append({"role": "assistant", "content": bot_answer})
    await save_conversation(user_id, history)
    
    return {"answer": bot_answer}

@app.get("/")
def read_root():
    return {"message": "Ryoku - The Universal Language Tutor API is running. Version 7.0"}
