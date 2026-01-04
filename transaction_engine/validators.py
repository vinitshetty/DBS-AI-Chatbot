"""
Transaction Validators - Business rule validation
Validates transactions against business rules and constraints
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TransactionValidator:
    """
    Validates transactions against business rules
    
    Checks:
    - Amount limits
    - Account validity
    - Business constraints
    """
    
    def __init__(self):
        from config.settings import settings
        self.settings = settings
    
    async def validate(
        self,
        tx_type: str,  # Using string instead of enum to avoid circular import
        params: Dict,
        user_context: Dict
    ) -> Dict:
        """
        Validate transaction against business rules
        
        Args:
            tx_type: Transaction type as string
            params: Transaction parameters
            user_context: User context with authentication info
            
        Returns:
            Dict with validation result
        """
        
        if params.get("needs_clarification"):
            return {
                "valid": False,
                "error": "Please specify which card to lock"
            }
        
        # Validate based on transaction type
        if tx_type == "transfer_funds":
            return await self._validate_transfer(params, user_context)
        
        elif tx_type == "lock_card":
            return await self._validate_card_lock(params, user_context)
        
        elif tx_type == "pay_bill":
            return await self._validate_bill_payment(params, user_context)
        
        # Default: allow transaction
        return {"valid": True}
    
    async def _validate_transfer(self, params: Dict, user_context: Dict) -> Dict:
        """Validate fund transfer"""
        amount = params.get("amount", 0)
        
        # Check daily limit
        if amount > 50000:
            return {
                "valid": False,
                "error": "Transfer amount exceeds daily limit of SGD 50,000"
            }
        
        # Check minimum amount
        if amount <= 0:
            return {
                "valid": False,
                "error": "Transfer amount must be greater than zero"
            }
        
        # Validate accounts exist
        from_account = params.get("from_account")
        to_account = params.get("to_account")
        
        if not from_account or not to_account:
            return {
                "valid": False,
                "error": "Both source and destination accounts are required"
            }
        
        # Check sufficient balance (would query core banking in production)
        # For now, assume validation passes
        
        return {"valid": True}
    
    async def _validate_card_lock(self, params: Dict, user_context: Dict) -> Dict:
        """Validate card locking request"""
        card_id = params.get("card_id")
        
        if not card_id:
            return {
                "valid": False,
                "error": "Card ID is required"
            }
        
        # Check if card belongs to user (would verify with core banking)
        # For now, assume validation passes
        
        return {"valid": True}
    
    async def _validate_bill_payment(self, params: Dict, user_context: Dict) -> Dict:
        """Validate bill payment"""
        amount = params.get("amount", 0)
        payee = params.get("payee")
        
        if not payee:
            return {
                "valid": False,
                "error": "Payee information is required"
            }
        
        if amount <= 0:
            return {
                "valid": False,
                "error": "Payment amount must be greater than zero"
            }
        
        # Check daily payment limit
        if amount > 20000:
            return {
                "valid": False,
                "error": "Bill payment exceeds daily limit of SGD 20,000"
            }
        
        return {"valid": True}
    
    def validate_amount(self, amount: float, min_amount: float = 0, max_amount: float = None) -> Dict:
        """Validate transaction amount"""
        if amount <= min_amount:
            return {
                "valid": False,
                "error": f"Amount must be greater than {min_amount}"
            }
        
        if max_amount and amount > max_amount:
            return {
                "valid": False,
                "error": f"Amount exceeds maximum limit of {max_amount}"
            }
        
        return {"valid": True}