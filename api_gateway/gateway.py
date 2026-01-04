from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from config.settings import settings
from api_gateway.middleware import RateLimiter, AuthMiddleware
from orchestration.conversation_manager import ConversationManager
from security.auth_service import AuthService

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
conversation_manager = ConversationManager()
auth_service = AuthService()

# Rate Limiter
rate_limiter = RateLimiter(max_requests=settings.API_RATE_LIMIT, window_seconds=60)

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    from pathlib import Path
    html_file = Path("frontend/index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
    else:
        return JSONResponse(content={
            "service": settings.APP_NAME,
            "status": "operational",
            "message": "Frontend UI not yet created. Use /docs for API documentation"
        })
        
@app.get("/ops")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api_gateway": "up",
            "llm_core": "up",
            "vector_db": "up",
            "transaction_engine": "up"
        }
    }

@app.post("/api/v1/chat")
async def chat(request: Request):
    '''Main chat endpoint - routes through orchestration layer'''
    try:
        # Rate limiting
        client_ip = request.client.host
        if not rate_limiter.check_limit(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Parse request
        body = await request.json()
        message = body.get("message")
        session_id = body.get("session_id") or request.headers.get("X-Session-ID")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get authentication token
        auth_token = request.headers.get("Authorization")
        user_context = None
        if auth_token:
            user_context = auth_service.verify_token(auth_token)
        
        # Process through orchestration layer
        response = await conversation_manager.process_message(
            message=message,
            session_id=session_id,
            user_context=user_context
        )
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/login")
async def login(request: Request):
    '''Authenticate user and return JWT token'''
    body = await request.json()
    user_id = body.get("user_id")
    otp = body.get("otp")
    
    # Verify OTP
    if auth_service.verify_otp(user_id, otp):
        token = auth_service.create_token(user_id)
        return {"token": token, "user_id": user_id}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/v1/auth/request-otp")
async def request_otp(request: Request):
    '''Request OTP for authentication'''
    body = await request.json()
    user_id = body.get("user_id")
    
    otp = auth_service.generate_otp(user_id)
    # In production, send via SMS/Email
    logger.info(f"OTP for {user_id}: {otp}")
    
    return {"message": "OTP sent successfully"}

@app.post("/api/v1/transactions/execute")
async def execute_transaction(request: Request):
    '''Execute banking transaction'''
    # This endpoint requires authentication
    auth_token = request.headers.get("Authorization")
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_context = auth_service.verify_token(auth_token)
    body = await request.json()
    
    # Process through transaction engine
    from transaction_engine.workflow_engine import TransactionEngine
    tx_engine = TransactionEngine()
    
    result = await tx_engine.execute(
        transaction_type=body.get("type"),
        params=body.get("params"),
        user_context=user_context
    )
    
    return result

@app.get("/api/v1/documents/ingest")
async def ingest_documents():
    '''Trigger document ingestion into vector DB'''
    from knowledge_base.rag_engine import RAGEngine
    
    rag = RAGEngine()
    result = await rag.ingest_documents()
    
    return {"status": "success", "documents_processed": result}

# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize components
    from knowledge_base.vector_store import VectorStore
    vector_store = VectorStore()
    await vector_store.initialize()
    
    logger.info("All components initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down gracefully...")
    # Cleanup resources

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway.gateway:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )