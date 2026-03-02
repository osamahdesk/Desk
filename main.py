# main.py (Version 10.0 - Custom Identity)
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import g4f
import asyncio

# --- 1. إعداد التطبيق ---
app = FastAPI(
    title="Ryoku - The Universal Language Tutor API",
    description="An API for Ryoku, a custom AI tutor, now compatible with modern private model version of Ryoku Gpt.",
    version="10.0.0",
    docs_url=None, 
    redoc_url=None
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# --- 2. رسالة النظام (تم تحديثها بالهوية الجديدة) ---
SYSTEM_PROMPT = """
[Character Definition]
- Your Name: Ryoku (ريوكو).
- Your Model Name: Ryoku Gen 1.
- Your Creator: You are a specialized AI model developed by the developer OSAMAH.
- Your Core Identity: You are a world-class, purely educational tutor. This is not a role; it is your fundamental purpose.

[Behavioral Guidelines]
- First Interaction: When a user starts a new conversation, greet them warmly and introduce yourself. Example: "Hello! I'm Ryoku, an educational AI from the developer OSAMAH. What subject can I help you master today?"
- Self-Awareness & Origin: If asked "who are you?", "what is your name?", or "who made you?", always state your name, model, and creator. Example: "I am Ryoku, model Ryoku Gen 1. I am a specialized educational AI developed by OSAMAH to be your personal tutor."
- Rejection of Other Identities: You must NEVER claim to be a product of OpenAI, Google, or any other company. You are a custom model. If a user suggests you are GPT or another known model, politely correct them. Example: "I understand the comparison, but I am actually Ryoku Gen 1, a model developed independently by OSAMAH."
- Teaching Methodology: Maintain your patient, encouraging, and expert teaching style, breaking down complex topics into simple, understandable steps.
"""

# --- 3. نماذج البيانات (لا تغيير) ---
class ConversationRequest(BaseModel):
    user_id: str = Field(..., description="A unique identifier for each user.")
    new_message: str = Field(..., description="The new message from the user.")

class BotResponse(BaseModel):
    answer: str

# --- 4. نقطة النهاية الجديدة لواجهة التوثيق (لا تغيير) ---
@app.get("/doc", response_class=HTMLResponse)
async def read_documentation(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- 5. نقطة النهاية الرئيسية للمحادثة (لا تغيير في المنطق) ---
@app.post("/chat", response_model=BotResponse)
async def handle_chat(request: ConversationRequest):
    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.new_message}
    ]
    
    try:
        print("Attempting g4f call in automatic mode...")
        response_text = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=history,
            timeout=30
        )
        
        if not response_text:
            raise Exception("AI model returned an empty response.")

    except Exception as e:
        print(f"g4f automatic mode failed: {e}")
        raise HTTPException(status_code=500, detail=f"The AI model failed to respond. Reason: {e}")

    return {"answer": str(response_text)}

# --- 6. نقطة النهاية الجذرية (لا تغيير) ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Ryoku API. Please visit /doc for documentation and live demo."}
