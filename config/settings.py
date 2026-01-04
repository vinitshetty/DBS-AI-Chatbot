import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DBS AI Chatbot"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Gateway
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RATE_LIMIT: int = 100  # requests per minute
    
    # Mistral API
    MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
    MISTRAL_MODEL: str = "mistral-large-latest"
    MISTRAL_TEMPERATURE: float = 0.3
    MISTRAL_MAX_TOKENS: int = 1024
    
    # ChromaDB (Vector Store)
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "dbs_knowledge"
    os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # RAG Configuration
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.7
    
    # Redis (Session Store)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    SESSION_TTL: int = 1800  # 30 minutes
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 30
    
    # Core Banking (Mock)
    CORE_BANKING_URL: str = "http://localhost:9000"
    CORE_BANKING_TIMEOUT: int = 10
    
    # Fraud Detection
    FRAUD_VELOCITY_LIMIT: int = 3  # max transactions per hour
    FRAUD_AMOUNT_THRESHOLD: float = 10000.0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/chatbot.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()