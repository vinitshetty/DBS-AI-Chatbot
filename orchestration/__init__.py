"""
Orchestration Layer - Coordinates conversation flow, intent routing, and context management
"""

# Import classes only when explicitly requested to avoid circular imports
def __getattr__(name):
    if name == 'ConversationManager':
        from orchestration.conversation_manager import ConversationManager
        return ConversationManager
    elif name == 'ConversationSession':
        from orchestration.conversation_manager import ConversationSession
        return ConversationSession
    elif name == 'IntentRouter':
        from orchestration.intent_router import IntentRouter
        return IntentRouter
    elif name == 'ResponseGenerator':
        from orchestration.response_generator import ResponseGenerator
        return ResponseGenerator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'ConversationManager',
    'ConversationSession',
    'IntentRouter',
    'ResponseGenerator'
]