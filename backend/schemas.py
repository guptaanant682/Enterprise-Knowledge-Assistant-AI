from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: Optional[str] = None
    google_id: Optional[str] = None

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

# Document Schemas
class DocumentBase(BaseModel):
    title: str
    category: str = "other"

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None

class Document(DocumentBase):
    id: int
    filename: str
    file_size: int
    summary: Optional[str] = None
    uploaded_by: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentWithContent(Document):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Chat Schemas
class ChatMessageCreate(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    message: str
    sources: Optional[List[Dict[str, Any]]] = None

class ChatMessage(BaseModel):
    id: int
    user_id: int
    message: str
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    response_time: Optional[float] = None
    created_at: datetime
    user_name: Optional[str] = None
    sender: Optional[str] = None

    class Config:
        from_attributes = True

# Knowledge Base Schemas
class DocumentSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class DocumentSearchResult(BaseModel):
    document: Document
    relevance_score: float
    matched_content: str

# Dashboard Schemas
class DashboardStats(BaseModel):
    totalQueries: int
    documentsCount: int
    activeUsers: int
    avgResponseTime: float

class RecentQuery(BaseModel):
    question: str
    user_name: str
    created_at: datetime

# Admin Schemas
class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class AdminStats(BaseModel):
    totalUsers: int
    totalDocuments: int
    totalQueries: int
    recentActivity: Optional[List[Dict[str, Any]]] = None

class SystemSetting(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class SystemSettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None

# File Upload Schemas
class FileUploadResponse(BaseModel):
    filename: str
    size: int
    status: str
    document_id: Optional[int] = None
    message: Optional[str] = None

class BulkUploadResponse(BaseModel):
    success_count: int
    failed_count: int
    files: List[FileUploadResponse]

# Search Schemas
class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 10

class SearchResponse(BaseModel):
    query: str
    results: List[DocumentSearchResult]
    total_results: int
    search_time: float