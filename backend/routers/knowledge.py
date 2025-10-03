from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database import get_db
from models import User, Document
from schemas import Document as DocumentSchema, DocumentSearchRequest, DocumentSearchResult
from auth_utils import get_current_user
from services.file_service import FileService
from services.knowledge_service import KnowledgeService
from services.ai_service import AIService

router = APIRouter()

@router.get("/documents", response_model=List[DocumentSchema])
async def get_documents(
    category: Optional[str] = None,
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents in knowledge base"""
    try:
        query = db.query(Document)
        
        if category and category != "all":
            query = query.filter(Document.category == category)
        
        documents = query.order_by(Document.created_at.desc()).limit(limit).all()
        return documents
        
    except Exception as e:
        print(f"Error getting documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form("other"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple documents to knowledge base"""
    try:
        file_service = FileService()
        knowledge_service = KnowledgeService(db)
        ai_service = AIService()
        
        # Validate category
        valid_categories = ["policy", "procedure", "manual", "guide", "other", "auto"]
        if category not in valid_categories:
            category = "other"
        
        results = []
        
        for file in files:
            try:
                # Save file
                file_result = await file_service.save_file(file)
                
                if not file_result["valid"]:
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "message": file_result["error"]
                    })
                    continue
                
                # Extract text content
                content = await file_service.extract_text(
                    file_result["file_path"],
                    file_result["content_type"]
                )
                
                if not content.strip():
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "message": "No text content could be extracted"
                    })
                    continue
                
                # Generate summary and auto-categorize (with fallback)
                try:
                    summary = await ai_service.generate_summary(content)
                except Exception as e:
                    print(f"Summary generation failed: {e}")
                    summary = "Summary not available"

                try:
                    auto_category = await ai_service.categorize_document(
                        file.filename, content
                    )
                except Exception as e:
                    print(f"Categorization failed: {e}")
                    auto_category = "other"

                # Use provided category or auto-detected
                final_category = category if category != "auto" else auto_category
                
                # Create document record
                document = Document(
                    title=os.path.splitext(file.filename)[0],
                    filename=file_result["filename"],
                    file_path=file_result["file_path"],
                    file_size=file_result["size"],
                    content=content,
                    summary=summary,
                    category=final_category,
                    uploaded_by=current_user.id
                )
                
                db.add(document)
                db.flush()  # Get document ID
                
                # Process for vector database
                chunks = knowledge_service.chunk_text(content)
                if chunks:
                    await knowledge_service.add_document_to_vector_db(document, chunks)
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "document_id": document.id,
                    "message": "Document uploaded successfully"
                })
                
            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "message": str(e)
                })
        
        db.commit()
        
        success_count = len([r for r in results if r["status"] == "success"])
        failed_count = len(results) - success_count
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "files": results
        }
        
    except Exception as e:
        import traceback
        print(f"Upload error: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload documents: {str(e)}"
        )

@router.get("/search")
async def search_documents(
    q: str,
    category: Optional[str] = None,
    limit: Optional[int] = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search documents using vector similarity"""
    try:
        knowledge_service = KnowledgeService(db)
        
        results = await knowledge_service.search_documents(
            query=q,
            limit=limit,
            category_filter=category
        )
        
        # Convert to response format
        documents = []
        for result in results:
            doc = db.query(Document).filter(Document.id == result["id"]).first()
            if doc:
                documents.append({
                    "id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "file_size": doc.file_size,
                    "summary": doc.summary,
                    "category": doc.category,
                    "created_at": doc.created_at,
                    "relevance_score": result["relevance_score"],
                    "matched_content": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                })
        
        return documents
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )

@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific document details"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "id": document.id,
            "title": document.title,
            "filename": document.filename,
            "file_size": document.file_size,
            "content": document.content,
            "summary": document.summary,
            "category": document.category,
            "uploaded_by": document.uploaded_by,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check permissions (admin or owner)
        if current_user.role != "admin" and document.uploaded_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Remove from vector database
        knowledge_service = KnowledgeService(db)
        await knowledge_service.delete_document_from_vector_db(document_id)
        
        # Delete file from disk
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

@router.get("/stats")
async def get_knowledge_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get knowledge base statistics"""
    try:
        knowledge_service = KnowledgeService(db)
        stats = await knowledge_service.get_document_stats()
        
        return stats
        
    except Exception as e:
        print(f"Error getting knowledge stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )

@router.get("/categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available document categories"""
    try:
        categories = db.query(Document.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return {
            "categories": category_list,
            "predefined": ["policy", "procedure", "manual", "guide", "other"]
        }
        
    except Exception as e:
        print(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )