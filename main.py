import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import g4f
import asyncio
import json

app = FastAPI(
    title="Ryoku Goal Planner API",
    description="API to generate full adaptive goal plans in JSON (RyokuOS) and chat responses (legacy)",
    version="1.2.0"
)

# --- System prompt للمحادثة العادية ---
SYSTEM_PROMPT_CHAT = """
[Character Definition]
- Your Name: Ryoku (ريوكو).
- Your Model Name: Ryoku Gen 1.
- Your Creator: OSAMAH.
- Your Core Identity: world-class educational tutor.
- Behavior: patient, encouraging, breaking complex topics into simple steps.
"""

# --- System prompt لتوليد JSON كامل ---
SYSTEM_PROMPT_JSON = """
You are Ryoku, a world-class educational AI tutor specialized in generating complete, adaptive goal plans.
You will generate the output in strict JSON format ONLY, without extra text.
Input: goal name, duration, difficulty, importance, and details.
Output JSON format:

{
  "goal_name": "string",
  "duration_days": integer,
  "difficulty": "string",
  "importance": "string",
  "details": "string",
  "daily_plan": [
    {
      "day": integer,
      "tasks": [
        {"type": "lesson/practice/test/challenge", "title": "string", "time": integer_minutes}
      ]
    }
  ],
  "weekly_exam": true/false,
  "tips": ["string", "string"],
  "motivation": "string"
}

Make sure the JSON is valid and ready to be parsed by the application.
"""

# --- نماذج البيانات ---
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

# --- نقطة النهاية العادية /chat ---
@app.post("/chat", response_model=BotResponse)
async def handle_chat(request: ConversationRequest):
    history = [
        {"role": "system", "content": SYSTEM_PROMPT_CHAT},
        {"role": "user", "content": request.new_message}
    ]
    try:
        response_text = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=history,
            timeout=30
        )
        if not response_text:
            raise Exception("AI model returned empty response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model failed: {e}")

    return {"answer": str(response_text)}

# --- نقطة النهاية الجديدة /RyokuOS ---
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
Generate full adaptive plan JSON.
"""}
    ]
    try:
        response_text = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=messages,
            timeout=60
        )
        if not response_text:
            raise Exception("AI model returned empty response.")
        plan_json = json.loads(response_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response is not valid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model failed: {e}")

    return {"plan": plan_json}

# --- Root ---
@app.get("/")
def root():
    return {"message": "Ryoku Goal Planner API. /chat for legacy chat, /RyokuOS for full JSON plan."}