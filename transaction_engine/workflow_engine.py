"""
Transaction Workflow Engine - State machine for multi-step transactions
Handles: Validation, Confirmation, Execution, Rollback
"""

import logging
from typing import Dict, Optional
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """Transaction state machine states"""
    INITIATED = "initiated"
    VALIDATED = "validated"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class TransactionType(Enum):
    """Supported transaction types"""
    LOCK_CARD = "lock_card"
    UNLOCK_CARD = "unlock_card"
    TRANSFER_FUNDS = "transfer_funds"
    PAY_BILL = "pay_bill"
    UPDATE_LIMITS = "update_limits"


class Transaction:
    """Transaction data model"""
    def __init__(self, tx_id: str, tx_type: TransactionType, user_id: str, initiated_at: datetime):
        self.tx_id = tx_id
        self.tx_type = tx_type
        self.user_id = user_id
        self.state = TransactionState.INITIATED
        self.params: Optional[Dict] = None
        self.reference: Optional[str] = None
        self.error: Optional[str] = None
        self.initiated_at = initiated_at
        self.completed_at: Optional[datetime] = None


class TransactionEngine:
    """
    Transaction workflow engine with state machine
    
    Features:
    - Multi-step transaction flows
    - Validation and confirmation
    - Fraud detection integration
    - Audit logging
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        from transaction_engine.validators import TransactionValidator
        from transaction_engine.core_banking_client import CoreBankingClient
        from security.fraud_detector import FraudDetector
        from security.audit_logger import AuditLogger
        
        self.validator = TransactionValidator()
        self.core_banking = CoreBankingClient()
        self.fraud_detector = FraudDetector()
        self.audit = AuditLogger()
        
        # In-memory transaction store (use Redis in production)
        self.transactions: Dict[str, Transaction] = {}
    
    async def initiate(
        self,
        intent: str,
        message: str,
        user_context: Dict,
        session: 'ConversationSession'
    ) -> Dict:
        """
        Initiate a transaction workflow
        
        Args:
            intent: User intent (lock_card, transfer_funds, etc.)
            message: Original user message
            user_context: Authenticated user context
            session: Conversation session
            
        Returns:
            Dict with transaction status and message
        """
        try:
            # Create transaction
            tx_id = str(uuid.uuid4())
            tx_type = self._map_intent_to_type(intent)
            
            transaction = Transaction(
                tx_id=tx_id,
                tx_type=tx_type,
                user_id=user_context["user_id"],
                initiated_at=datetime.now()
            )
            
            self.transactions[tx_id] = transaction
            
            # Extract parameters from message
            params = await self._extract_parameters(message, tx_type, user_context)
            transaction.params = params
            
            # Validate transaction
            validation_result = await self.validator.validate(
                tx_type.value,  # Pass string value instead of enum
                params, 
                user_context
            )
            
            if not validation_result["valid"]:
                transaction.state = TransactionState.FAILED
                transaction.error = validation_result["error"]
                return {
                    "message": f"Unable to process: {validation_result['error']}",
                    "error": True
                }
            
            transaction.state = TransactionState.VALIDATED
            
            # Fraud check
            fraud_result = await self.fraud_detector.check(transaction, user_context)
            if fraud_result["is_suspicious"]:
                transaction.state = TransactionState.FAILED
                transaction.error = "Transaction blocked due to suspicious activity"
                
                # Alert security
                await self.audit.log_security_alert(
                    user_id=user_context["user_id"],
                    transaction_id=tx_id,
                    reason=fraud_result["reason"]
                )
                
                return {
                    "message": "This transaction has been flagged for review. Please contact customer support.",
                    "blocked": True
                }
            
            # Request confirmation
            transaction.state = TransactionState.PENDING_CONFIRMATION
            confirmation_message = self._generate_confirmation_message(transaction)
            
            return {
                "message": confirmation_message,
                "requires_confirmation": True,
                "transaction_id": tx_id,
                "metadata": {
                    "type": tx_type.value,
                    "params": params
                }
            }
            
        except Exception as e:
            logger.error(f"Transaction initiation failed: {str(e)}", exc_info=True)
            return {
                "message": "Unable to initiate transaction. Please try again.",
                "error": True
            }
    
    async def execute(
        self,
        transaction_type: str,
        params: Dict,
        user_context: Dict
    ) -> Dict:
        """
        Execute confirmed transaction
        
        Args:
            transaction_type: Type of transaction
            params: Transaction parameters including transaction_id
            user_context: User context
            
        Returns:
            Dict with execution result
        """
        try:
            tx_id = params.get("transaction_id")
            transaction = self.transactions.get(tx_id)
            
            if not transaction:
                raise ValueError("Transaction not found")
            
            if transaction.state != TransactionState.PENDING_CONFIRMATION:
                raise ValueError(f"Invalid transaction state: {transaction.state}")
            
            transaction.state = TransactionState.EXECUTING
            
            # Execute via core banking
            result = await self._execute_core_banking(transaction)
            
            if result["success"]:
                transaction.state = TransactionState.COMPLETED
                transaction.completed_at = datetime.now()
                transaction.reference = result["reference"]
                
                # Audit log
                await self.audit.log_transaction(
                    user_id=user_context["user_id"],
                    transaction=transaction,
                    result="success"
                )
                
                success_message = self._generate_success_message(transaction, result)
                
                return {
                    "success": True,
                    "message": success_message,
                    "reference": result["reference"],
                    "transaction_id": tx_id
                }
            else:
                transaction.state = TransactionState.FAILED
                transaction.error = result.get("error", "Unknown error")
                
                return {
                    "success": False,
                    "message": f"Transaction failed: {transaction.error}",
                    "error": True
                }
                
        except Exception as e:
            logger.error(f"Transaction execution failed: {str(e)}", exc_info=True)
            if transaction:
                transaction.state = TransactionState.FAILED
            return {
                "success": False,
                "message": "Transaction could not be completed. Please try again.",
                "error": True
            }
    
    async def _extract_parameters(
        self,
        message: str,
        tx_type: TransactionType,
        user_context: Dict
    ) -> Dict:
        """Extract transaction parameters from message"""
        # Use LLM to extract structured data
        if tx_type == TransactionType.LOCK_CARD:
            return await self._extract_card_params(message, user_context)
        elif tx_type == TransactionType.TRANSFER_FUNDS:
            return await self._extract_transfer_params(message, user_context)
        else:
            return {}
    
    async def _extract_card_params(self, message: str, user_context: Dict) -> Dict:
        """Extract card locking parameters"""
        # Get user's cards from core banking
        user_data = await self.core_banking.get_user_cards(user_context["user_id"])
        
        # If user has multiple cards, need to ask which one
        if len(user_data["cards"]) > 1:
            return {
                "needs_clarification": True,
                "available_cards": user_data["cards"]
            }
        else:
            return {
                "card_id": user_data["cards"][0]["id"]
            }
    
    async def _extract_transfer_params(self, message: str, user_context: Dict) -> Dict:
        """Extract fund transfer parameters"""
        # In production, use Mistral function calling for entity extraction
        return {
            "amount": 1000.0,
            "from_account": "savings",
            "to_account": "checking"
        }
    
    def _map_intent_to_type(self, intent: str) -> TransactionType:
        """Map intent string to transaction type enum"""
        mapping = {
            "lock_card": TransactionType.LOCK_CARD,
            "unlock_card": TransactionType.UNLOCK_CARD,
            "transfer_funds": TransactionType.TRANSFER_FUNDS,
            "pay_bill": TransactionType.PAY_BILL
        }
        return mapping.get(intent, TransactionType.LOCK_CARD)
    
    def _generate_confirmation_message(self, transaction: Transaction) -> str:
        """Generate human-readable confirmation message"""
        if transaction.tx_type == TransactionType.LOCK_CARD:
            return (
                f"You're about to lock your card. This will:\n"
                f"• Prevent all new transactions\n"
                f"• Block ATM withdrawals\n"
                f"• Stop online purchases\n\n"
                f"You can unlock it anytime. Proceed?"
            )
        elif transaction.tx_type == TransactionType.TRANSFER_FUNDS:
            params = transaction.params
            return (
                f"Confirm transfer:\n"
                f"• Amount: SGD {params.get('amount', 0):,.2f}\n"
                f"• From: {params.get('from_account', 'N/A')}\n"
                f"• To: {params.get('to_account', 'N/A')}\n\n"
                f"Proceed with this transfer?"
            )
        return "Please confirm this transaction."
    
    def _generate_success_message(self, transaction: Transaction, result: Dict) -> str:
        """Generate success message"""
        if transaction.tx_type == TransactionType.LOCK_CARD:
            return (
                f"✅ Success! Your card has been locked.\n\n"
                f"Reference: {result['reference']}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Next steps:\n"
                f"• Unlock anytime via app\n"
                f"• Request replacement if lost\n"
                f"• Call 1800-111-1111 to report fraud"
            )
        return f"✅ Transaction completed successfully.\nReference: {result['reference']}"
    
    async def _execute_core_banking(self, transaction: Transaction) -> Dict:
        """Execute transaction via core banking API"""
        if transaction.tx_type == TransactionType.LOCK_CARD:
            return await self.core_banking.lock_card(
                user_id=transaction.user_id,
                card_id=transaction.params.get("card_id", "")
            )
        elif transaction.tx_type == TransactionType.TRANSFER_FUNDS:
            return await self.core_banking.transfer_funds(
                user_id=transaction.user_id,
                **transaction.params
            )
        return {"success": False, "error": "Unsupported transaction type"}