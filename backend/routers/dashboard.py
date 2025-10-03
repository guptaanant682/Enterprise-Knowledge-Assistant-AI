from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import User, Document, ChatMessage
from schemas import DashboardStats, RecentQuery
from auth_utils import get_current_user

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    try:
        # Total queries
        total_queries = db.query(ChatMessage).count()
        
        # Documents count
        documents_count = db.query(Document).count()
        
        # Active users (users who sent messages in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = db.query(ChatMessage.user_id).filter(
            ChatMessage.created_at >= thirty_days_ago
        ).distinct().count()
        
        # Average response time
        avg_response_time = db.query(
            func.avg(ChatMessage.response_time)
        ).filter(
            ChatMessage.response_time.isnot(None)
        ).scalar() or 0
        
        return DashboardStats(
            totalQueries=total_queries,
            documentsCount=documents_count,
            activeUsers=active_users,
            avgResponseTime=round(avg_response_time, 2)
        )
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )

@router.get("/recent-queries", response_model=List[RecentQuery])
async def get_recent_queries(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent queries across all users"""
    try:
        recent_queries = db.query(
            ChatMessage.message.label('question'),
            User.name.label('user_name'),
            ChatMessage.created_at
        ).join(
            User, ChatMessage.user_id == User.id
        ).order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        
        return [
            RecentQuery(
                question=query.question[:100] + "..." if len(query.question) > 100 else query.question,
                user_name=query.user_name,
                created_at=query.created_at
            )
            for query in recent_queries
        ]
        
    except Exception as e:
        print(f"Error getting recent queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent queries"
        )

@router.get("/user-activity")
async def get_user_activity(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity over time"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query messages by day
        activity = db.query(
            func.date(ChatMessage.created_at).label('date'),
            func.count(ChatMessage.id).label('message_count'),
            func.count(func.distinct(ChatMessage.user_id)).label('active_users')
        ).filter(
            ChatMessage.created_at >= start_date
        ).group_by(
            func.date(ChatMessage.created_at)
        ).order_by('date').all()
        
        return [
            {
                "date": str(day.date),
                "message_count": day.message_count,
                "active_users": day.active_users
            }
            for day in activity
        ]
        
    except Exception as e:
        print(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )

@router.get("/popular-topics")
async def get_popular_topics(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get most popular discussion topics"""
    try:
        # This is a simplified version - in a real implementation,
        # you might use NLP to extract topics from messages
        
        # For now, we'll return categories of documents that are most referenced
        popular_docs = db.query(
            Document.category,
            func.count(Document.id).label('count')
        ).group_by(
            Document.category
        ).order_by(
            func.count(Document.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "topic": doc.category.title(),
                "count": doc.count
            }
            for doc in popular_docs
        ]
        
    except Exception as e:
        print(f"Error getting popular topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular topics"
        )

@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health metrics"""
    try:
        # Check database connectivity
        db_health = "healthy"
        try:
            db.execute("SELECT 1")
        except:
            db_health = "unhealthy"
        
        # Check if we have recent activity
        recent_activity = db.query(ChatMessage).filter(
            ChatMessage.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        # Simple health scoring
        health_score = 100
        if db_health != "healthy":
            health_score -= 50
        
        return {
            "overall_health": "healthy" if health_score > 70 else "degraded" if health_score > 30 else "unhealthy",
            "health_score": health_score,
            "database_status": db_health,
            "recent_activity": recent_activity,
            "uptime": "Available",  # In a real system, you'd track actual uptime
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        )