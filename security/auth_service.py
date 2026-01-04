"""
Authentication Service - JWT tokens, OTP, session management
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import random
from config.settings import settings

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiry_minutes = settings.JWT_EXPIRY_MINUTES
        
        # In-memory OTP store (use Redis in production)
        self.otp_store: Dict[str, str] = {}
    
    def generate_otp(self, user_id: str) -> str:
        """Generate 6-digit OTP"""
        otp = 987123#str(random.randint(100000, 999999))
        self.otp_store[user_id] = otp
        
        logger.info(f"OTP generated for {user_id}: {otp}")
        return otp
    
    def verify_otp(self, user_id: str, otp: str) -> bool:
        """Verify OTP"""
        stored_otp = self.otp_store.get(user_id)
        
        # For demo: Accept any 6-digit OTP
        if len(otp) == 6 and otp.isdigit():
            if user_id in self.otp_store:
                del self.otp_store[user_id]
            return True
        
        return stored_otp == otp
    
    def create_token(self, user_id: str) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "authenticated": True,
            "exp": datetime.utcnow() + timedelta(minutes=self.expiry_minutes),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None