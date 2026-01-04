"""
Conversation Manager - Orchestrates the entire conversation flow
Manages: Session, Context, Intent Routing, Response Generation
"""

import uuid
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Main orchestrator for conversation flow
    
    Coordinates:
    - Session management
    - Intent classification and routing
    - Response generation
    - Context tracking
    - Audit logging
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        from orchestration.intent_router import IntentRouter
        from orchestration.response_generator import ResponseGenerator
        from security.audit_logger import AuditLogger
        
        self.intent_router = IntentRouter()
        self.response_generator = ResponseGenerator()
        self.audit = AuditLogger()
        
        # In-memory session store (use Redis in production)
        self.sessions: Dict[str, 'ConversationSession'] = {}
    
    async def process_message(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Main orchestration method - coordinates entire conversation flow
        
        Flow:
        1. Get/Create session
        2. Update context with new message
        3. Route intent
        4. Generate response (FAQ vs Transaction)
        5. Update session
        6. Audit log
        
        Args:
            message: User's input message
            session_id: Optional session identifier
            user_context: Optional authenticated user context
            
        Returns:
            Dict with response, intent, metadata
        """
        try:
            # Step 1: Session Management
            if not session_id:
                session_id = str(uuid.uuid4())
            
            session = self.sessions.get(session_id)
            if not session:
                session = ConversationSession(session_id, user_context)
                self.sessions[session_id] = session
            
            # Step 2: Update Context
            session.add_message("user", message)
            
            # Step 3: Intent Classification
            intent_result = await self.intent_router.classify(
                message=message,
                context=session.get_context()
            )
            
            logger.info(f"Intent classified: {intent_result['intent']} "
                       f"(confidence: {intent_result['confidence']:.2f})")
            
            # Step 4: Route & Generate Response based on intent
            if intent_result["intent"] in ["faq", "general_query"]:
                response = await self._handle_faq(message, session)
            
            elif intent_result["intent"] in ["check_balance", "transaction_history"]:
                response = await self._handle_account_query(message, session, user_context)
            
            elif intent_result["intent"] in ["transfer_funds", "lock_card", "pay_bill"]:
                response = await self._handle_transaction(
                    intent_result["intent"], 
                    message, 
                    session, 
                    user_context
                )
            
            else:
                response = await self._handle_fallback(message, session)
            
            # Step 5: Update Session
            session.add_message("assistant", response["message"])
            session.last_intent = intent_result["intent"]
            
            # Step 6: Audit Logging
            self.audit.log_interaction(
                session_id=session_id,
                user_id=user_context.get("user_id") if user_context else None,
                intent=intent_result["intent"],
                message=message,
                response=response["message"]
            )
            
            return {
                "session_id": session_id,
                "message": response["message"],
                "intent": intent_result["intent"],
                "confidence": intent_result["confidence"],
                "requires_auth": response.get("requires_auth", False),
                "requires_confirmation": response.get("requires_confirmation", False),
                "metadata": response.get("metadata", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in conversation processing: {str(e)}", exc_info=True)
            return {
                "session_id": session_id or str(uuid.uuid4()),
                "message": "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_faq(self, message: str, session: 'ConversationSession') -> Dict:
        """
        Handle FAQ queries using RAG (Retrieval Augmented Generation)
        
        Process:
        1. Retrieve relevant documents from vector store
        2. Generate response using LLM + RAG context
        3. Return response with sources
        """
        try:
            from knowledge_base.rag_engine import RAGEngine
            from llm_core.mistral_client import MistralClient
            
            rag = RAGEngine()
            mistral = MistralClient()
            
            # Retrieve relevant documents
            context_docs = await rag.retrieve(query=message, top_k=3)
            
            logger.info(f"Retrieved {len(context_docs)} documents for context")
            
            # Generate response using LLM + RAG context
            response = await mistral.generate_response(
                message=message,
                context_documents=context_docs,
                conversation_history=session.get_history()
            )
            
            return {
                "message": response,
                "sources": [doc.get("metadata", {}).get("source", "Unknown") for doc in context_docs],
                "type": "faq"
            }
            
        except Exception as e:
            logger.error(f"FAQ handling error: {str(e)}", exc_info=True)
            return {
                "message": "I can help with general banking questions. What would you like to know about accounts, cards, transfers, or branch services?",
                "type": "faq"
            }
    
    async def _handle_account_query(
        self, 
        message: str, 
        session: 'ConversationSession',
        user_context: Optional[Dict]
    ) -> Dict:
        """
        Handle account-related queries (balance, transactions)
        Requires authentication
        """
        if not user_context or not user_context.get("authenticated"):
            return {
                "message": "To check your account information, I need to verify your identity first. Please authenticate to continue.",
                "requires_auth": True,
                "type": "account_query"
            }
        
        try:
            from transaction_engine.core_banking_client import CoreBankingClient
            
            banking = CoreBankingClient()
            account_data = await banking.get_account_info(user_context["user_id"])
            
            # Generate natural language response
            response = await self.response_generator.format_account_info(
                account_data, 
                message
            )
            
            return {
                "message": response,
                "type": "account_query"
            }
            
        except Exception as e:
            logger.error(f"Account query error: {str(e)}", exc_info=True)
            return {
                "message": "I'm having trouble retrieving your account information. Please try again in a moment.",
                "type": "account_query",
                "error": True
            }
    
    async def _handle_transaction(
        self,
        intent: str,
        message: str,
        session: 'ConversationSession',
        user_context: Optional[Dict]
    ) -> Dict:
        """
        Handle transactional intents (transfers, card locking, bill payments)
        Requires authentication and may require confirmation
        """
        if not user_context or not user_context.get("authenticated"):
            return {
                "message": "For security, I need to verify your identity before processing any transactions. Please authenticate first.",
                "requires_auth": True,
                "type": "transaction"
            }
        
        try:
            from transaction_engine.workflow_engine import TransactionEngine
            
            tx_engine = TransactionEngine()
            result = await tx_engine.initiate(
                intent=intent,
                message=message,
                user_context=user_context,
                session=session
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Transaction handling error: {str(e)}", exc_info=True)
            return {
                "message": "I'm unable to process this transaction at the moment. Please try again or visit a branch for assistance.",
                "type": "transaction",
                "error": True
            }
    
    async def _handle_fallback(self, message: str, session: 'ConversationSession') -> Dict:
        """
        Fallback handler for unrecognized or ambiguous intents
        Provides helpful guidance to user
        """
        return {
            "message": (
                "I'm not quite sure how to help with that. Here's what I can do:\n\n"
                "💰 **Account Services**\n"
                "• Check your balance and transaction history\n"
                "• View account details\n\n"
                "💳 **Card Management**\n"
                "• Lock or unlock your cards\n"
                "• Report lost or stolen cards\n\n"
                "💸 **Transactions**\n"
                "• Transfer funds between accounts\n"
                "• Pay bills\n\n"
                "❓ **Information**\n"
                "• Branch hours and locations\n"
                "• Fees and limits\n"
                "• Product information\n\n"
                "What would you like to do?"
            ),
            "fallback": True,
            "type": "fallback"
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session"""
        session = self.sessions.get(session_id)
        if session:
            return {
                "session_id": session.session_id,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "last_intent": session.last_intent
            }
        return None


class ConversationSession:
    """
    Manages conversation state and context for a single session
    
    Tracks:
    - Message history
    - User context (authentication state)
    - Transaction state
    - Intent history
    """
    
    def __init__(self, session_id: str, user_context: Optional[Dict] = None):
        self.session_id = session_id
        self.user_context = user_context or {}
        self.messages: List[Dict] = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.last_intent: Optional[str] = None
        self.transaction_state: Optional[Dict] = None
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now()
        logger.debug(f"Session {self.session_id}: Added {role} message")
    
    def get_history(self, last_n: int = 10) -> List[Dict]:
        """Get last N messages from history"""
        return self.messages[-last_n:] if self.messages else []
    
    def get_context(self) -> Dict:
        """Get current session context for intent classification"""
        return {
            "session_id": self.session_id,
            "user_context": self.user_context,
            "last_intent": self.last_intent,
            "message_count": len(self.messages),
            "transaction_state": self.transaction_state,
            "session_duration": (datetime.now() - self.created_at).total_seconds()
        }
    
    def update_user_context(self, updates: Dict):
        """Update user context (e.g., after authentication)"""
        self.user_context.update(updates)
        logger.info(f"Session {self.session_id}: Updated user context")
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        elapsed = datetime.now() - self.last_activity
        return elapsed.total_seconds() > (timeout_minutes * 60)