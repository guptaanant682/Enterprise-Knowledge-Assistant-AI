from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import User, Document, ChatMessage, AuditLog
from schemas import User as UserSchema, AdminUserUpdate, AdminStats
from auth_utils import get_current_admin_user, get_current_user

router = APIRouter()

@router.get("/users", response_model=List[UserSchema])
async def get_all_users(
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    try:
        users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
        return users
        
    except Exception as e:
        print(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from demoting themselves
        if user_id == current_admin.id and user_update.role == "user":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself"
            )
        
        # Update user fields
        if user_update.role is not None:
            user.role = user_update.role
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        db.commit()
        db.refresh(user)
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="user_updated",
            resource_type="user",
            resource_id=str(user_id),
            details={
                "updated_fields": user_update.dict(exclude_unset=True),
                "target_user": user.email
            }
        )
        db.add(audit_log)
        db.commit()
        
        return {"message": "User updated successfully", "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from deleting themselves
        if user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself"
            )
        
        # Log the action before deletion
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="user_deleted",
            resource_type="user",
            resource_id=str(user_id),
            details={
                "deleted_user": {
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                }
            }
        )
        db.add(audit_log)
        
        # Delete user (this will cascade to related records)
        db.delete(user)
        db.commit()
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/documents")
async def get_all_documents(
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all documents with uploader info (admin only)"""
    try:
        documents = db.query(
            Document.id,
            Document.title,
            Document.filename,
            Document.file_size,
            Document.category,
            Document.created_at,
            User.name.label('uploader_name'),
            User.email.label('uploader_email')
        ).outerjoin(
            User, Document.uploaded_by == User.id
        ).order_by(Document.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": doc.id,
                "title": doc.title,
                "filename": doc.filename,
                "file_size": doc.file_size,
                "category": doc.category,
                "created_at": doc.created_at,
                "uploader_name": doc.uploader_name,
                "uploader_email": doc.uploader_email
            }
            for doc in documents
        ]
        
    except Exception as e:
        print(f"Error getting documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.delete("/documents/{document_id}")
async def admin_delete_document(
    document_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete document (admin only)"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Log the action
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="document_deleted",
            resource_type="document",
            resource_id=str(document_id),
            details={
                "document_title": document.title,
                "document_filename": document.filename
            }
        )
        db.add(audit_log)
        
        # Remove from vector database
        from services.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService(db)
        await knowledge_service.delete_document_from_vector_db(document_id)
        
        # Delete file from disk
        from services.file_service import FileService
        file_service = FileService()
        file_service.delete_file(document.file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

@router.get("/analytics", response_model=AdminStats)
async def get_admin_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics (admin only)"""
    try:
        # Basic counts
        total_users = db.query(User).count()
        total_documents = db.query(Document).count()
        total_queries = db.query(ChatMessage).count()
        
        # Recent activity
        recent_activity = []
        
        # Recent user registrations
        recent_users = db.query(User).filter(
            User.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(User.created_at.desc()).limit(5).all()
        
        for user in recent_users:
            recent_activity.append({
                "description": f"New user registered: {user.name}",
                "timestamp": user.created_at.strftime("%Y-%m-%d %H:%M")
            })
        
        # Recent document uploads
        recent_docs = db.query(Document).filter(
            Document.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(Document.created_at.desc()).limit(5).all()
        
        for doc in recent_docs:
            recent_activity.append({
                "description": f"Document uploaded: {doc.title}",
                "timestamp": doc.created_at.strftime("%Y-%m-%d %H:%M")
            })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:10]
        
        return AdminStats(
            totalUsers=total_users,
            totalDocuments=total_documents,
            totalQueries=total_queries,
            recentActivity=recent_activity
        )
        
    except Exception as e:
        print(f"Error getting admin analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )

@router.get("/analytics/export")
async def export_analytics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export analytics to CSV (admin only)"""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import csv
        
        # Get comprehensive data
        users_data = db.query(User).all()
        documents_data = db.query(Document).all()
        messages_data = db.query(ChatMessage).all()
        
        # Create CSV content
        output = io.StringIO()
        
        # Write users data
        output.write("=== USERS ===\n")
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Email", "Department", "Role", "Active", "Created"])
        
        for user in users_data:
            writer.writerow([
                user.id, user.name, user.email, user.department,
                user.role, user.is_active, user.created_at
            ])
        
        output.write("\n=== DOCUMENTS ===\n")
        writer.writerow(["ID", "Title", "Category", "File Size", "Uploaded By", "Created"])
        
        for doc in documents_data:
            writer.writerow([
                doc.id, doc.title, doc.category, doc.file_size,
                doc.uploaded_by, doc.created_at
            ])
        
        output.write("\n=== CHAT MESSAGES ===\n")
        writer.writerow(["ID", "User ID", "Message Length", "Response Time", "Created"])
        
        for msg in messages_data:
            writer.writerow([
                msg.id, msg.user_id, len(msg.message),
                msg.response_time, msg.created_at
            ])
        
        output.seek(0)
        content = output.getvalue()
        
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_export.csv"}
        )
        
    except Exception as e:
        print(f"Error exporting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics"
        )

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs (admin only)"""
    try:
        logs = db.query(
            AuditLog.id,
            AuditLog.action,
            AuditLog.resource_type,
            AuditLog.resource_id,
            AuditLog.details,
            AuditLog.created_at,
            User.name.label('user_name'),
            User.email.label('user_email')
        ).outerjoin(
            User, AuditLog.user_id == User.id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "created_at": log.created_at,
                "user_name": log.user_name,
                "user_email": log.user_email
            }
            for log in logs
        ]
        
    except Exception as e:
        print(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )