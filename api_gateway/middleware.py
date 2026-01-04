from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_limit(self, identifier: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        self.requests[identifier].append(now)
        return True

class AuthMiddleware:
    @staticmethod
    def verify_token(token: str) -> dict:
        from security.auth_service import AuthService
        auth = AuthService()
        return auth.verify_token(token)