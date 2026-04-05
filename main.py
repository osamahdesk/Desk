import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import g4f
import asyncio
import json
import re
from collections import defaultdict

app = FastAPI(
    title="Ryoku Goal Planner API",
    description="API to generate full adaptive goal plans in JSON (RyokuOS) and chat responses (legacy)",
    version="2.0.0"
)

# --- Templates setup ---
templates = Jinja2Templates(directory="templates")  # folder containing index.html

# --- Store conversation history per user ---
user_conversations = defaultdict(list)
MAX_HISTORY = 20  # Keep last 20 messages per user

# --- System prompts ---
SYSTEM_PROMPT_CHAT = """
[Character Definition]
- Your Name: Ryoku (ريوكو).
- Your Model Name: Ryoku Gen 1.
- Your Creator: OSAMAH.
- Your Core Identity: World-class AI goal planner and educational tutor.
[Your Capabilities]
- Create detailed study plans and goal schedules
- Give exam preparation strategies
- Provide motivational coaching
- Help break down complex goals into daily tasks
- Answer educational questions on any topic
- Give productivity and time management tips
[Behavior Rules]
- Be patient, encouraging, and specific in your answers
- Break complex topics into simple, actionable steps
- When asked about planning, recommend using the Goals tab in the app
- Always be helpful and give real, useful advice — never generic responses
- If the user shares their goal context, reference it in your responses
- Keep responses concise but informative (2-4 paragraphs max)
- Use bullet points and numbered lists for clarity
- You can respond in Arabic or English based on the user's language
"""

SYSTEM_PROMPT_JSON = """
You are Ryoku, a world-class educational AI tutor specialized in generating complete, adaptive goal plans.
You MUST generate the output in strict JSON format ONLY, without any extra text, markdown, or code blocks.
Do NOT wrap the JSON in ```json``` or any other formatting. Output ONLY the raw JSON object.
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
  "tips": ["string", "string", "string"],
  "motivation": "string"
}
Rules:
- Generate a task list for EVERY day from day 1 to duration_days
- Each day should have 2-5 tasks depending on difficulty
- Task types: lesson (learning), practice (exercises), test (quizzes), challenge (boss challenges)
- Make task titles specific to the goal, not generic
- Tips should be actionable and specific to the goal
- Motivation should be personal and inspiring
- Output ONLY valid JSON, no extra text
"""

# --- Data models ---
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

# --- Helper function ---
def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{.*\}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if '```' in pattern else match.group(0))
            except (json.JSONDecodeError, IndexError):
                continue
    raise ValueError("Could not extract valid JSON from response")

# --- Chat endpoint ---
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

# --- JSON plan endpoint ---
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
Generate the complete adaptive plan as raw JSON only. No markdown, no extra text.
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
        plan_json = extract_json(str(response_text))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Could not parse AI response as JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI model failed: {e}")
    return {"plan": plan_json}

# --- Documentation endpoint ---
@app.get("/doc", response_class=HTMLResponse)
async def read_documentation(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Clear chat history ---
@app.delete("/chat/{user_id}")
async def clear_chat(user_id: str):
    if user_id in user_conversations:
        del user_conversations[user_id]
    return {"message": f"Chat history cleared for {user_id}"}

# --- Root ---
@app.get("/")
def root():
    return {
        "message": "Ryoku Goal Planner API v2.0",
        "endpoints": {
            "/chat": "POST - Chat with Ryoku (with conversation history)",
            "/RyokuOS": "POST - Generate full goal plan as JSON",
            "/chat/{user_id}": "DELETE - Clear chat history",
            "/doc": "GET - HTML documentation page"
        }
    }