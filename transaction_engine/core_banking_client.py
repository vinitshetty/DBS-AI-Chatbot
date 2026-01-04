"""
Core Banking Client - Interface to core banking systems
Mock implementation for demo, replace with real APIs in production
"""

import logging
from typing import Dict, List
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class CoreBankingClient:
    """
    Mock core banking client
    In production: Replace with actual REST/SOAP API calls to core banking
    """
    
    # Mock user database
    MOCK_USERS = {
        "user_001": {
            "name": "Sarah Tan",
            "accounts": [
                {
                    "id": "acc_001",
                    "number": "1234567890",
                    "type": "Savings",
                    "balance": 15420.50,
                    "currency": "SGD"
                },
                {
                    "id": "acc_002",
                    "number": "0987654321",
                    "type": "Current",
                    "balance": 8250.00,
                    "currency": "SGD"
                }
            ],
            "cards": [
                {
                    "id": "card_001",
                    "type": "VISA Credit",
                    "last_four": "1234",
                    "status": "active"
                },
                {
                    "id": "card_002",
                    "type": "Mastercard Debit",
                    "last_four": "5678",
                    "status": "active"
                }
            ]
        }
    }
    
    async def get_account_info(self, user_id: str) -> Dict:
        """Get user account information"""
        await asyncio.sleep(0.1)  # Simulate API latency
        
        user_data = self.MOCK_USERS.get(user_id, {})
        return {
            "user_id": user_id,
            "accounts": user_data.get("accounts", [])
        }
    
    async def get_user_cards(self, user_id: str) -> Dict:
        """Get user's cards"""
        await asyncio.sleep(0.1)
        
        user_data = self.MOCK_USERS.get(user_id, {})
        return {
            "user_id": user_id,
            "cards": user_data.get("cards", [])
        }
    
    async def lock_card(self, user_id: str, card_id: str) -> Dict:
        """Lock a credit/debit card"""
        await asyncio.sleep(0.2)  # Simulate processing
        
        # In production: Make API call to core banking
        # POST /api/cards/{card_id}/lock
        
        reference = f"REF{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Card {card_id} locked for user {user_id}")
        
        return {
            "success": True,
            "reference": reference,
            "timestamp": datetime.now().isoformat()
        }
    
    async def transfer_funds(
        self,
        user_id: str,
        amount: float,
        from_account: str,
        to_account: str
    ) -> Dict:
        """Transfer funds between accounts"""
        await asyncio.sleep(0.3)
        
        reference = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Transfer: {amount} from {from_account} to {to_account}")
        
        return {
            "success": True,
            "reference": reference,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }