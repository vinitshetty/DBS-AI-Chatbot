"""
Intent Router - Classifies user intent and routes to appropriate handler
Uses: Mistral function calling for structured intent extraction
Falls back to keyword matching if LLM unavailable
"""

from typing import Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class IntentRouter:
    """
    Intelligent intent classification and routing
    
    Features:
    - LLM-based classification (Mistral function calling)
    - Keyword-based fallback
    - Context-aware classification
    - Entity extraction
    """
    
    def __init__(self):
        # Define intent taxonomy with examples and keywords
        self.intents = {
            "faq": {
                "description": "General questions about banking services, hours, fees, products",
                "examples": [
                    "What are your opening hours?",
                    "Tell me about credit cards",
                    "What are the fees?",
                    "Where is the nearest branch?"
                ],
                "keywords": ["hour", "open", "close", "timing", "fee", "charge", "cost", 
                           "product", "service", "branch", "atm", "location", "interest rate"]
            },
            "check_balance": {
                "description": "Check account balance or view account information",
                "examples": [
                    "What's my balance?",
                    "Show my accounts",
                    "How much money do I have?"
                ],
                "keywords": ["balance", "how much", "account", "money", "check account"]
            },
            "transaction_history": {
                "description": "View past transactions and account statements",
                "examples": [
                    "Show recent transactions",
                    "What did I spend on?",
                    "Transaction history"
                ],
                "keywords": ["transaction", "history", "statement", "spent", "purchase", 
                           "recent", "last month"]
            },
            "transfer_funds": {
                "description": "Transfer money between accounts or to other people",
                "examples": [
                    "Transfer $500 to savings",
                    "Send money to John",
                    "Move funds to checking"
                ],
                "keywords": ["transfer", "send money", "move", "pay", "wire"]
            },
            "lock_card": {
                "description": "Lock or unlock credit/debit card",
                "examples": [
                    "Lock my card",
                    "I lost my credit card",
                    "Freeze my card",
                    "Unlock my card"
                ],
                "keywords": ["lock", "unlock", "freeze", "block", "lost", "stolen", 
                           "found card", "unblock", "card"]
            },
            "pay_bill": {
                "description": "Pay bills or set up recurring payments",
                "examples": [
                    "Pay my electricity bill",
                    "Set up auto-pay",
                    "Bill payment"
                ],
                "keywords": ["pay bill", "payment", "auto-pay", "recurring", "utilities"]
            },
            "general_query": {
                "description": "Other banking-related questions or requests",
                "examples": [
                    "How do I change my PIN?",
                    "Update my address",
                    "Cancel a transaction"
                ],
                "keywords": ["change", "update", "cancel", "modify", "help"]
            }
        }
    
    async def classify(self, message: str, context: Dict) -> Dict:
        """
        Classify user intent using LLM or fallback to keyword matching
        
        Args:
            message: User's input message
            context: Conversation context
            
        Returns:
            Dict with intent, confidence, and extracted entities
        """
        try:
            # Try LLM-based classification first
            from llm_core.mistral_client import MistralClient
            
            mistral = MistralClient()
            result = await mistral.classify_intent(
                message=message,
                intents=list(self.intents.keys()),
                context=self._build_context_string(message, context)
            )
            
            logger.info(f"LLM classification: {result['intent']} "
                       f"(confidence: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {str(e)}. Using fallback.")
            # Fallback to keyword-based classification
            return self._keyword_classify(message, context)
    
    def _keyword_classify(self, message: str, context: Dict) -> Dict:
        """
        Fallback keyword-based classification
        Uses pattern matching and keyword scoring
        """
        msg_lower = message.lower()
        
        # Score each intent based on keyword matches
        scores = {}
        for intent_name, intent_info in self.intents.items():
            score = 0
            keywords = intent_info.get("keywords", [])
            
            for keyword in keywords:
                if keyword in msg_lower:
                    # Exact keyword match
                    score += 1
                    
                    # Bonus for keyword at start of message
                    if msg_lower.startswith(keyword):
                        score += 0.5
            
            scores[intent_name] = score
        
        # Find highest scoring intent
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            intent_name, score = best_intent
            
            if score > 0:
                # Normalize confidence (max out at 3 keywords = 0.9 confidence)
                confidence = min(0.5 + (score * 0.15), 0.95)
                
                # Extract entities
                entities = self._extract_entities(message, intent_name)
                
                logger.info(f"Keyword classification: {intent_name} "
                          f"(confidence: {confidence:.2f}, score: {score})")
                
                return {
                    "intent": intent_name,
                    "confidence": confidence,
                    "entities": entities,
                    "method": "keyword"
                }
        
        # Default to general_query if no matches
        logger.info("No strong keyword matches, defaulting to general_query")
        return {
            "intent": "general_query",
            "confidence": 0.50,
            "entities": {},
            "method": "default"
        }
    
    def _extract_entities(self, message: str, intent: str) -> Dict:
        """
        Extract relevant entities from message based on intent
        
        Entities might include:
        - Amounts (money values)
        - Account numbers
        - Card numbers (last 4 digits)
        - Dates
        - Recipient names
        """
        entities = {}
        
        # Extract monetary amounts
        amount_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, message)
        if amounts:
            entities["amount"] = amounts[0].replace(',', '')
        
        # Extract last 4 digits (card numbers)
        card_pattern = r'\b\d{4}\b'
        card_matches = re.findall(card_pattern, message)
        if card_matches:
            entities["card_last_four"] = card_matches[0]
        
        # Extract account types
        account_types = ["savings", "checking", "current", "credit"]
        msg_lower = message.lower()
        for acc_type in account_types:
            if acc_type in msg_lower:
                entities["account_type"] = acc_type
                break
        
        # Extract dates (simple patterns)
        date_keywords = ["today", "yesterday", "last week", "last month"]
        for date_kw in date_keywords:
            if date_kw in msg_lower:
                entities["date_reference"] = date_kw
                break
        
        return entities
    
    def _build_context_string(self, message: str, context: Dict) -> str:
        """
        Build a context string for LLM classification
        Includes conversation history and state
        """
        parts = [f"Current message: {message}"]
        
        if context.get("last_intent"):
            parts.append(f"Previous intent: {context['last_intent']}")
        
        if context.get("transaction_state"):
            parts.append("User is in the middle of a transaction")
        
        if context.get("message_count", 0) > 1:
            parts.append(f"Message {context['message_count']} in conversation")
        
        return " | ".join(parts)
    
    def get_intent_description(self, intent_name: str) -> Optional[str]:
        """Get human-readable description of an intent"""
        intent_info = self.intents.get(intent_name)
        return intent_info.get("description") if intent_info else None
    
    def get_intent_examples(self, intent_name: str) -> Optional[List[str]]:
        """Get example phrases for an intent"""
        intent_info = self.intents.get(intent_name)
        return intent_info.get("examples") if intent_info else None
    
    def validate_intent_transition(
        self, 
        previous_intent: Optional[str], 
        new_intent: str
    ) -> bool:
        """
        Validate if intent transition makes sense
        Can be used to detect context switches
        """
        # Allow any transition for now
        # In production, you might want to enforce certain flows
        # e.g., transfer_funds -> confirm_transfer -> complete_transfer
        return True