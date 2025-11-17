"""API endpoints for conversational AI chat interface."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
import json

from database import get_db
from config import settings
from ai.gemini_service import gemini_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat completion."""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat."""
    message: str
    conversation_id: str
    suggestions: Optional[List[str]] = None


@router.post("/{engagement_id}/chat", response_model=ChatResponse)
async def chat(
    engagement_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with AI assistant about valuation.
    
    The AI can:
    - Answer questions about the financials
    - Adjust valuation assumptions
    - Run sensitivity analysis
    - Explain calculations
    """
    try:
        # Get engagement context
        context = await _get_engagement_context(engagement_id, db)
        
        # Get conversation history
        conversation_id = request.conversation_id or _generate_conversation_id()
        history = await _get_conversation_history(conversation_id, db)
        
        # Generate AI response
        response = await gemini_service.chat_response(
            user_message=request.message,
            context=context,
            conversation_history=history
        )
        
        # Save messages to database
        await _save_message(conversation_id, "user", request.message, db)
        await _save_message(conversation_id, "assistant", response, db)
        
        # Generate helpful suggestions
        suggestions = _generate_suggestions(request.message, context)
        
        return ChatResponse(
            message=response,
            conversation_id=conversation_id,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{engagement_id}/chat/stream")
async def chat_stream(
    engagement_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Stream chat response for better UX.
    
    Returns Server-Sent Events (SSE) stream.
    """
    async def event_generator():
        try:
            # Get context
            context = await _get_engagement_context(engagement_id, db)
            conversation_id = request.conversation_id or _generate_conversation_id()
            history = await _get_conversation_history(conversation_id, db)
            
            # Generate response (streaming)
            response = await gemini_service.chat_response(
                user_message=request.message,
                context=context,
                conversation_history=history
            )
            
            # Stream response word by word for demo
            # In production, you'd use Gemini's streaming API
            words = response.split()
            for i, word in enumerate(words):
                chunk = {
                    "type": "content",
                    "content": word + (" " if i < len(words) - 1 else ""),
                    "conversation_id": conversation_id
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Simulate streaming
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            # Save to database
            await _save_message(conversation_id, "user", request.message, db)
            await _save_message(conversation_id, "assistant", response, db)
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            error_chunk = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/{engagement_id}/chat/conversations/{conversation_id}")
async def get_conversation(
    engagement_id: str,
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get full conversation history."""
    try:
        history = await _get_conversation_history(conversation_id, db)
        
        return {
            "conversation_id": conversation_id,
            "messages": history,
            "engagement_id": engagement_id
        }
        
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/{engagement_id}/chat/conversations")
async def list_conversations(
    engagement_id: str,
    db: Session = Depends(get_db)
):
    """List all conversations for an engagement."""
    try:
        # TODO: Query conversations from database
        
        return {
            "conversations": [],
            "total": 0
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

async def _get_engagement_context(engagement_id: str, db: Session) -> dict:
    """Get engagement context for AI."""
    # TODO: Query from database
    # Include: company info, financials, valuation, assumptions
    
    return {
        "engagement_id": engagement_id,
        "company_name": "Example Corp",
        "industry": "SaaS",
        "financials": {
            "revenue": [1000000, 1500000, 2000000],
            "years": [2021, 2022, 2023]
        },
        "valuation": {
            "enterprise_value": 50000000,
            "wacc": 0.12,
            "terminal_growth": 0.03
        }
    }


async def _get_conversation_history(conversation_id: str, db: Session) -> List[dict]:
    """Get conversation history from database."""
    # TODO: Query from database
    
    return []


async def _save_message(
    conversation_id: str,
    role: str,
    content: str,
    db: Session
):
    """Save message to database."""
    # TODO: Insert into database
    pass


def _generate_conversation_id() -> str:
    """Generate unique conversation ID."""
    from uuid import uuid4
    return str(uuid4())


def _generate_suggestions(message: str, context: dict) -> List[str]:
    """Generate helpful follow-up suggestions."""
    # Simple rule-based suggestions
    # In production, use AI to generate contextual suggestions
    
    suggestions = [
        "What happens if revenue growth is 20% instead?",
        "Show me sensitivity analysis on WACC",
        "Explain the DCF calculation",
        "What are the key value drivers?"
    ]
    
    return suggestions[:3]
