"""
DBS AI Chatbot - Main Entry Point
"""

import uvicorn
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting DBS AI Chatbot...")
    
    # Ensure directories exist
    Path("data/chroma").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)
    Path("knowledge_base/documents").mkdir(parents=True, exist_ok=True)
    
    # Run FastAPI app
    uvicorn.run(
        "api_gateway.gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )