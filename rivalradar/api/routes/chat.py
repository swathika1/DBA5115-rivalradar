import os
import logging
from fastapi import APIRouter, Depends
from groq import Groq
from db.schemas import User
from api.models import ChatRequest, ChatResponse
from api.routes.auth import get_current_user

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are RivalRadar, an AI competitive intelligence assistant for VC portfolio managers and founders.
You help users understand competitor movements, portfolio risk, and strategic actions.
Be concise, data-driven, and board-level in tone."""


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: User = Depends(get_current_user)):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        # TODO: inject retrieved docs here (RAG hook)
        {"role": "user", "content": req.message},
    ]
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
        )
        reply = response.choices[0].message.content
    except Exception as exc:
        logger.error("Chat LLM error: %s", exc)
        reply = "I'm having trouble connecting to the AI. Please try again."
    return ChatResponse(reply=reply)
