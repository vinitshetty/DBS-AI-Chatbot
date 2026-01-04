"""
Transaction Engine - Handles banking transactions with state machine workflow
Manages transaction validation, execution, and core banking integration
"""

# Import classes only when explicitly requested to avoid circular imports
def __getattr__(name):
    if name == 'TransactionEngine':
        from transaction_engine.workflow_engine import TransactionEngine
        return TransactionEngine
    elif name == 'Transaction':
        from transaction_engine.workflow_engine import Transaction
        return Transaction
    elif name == 'TransactionState':
        from transaction_engine.workflow_engine import TransactionState
        return TransactionState
    elif name == 'TransactionType':
        from transaction_engine.workflow_engine import TransactionType
        return TransactionType
    elif name == 'TransactionValidator':
        from transaction_engine.validators import TransactionValidator
        return TransactionValidator
    elif name == 'CoreBankingClient':
        from transaction_engine.core_banking_client import CoreBankingClient
        return CoreBankingClient
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'TransactionEngine',
    'Transaction',
    'TransactionState',
    'TransactionType',
    'TransactionValidator',
    'CoreBankingClient'
]