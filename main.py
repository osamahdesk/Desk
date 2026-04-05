import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import g4f
import asyncio
import json
import re
from collections import defaultdict

# --- 1. إعداد التطبيق ---
app = FastAPI(
    title="Ryoku Goal Planner API",
    description="API to generate full adaptive goal plans in JSON (RyokuOS) and chat responses (legacy)",
    version="2.0.0"
)

# --- 2. Mount static and templates ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")  # ✅ هذا هو التغيير الوحيد

# --- 3. Store conversation history per user ---
user_conversations = defaultdict(list)
MAX_HISTORY = 20

# --- 4. System prompts ---
SYSTEM_PROMPT_CHAT = """[Character Definition]
- Your Name: Ryoku (ريوكو).
- Your Model Name: Ryoku Gen 1.
- Your Creator: OSAMAH.
- Your Core Identity: World-class AI goal planner and educational tutor.
[Behavior Rules]
- Be patient, encouraging, and specific in your answers
- Break complex topics into simple, actionable steps
"""

SYSTEM_PROMPT_JSON = """You are Ryoku, a world-class educational AI tutor specialized in generating complete, adaptive goal plans.
You MUST generate the output in strict JSON format ONLY, without any extra text, markdown, or code blocks.
"""

# --- 5. Data models ---
class ConversationRequest(BaseModel):
    user_id: str
    new_message: str

class GoalRequest(BaseModel):
    user_id: str
    goal_name: str
    duration_days: int
    difficulty: str
    importance: str
    details: str

class BotResponse(BaseModel):
    answer: str

class GoalPlanResponse(BaseModel):
    plan: dict

# --- 6. Helper: Extract JSON ---
def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    patterns = [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```', r'\{.*\}']
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if '```' in pattern else match.group(0))
            except (json.JSONDecodeError, IndexError):
                continue
    raise ValueError("Could not extract valid JSON from response")

# --- 7. Chat endpoint ---
@app.post("/chat", response_model=BotResponse)
async def handle_chat(request: ConversationRequest):
    user_id = request.user_id
    messages = [{"role": "system", "content": SYSTEM_PROMPT_CHAT}]
    history = user_conversations[user_id]
    messages.extend(history[-MAX_HISTORY:])
    messages.append({"role": "user", "content": request.new_message})
    try:
        response_text = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=messages,
            timeout=30
        )
        if not response_text:
            raise Exception("AI model returned empty response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model failed: {e}")

    user_conversations[user_id].append({"role": "user", "content": request.new_message})
    user_conversations[user_id].append({"role": "assistant", "content": str(response_text)})
    if len(user_conversations[user_id]) > MAX_HISTORY * 2:
        user_conversations[user_id] = user_conversations[user_id][-MAX_HISTORY:]
    return {"answer": str(response_text)}

# --- 8. JSON goal plan endpoint ---
@app.post("/RyokuOS", response_model=GoalPlanResponse)
async def generate_goal_plan(request: GoalRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_JSON},
        {"role": "user", "content": f"""
Goal Name: {request.goal_name}
Duration: {request.duration_days} days
Difficulty: {request.difficulty}
Importance: {request.importance}
Details: {request.details}
Generate the complete adaptive plan as raw JSON only.
"""}
    ]
    try:
        response_text = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=messages,
            timeout=60
        )
        plan_json = extract_json(str(response_text))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model failed: {e}")
    return {"plan": plan_json}

# --- 9. Documentation endpoint (/doc) ---
@app.get("/doc", response_class=HTMLResponse)
async def read_documentation(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- 10. Clear chat history ---
@app.delete("/chat/{user_id}")
async def clear_chat(user_id: str):
    if user_id in user_conversations:
        del user_conversations[user_id]
    return {"message": f"Chat history cleared for {user_id}"}

# --- 11. Root endpoint ---
@app.get("/")
def root():
    return {
        "message": "Ryoku Goal Planner API v2.0",
        "endpoints": {
            "/chat": "POST - Chat with Ryoku",
            "/RyokuOS": "POST - Generate goal plan as JSON",
            "/chat/{user_id}": "DELETE - Clear chat history",
            "/doc": "GET - HTML documentation page"
        }
    }