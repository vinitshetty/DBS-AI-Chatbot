"""
Response Generator - Formats responses in natural, conversational language
Handles templating, formatting, and response composition
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates natural language responses from structured data
    
    Features:
    - Template-based formatting
    - Dynamic content insertion
    - Tone adaptation
    - Multi-format support (text, structured data)
    """
    
    def __init__(self):
        # Response templates for different scenarios
        self.templates = {
            "balance": {
                "single": "Your {account_type} account (ending in {last_four}) has a balance of {currency} ${balance:,.2f}.",
                "multiple": "Here are your current account balances:\n\n{account_list}\n\nAll balances are updated in real-time."
            },
            "transaction_success": {
                "default": "✅ **Transaction Successful**\n\n{transaction_details}\n\nIs there anything else I can help you with?"
            },
            "card_locked": {
                "default": "✅ **Card Locked Successfully**\n\nYour {card_type} ending in {last_four} has been locked.\n\n**Reference:** {reference}\n**Time:** {timestamp}\n\n**Next Steps:**\n• Unlock anytime via the app\n• Request replacement if lost/stolen\n• Call 1800-111-1111 for fraud reporting"
            },
            "card_unlocked": {
                "default": "✅ **Card Unlocked**\n\nYour {card_type} ending in {last_four} is now active and ready to use.\n\n**Reference:** {reference}"
            },
            "transfer_complete": {
                "default": "✅ **Transfer Completed**\n\n**Amount:** {currency} ${amount:,.2f}\n**From:** {from_account}\n**To:** {to_account}\n**Reference:** {reference}\n**Time:** {timestamp}\n\nYour transfer has been processed successfully."
            },
            "error": {
                "generic": "I apologize, but I'm unable to process your request at the moment. Please try again or contact our support team.",
                "timeout": "The request took too long to process. Please try again.",
                "unauthorized": "For security, you need to authenticate before I can help with this request."
            }
        }
    
    async def format_account_info(self, account_data: Dict, original_query: str) -> str:
        """
        Format account information in a natural, readable way
        
        Args:
            account_data: Account information from core banking
            original_query: User's original query
            
        Returns:
            Formatted response string
        """
        try:
            accounts = account_data.get("accounts", [])
            
            if not accounts:
                return "I don't see any accounts associated with your profile. Please contact support if you believe this is an error."
            
            if len(accounts) == 1:
                # Single account - simple format
                acc = accounts[0]
                return self.templates["balance"]["single"].format(
                    account_type=acc.get("type", "Account"),
                    last_four=acc.get("number", "")[-4:],
                    currency=acc.get("currency", "SGD"),
                    balance=acc.get("balance", 0.0)
                )
            else:
                # Multiple accounts - list format
                account_lines = []
                for acc in accounts:
                    line = f"• **{acc['type']}** (****{acc['number'][-4:]}): {acc['currency']} ${acc['balance']:,.2f}"
                    account_lines.append(line)
                
                account_list = "\n".join(account_lines)
                return self.templates["balance"]["multiple"].format(
                    account_list=account_list
                )
                
        except Exception as e:
            logger.error(f"Error formatting account info: {str(e)}", exc_info=True)
            return "I found your accounts but had trouble formatting the information. Please try again."
    
    async def format_transaction_result(self, result: Dict) -> str:
        """
        Format transaction result with appropriate template
        
        Args:
            result: Transaction result from transaction engine
            
        Returns:
            Formatted response string
        """
        try:
            transaction_type = result.get("type", "transaction")
            
            # Select appropriate template
            if transaction_type == "card_lock":
                template = self.templates["card_locked"]["default"]
                return template.format(
                    card_type=result.get("card_type", "Card"),
                    last_four=result.get("last_four", "****"),
                    reference=result.get("reference", "N/A"),
                    timestamp=self._format_timestamp(result.get("timestamp"))
                )
            
            elif transaction_type == "card_unlock":
                template = self.templates["card_unlocked"]["default"]
                return template.format(
                    card_type=result.get("card_type", "Card"),
                    last_four=result.get("last_four", "****"),
                    reference=result.get("reference", "N/A")
                )
            
            elif transaction_type == "transfer":
                template = self.templates["transfer_complete"]["default"]
                return template.format(
                    currency=result.get("currency", "SGD"),
                    amount=result.get("amount", 0.0),
                    from_account=result.get("from_account", "Source"),
                    to_account=result.get("to_account", "Destination"),
                    reference=result.get("reference", "N/A"),
                    timestamp=self._format_timestamp(result.get("timestamp"))
                )
            
            else:
                # Generic success message
                details = self._format_transaction_details(result)
                return self.templates["transaction_success"]["default"].format(
                    transaction_details=details
                )
                
        except Exception as e:
            logger.error(f"Error formatting transaction result: {str(e)}", exc_info=True)
            return "Your transaction was processed, but I had trouble formatting the confirmation. Please check your account for details."
    
    def format_error(self, error_type: str = "generic", details: Optional[str] = None) -> str:
        """
        Format error messages in a user-friendly way
        
        Args:
            error_type: Type of error (generic, timeout, unauthorized)
            details: Optional additional details
            
        Returns:
            Formatted error message
        """
        base_message = self.templates["error"].get(error_type, 
                                                   self.templates["error"]["generic"])
        
        if details:
            return f"{base_message}\n\nDetails: {details}"
        
        return base_message
    
    def format_confirmation_request(self, action: str, details: Dict) -> str:
        """
        Format a confirmation request for user action
        
        Args:
            action: Action requiring confirmation
            details: Details about the action
            
        Returns:
            Formatted confirmation request
        """
        if action == "lock_card":
            return (
                f"⚠️ **Confirm Card Lock**\n\n"
                f"You're about to lock your {details.get('card_type', 'card')} "
                f"ending in {details.get('last_four', '****')}.\n\n"
                f"**This will:**\n"
                f"• Prevent all new transactions\n"
                f"• Block ATM withdrawals\n"
                f"• Stop online purchases\n\n"
                f"You can unlock it anytime through the app.\n\n"
                f"**Do you want to proceed?**"
            )
        
        elif action == "transfer":
            return (
                f"⚠️ **Confirm Transfer**\n\n"
                f"**Amount:** {details.get('currency', 'SGD')} ${details.get('amount', 0):,.2f}\n"
                f"**From:** {details.get('from_account', 'Source account')}\n"
                f"**To:** {details.get('to_account', 'Destination account')}\n\n"
                f"**Do you want to proceed with this transfer?**"
            )
        
        else:
            return (
                f"⚠️ **Confirmation Required**\n\n"
                f"Please confirm you want to proceed with this action.\n\n"
                f"**Details:** {details}"
            )
    
    def format_suggestion_list(self, suggestions: List[str]) -> str:
        """
        Format a list of suggestions for the user
        
        Args:
            suggestions: List of suggestion strings
            
        Returns:
            Formatted suggestion list
        """
        if not suggestions:
            return ""
        
        formatted = "💡 **You might want to:**\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            formatted += f"{i}. {suggestion}\n"
        
        return formatted
    
    def _format_transaction_details(self, result: Dict) -> str:
        """Format transaction details as a readable string"""
        details = []
        
        if result.get("reference"):
            details.append(f"**Reference:** {result['reference']}")
        
        if result.get("amount"):
            currency = result.get("currency", "SGD")
            details.append(f"**Amount:** {currency} ${result['amount']:,.2f}")
        
        if result.get("timestamp"):
            details.append(f"**Time:** {self._format_timestamp(result['timestamp'])}")
        
        return "\n".join(details) if details else "Transaction completed"
    
    def _format_timestamp(self, timestamp) -> str:
        """Format timestamp for display"""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return timestamp
        elif isinstance(timestamp, datetime):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def add_friendly_closing(self, message: str, intent: Optional[str] = None) -> str:
        """
        Add a friendly closing to the message
        
        Args:
            message: Main message content
            intent: Intent type for context-aware closing
            
        Returns:
            Message with appropriate closing
        """
        closings = {
            "faq": "\n\nIs there anything else you'd like to know?",
            "check_balance": "\n\nWould you like to know anything else about your accounts?",
            "transaction": "\n\nIs there anything else I can help you with today?",
            "default": "\n\nHow else can I assist you?"
        }
        
        closing = closings.get(intent, closings["default"])
        
        # Don't add closing if message already has a question
        if message.rstrip().endswith("?"):
            return message
        
        return message + closing