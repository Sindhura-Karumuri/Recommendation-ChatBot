import logging
from fastapi import APIRouter, HTTPException
from groq import RateLimitError
from backend.models.schemas import ChatRequest, ChatResponse, Recommendation
from backend.services.agent import chat

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list is empty")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        result = chat(messages)
    except RateLimitError:
        raise HTTPException(
            status_code=503,
            detail="All models are currently rate-limited. Please wait a few minutes and try again.",
        )
    except RuntimeError as e:
        if "rate" in str(e).lower():
            raise HTTPException(status_code=503, detail=str(e))
        logger.exception("Runtime error in /chat")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        logger.exception("Unhandled error in /chat")
        raise HTTPException(status_code=500, detail="Internal server error")

    return ChatResponse(
        reply=result["reply"],
        recommendations=[Recommendation(**r) for r in result["recommendations"]],
        end_of_conversation=result["end_of_conversation"],
    )
