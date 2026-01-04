"""
Mistral API Client - Handles all LLM interactions
Supports: Chat completion, Function calling, Mock mode for testing
"""

import os
import logging
from typing import Dict, List, Optional, Union

from mistralai.models.chat_completion import ChatMessage

logger = logging.getLogger(__name__)

class MistralClient:
    def __init__(self):
        from config.settings import settings
        
        self.api_key = settings.MISTRAL_API_KEY or os.getenv("MISTRAL_API_KEY")
        self.model = settings.MISTRAL_MODEL
        self.temperature = settings.MISTRAL_TEMPERATURE
        self.max_tokens = settings.MISTRAL_MAX_TOKENS
        
        # Initialize Mistral client if API key available
        if self.api_key and self.api_key != "your_mistral_api_key_here":
            try:
                from mistralai.client import MistralClient as MistralAI
                self.client = MistralAI(api_key=self.api_key)
                logger.info("Mistral API client initialized")
            except Exception as e:
                logger.warning(f"Mistral API initialization failed: {e}. Using mock mode.")
                self.client = None
        else:
            logger.warning("MISTRAL_API_KEY not set - using mock responses")
            self.client = None
    
    async def generate_response(
        self,
        message: str,
        context_documents: List[Dict] = None,
        conversation_history: List[Dict] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response using Mistral API with RAG context
        Falls back to mock responses if API unavailable
        """
        try:
            if not self.client:
                return self._mock_response(message, context_documents)
            
            # Build messages for Mistral
            messages = self._build_messages(
                message, 
                context_documents, 
                conversation_history,
                system_prompt
            )
            
            # Call Mistral API
            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Mistral API error: {str(e)}", exc_info=True)
            return self._mock_response(message, context_documents)
    
    async def classify_intent(
        self,
        message: str,
        intents: List[str],
        context: str = None
    ) -> Dict:
        """Classify intent - fallback to keyword matching"""
        try:
            if not self.client:
                return self._mock_intent(message, intents)
            
            # Simple prompt-based classification (no function calling)
            prompt = f"Classify this banking query into one of these intents: {', '.join(intents)}\n\nQuery: {message}\n\nIntent:"
            
            response = self.client.chat(
                model=self.model,
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.1,
                max_tokens=50
            )
            
            intent_text = response.choices[0].message.content.strip().lower()
            
            # Find matching intent
            for intent in intents:
                if intent in intent_text:
                    return {"intent": intent, "confidence": 0.85, "entities": {}}
            
            # Fallback to keyword
            return self._mock_intent(message, intents)
                
        except Exception as e:
            logger.error(f"Intent classification error: {str(e)}")
            return self._mock_intent(message, intents)
    
    def _build_messages(
        self,
        message: str,
        context_docs: Optional[List[Dict]],
        history: Optional[List[Dict]],
        system_prompt: Optional[str]
    ) -> List:
        """Build message array for Mistral API"""
        messages = []
        
        # System prompt
        if not system_prompt:
            from llm_core.prompts import BANKING_SYSTEM_PROMPT
            system_prompt = BANKING_SYSTEM_PROMPT
        
        messages.append(ChatMessage(role="system", content=system_prompt))
        
        # Add conversation history (last 6 messages)
        if history:
            for msg in history[-6:]:
                messages.append(ChatMessage(
                    role=msg["role"],
                    content=msg["content"]
                ))
        
        # Add RAG context if available
        if context_docs:
            context_text = self._format_context(context_docs)
            messages.append(ChatMessage(
                role="system",
                content=f"Relevant information:\\n\\n{context_text}"
            ))
        
        # Current message
        messages.append(ChatMessage(role="user", content=message))
        
        return messages
    
    def _format_context(self, docs: List[Dict]) -> str:
        """Format retrieved documents as context"""
        parts = []
        for i, doc in enumerate(docs, 1):
            content = doc.get('content', '')
            source = doc.get('metadata', {}).get('source', 'Unknown')
            parts.append(f"[{i}] {content}\\n(Source: {source})")
        return "\\n\\n".join(parts)
    
    def _mock_response(self, message: str, context_docs: Optional[List[Dict]] = None) -> str:
        """
        Mock response when API unavailable
        Uses context from RAG if available
        """
        msg_lower = message.lower()
        
        # If we have context documents, use them
        if context_docs and len(context_docs) > 0:
            # Extract content from first document
            content = context_docs[0].get('content', '')
            if content:
                # Return a summary of the context
                summary = content[:300] + "..." if len(content) > 300 else content
                return f"Based on our knowledge base: {summary}\\n\\nIs there anything specific you'd like to know?"
        
        # Fallback to keyword-based responses
        if "balance" in msg_lower:
            return "Your accounts:\\n• Savings (****7890): SGD 15,420.50\\n• Current (****4321): SGD 8,250.00\\n\\nAll balances updated in real-time."
        
        elif any(word in msg_lower for word in ["hour", "open", "timing"]):
            return "Most DBS branches are open:\\n• Mon-Fri: 9:30 AM - 4:30 PM\\n• Saturday: 9:30 AM - 12:30 PM\\n• Sunday: Closed\\n\\nATMs available 24/7."
        
        elif any(word in msg_lower for word in ["fee", "charge", "cost"]):
            return "DBS account fees:\\n• Savings: No fee if balance above SGD 3,000\\n• Credit cards: SGD 0-642 annually (varies by card)\\n• Many fees waived for qualifying customers."
        
        elif any(word in msg_lower for word in ["transfer", "limit"]):
            return "Daily transfer limits:\\n• Own accounts: SGD 50,000\\n• DBS/POSB: SGD 30,000\\n• Other banks: SGD 20,000\\n\\nHigher limits available at branches."
        
        elif "lock" in msg_lower or "card" in msg_lower:
            return "You can lock your card instantly through:\\n• DBS digibank mobile app\\n• Online banking\\n• This chatbot\\n• Call 1800-111-1111\\n\\nLocking prevents all transactions but you can unlock anytime."
        
        else:
            return "I'm running in demo mode (MISTRAL_API_KEY not configured). I can help with:\\n• Account balances\\n• Opening hours\\n• Fees and limits\\n• Card management\\n\\nWhat would you like to know?"
    
    def _mock_intent(self, message: str, intents: List[str]) -> Dict:
        """Mock intent classification using keywords"""
        msg_lower = message.lower()
        
        if "balance" in msg_lower:
            return {"intent": "check_balance", "confidence": 0.90, "entities": {}}
        elif any(word in msg_lower for word in ["lock", "freeze", "block", "lost", "stolen"]):
            return {"intent": "lock_card", "confidence": 0.88, "entities": {}}
        elif "transfer" in msg_lower or "send money" in msg_lower:
            return {"intent": "transfer_funds", "confidence": 0.85, "entities": {}}
        elif any(word in msg_lower for word in ["transaction", "history", "statement"]):
            return {"intent": "transaction_history", "confidence": 0.82, "entities": {}}
        elif any(word in msg_lower for word in ["pay", "bill", "payment"]):
            return {"intent": "pay_bill", "confidence": 0.80, "entities": {}}
        elif any(word in msg_lower for word in ["hour", "open", "fee", "charge", "limit"]):
            return {"intent": "faq", "confidence": 0.75, "entities": {}}
        else:
            return {"intent": "general_query", "confidence": 0.60, "entities": {}}