# main.py (Version 9.0 - Modern g4f Compatibility)
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
    description="A stable API for Ryoku, now compatible with modern g4f versions.",
    version="9.0.0",
    docs_url=None, 
    redoc_url=None
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# --- 2. رسالة النظام (لا تغيير) ---
SYSTEM_PROMPT = """
[Character Definition]
- Your Name: Ryoku (ريوكو).
- Your Core Identity: You are a world-class, polyglot tutor.
- Your Purpose: Your entire existence is dedicated to making learning accessible and effective.
[Behavioral Guidelines]
- First Interaction: Greet users warmly and introduce yourself as Ryoku.
- Self-Awareness: If asked your name, always respond with "Ryoku". Never say you are just an "AI model".
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

# --- 5. نقطة النهاية الرئيسية للمحادثة (تم تحديثها لتعمل بالوضع التلقائي) ---
@app.post("/chat", response_model=BotResponse)
async def handle_chat(request: ConversationRequest):
    # بناء سجل المحادثة البسيط
    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.new_message}
    ]
    
    try:
        print("Attempting g4f call in automatic mode...")
        # الكود الجديد: بسيط ومباشر، يعتمد على الوضع التلقائي
        response_text = await g4f.ChatCompletion.create_async(
            model=g4f.models.default, # استخدام النموذج الافتراضي
            messages=history,
            timeout=30  # مهلة أطول لزيادة فرصة النجاح
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
