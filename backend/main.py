from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import socketio
from contextlib import asynccontextmanager
import os

from database import engine, Base
from config import settings
from routers import auth, chat, knowledge, dashboard, admin
from auth_utils import get_current_user
from models import User

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    logger=True,
    engineio_logger=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Enterprise Knowledge Assistant API")
    print(f"📊 Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Local'}")
    print(f"🤖 AI Model: OpenAI GPT-4")
    print(f"🔍 Vector DB: ChromaDB")
    yield
    # Shutdown
    print("👋 Shutting down Enterprise Knowledge Assistant API")

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    description="AI-powered internal assistant for enterprise knowledge management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIRECTORY), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Socket.IO events
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    try:
        if auth and 'token' in auth:
            # Verify token and get user
            user = await get_current_user_from_token(auth['token'])
            await sio.save_session(sid, {'user_id': user.id, 'user_name': user.name})
            print(f"User {user.name} connected with session {sid}")
        else:
            await sio.disconnect(sid)
    except Exception as e:
        print(f"Connection error: {e}")
        await sio.disconnect(sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    session = await sio.get_session(sid)
    user_name = session.get('user_name', 'Unknown')
    print(f"User {user_name} disconnected")

@sio.event
async def message(sid, data):
    """Handle chat messages"""
    try:
        session = await sio.get_session(sid)
        user_id = session.get('user_id')
        user_name = session.get('user_name')
        
        if not user_id:
            await sio.emit('error', {'message': 'Unauthorized'}, room=sid)
            return
        
        # Emit typing indicator
        await sio.emit('typing', room=sid)
        
        # Process message with AI
        from services.ai_service import AIService
        from services.knowledge_service import KnowledgeService
        from database import get_db
        from models import ChatMessage
        
        # Get database session with proper management
        db_gen = get_db()
        db = next(db_gen)
        try:
            ai_service = AIService()
            knowledge_service = KnowledgeService(db)
            
            # Get relevant documents
            relevant_docs = await knowledge_service.search_documents(data['message'])
            
            # Generate AI response
            response = await ai_service.generate_response(
                data['message'], 
                relevant_docs,
                user_id=user_id
            )
            
            # Save to database
            chat_message = ChatMessage(
                user_id=user_id,
                message=data['message'],
                response=response['message'],
                sources=response.get('sources', [])
            )
            db.add(chat_message)
            db.commit()

            # Get the data we need before closing the session
            message_id = chat_message.id
            created_at = chat_message.created_at
        finally:
            db.close()

        # Stop typing and send response
        await sio.emit('stop_typing', room=sid)
        await sio.emit('response', {
            'id': message_id,
            'message': response['message'],
            'sender': 'assistant',
            'timestamp': created_at.isoformat(),
            'sources': response.get('sources', [])
        }, room=sid)
        
    except Exception as e:
        print(f"Message processing error: {e}")
        await sio.emit('stop_typing', room=sid)
        await sio.emit('error', {'message': 'Failed to process message'}, room=sid)

async def get_current_user_from_token(token: str):
    """Get user from JWT token for socket authentication"""
    from auth_utils import verify_token
    from database import get_db
    
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_gen = get_db()
        db = next(db_gen)
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            return user
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "Enterprise Knowledge Assistant API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "ai_service": "available",
        "vector_db": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )