from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import time

from database import get_db
from models import User, ChatMessage
from schemas import ChatMessageCreate, ChatMessageResponse, ChatMessage as ChatMessageSchema
from auth_utils import get_current_user
from services.ai_service import AIService
from services.knowledge_service import KnowledgeService

router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response"""
    try:
        start_time = time.time()
        
        # Initialize services
        ai_service = AIService()
        knowledge_service = KnowledgeService(db)
        
        # Search for relevant documents
        relevant_docs = await knowledge_service.search_documents(
            message_data.message,
            limit=5
        )
        
        # Generate AI response
        response = await ai_service.generate_response(
            message_data.message,
            relevant_docs,
            user_id=current_user.id
        )
        
        response_time = time.time() - start_time
        
        # Save to database
        chat_message = ChatMessage(
            user_id=current_user.id,
            message=message_data.message,
            response=response["message"],
            sources=response.get("sources", []),
            response_time=response_time
        )
        
        db.add(chat_message)
        db.commit()
        
        return ChatMessageResponse(
            message=response["message"],
            sources=response.get("sources", [])
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.get("/history", response_model=List[ChatMessageSchema])
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat history"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        # Convert to response format
        chat_history = []
        for msg in reversed(messages):  # Reverse to show oldest first
            # Add user message
            chat_history.append({
                "id": msg.id * 10 + 1,  # Create unique ID for user message
                "user_id": msg.user_id,
                "message": msg.message,
                "response": msg.message,  # For user messages, response = message
                "sources": [],
                "response_time": None,
                "timestamp": msg.created_at.isoformat(),
                "created_at": msg.created_at,
                "user_name": current_user.name,
                "sender": "user"
            })

            # Add assistant response
            chat_history.append({
                "id": msg.id,
                "user_id": msg.user_id,
                "message": msg.response,
                "response": msg.response,
                "sources": msg.sources or [],
                "response_time": msg.response_time,
                "timestamp": msg.created_at.isoformat(),
                "created_at": msg.created_at,
                "user_name": "Assistant",
                "sender": "assistant"
            })
        
        return chat_history
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )

@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear user's chat history"""
    try:
        db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        return {"message": "Chat history cleared successfully"}
        
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear chat history"
        )

@router.get("/stats")
async def get_chat_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chat statistics"""
    try:
        total_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).count()
        
        # Get average response time
        avg_response_time = db.query(
            func.avg(ChatMessage.response_time)
        ).filter(
            ChatMessage.user_id == current_user.id,
            ChatMessage.response_time.isnot(None)
        ).scalar() or 0
        
        return {
            "total_messages": total_messages,
            "average_response_time": round(avg_response_time, 2)
        }
        
    except Exception as e:
        print(f"Error getting chat stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat statistics"
        )