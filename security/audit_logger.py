"""
Audit Logger - Compliance logging for all transactions and security events
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from transaction_engine.workflow_engine import Transaction

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self):
        self.audit_file = Path("logs/audit.log")
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_interaction(
        self,
        session_id: str,
        user_id: Optional[str],
        intent: str,
        message: str,
        response: str
    ):
        """Log user interaction"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "interaction",
            "session_id": session_id,
            "user_id": user_id,
            "intent": intent,
            "message_length": len(message),
            "response_length": len(response)
        }
        self._write_audit(audit_entry)
    
    async def log_transaction(
        self,
        user_id: str,
        transaction: 'Transaction',
        result: str
    ):
        """Log transaction execution"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "transaction",
            "user_id": user_id,
            "transaction_id": transaction.tx_id,
            "transaction_type": transaction.tx_type.value,
            "result": result,
            "reference": transaction.reference
        }
        self._write_audit(audit_entry)
    
    async def log_security_alert(
        self,
        user_id: str,
        transaction_id: str,
        reason: str
    ):
        """Log security alert"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "security_alert",
            "user_id": user_id,
            "transaction_id": transaction_id,
            "reason": reason,
            "severity": "high"
        }
        self._write_audit(audit_entry)
        
        # In production: Send to SIEM, alert SOC team
        logger.warning(f"SECURITY ALERT: {reason} - User: {user_id}")
    
    def _write_audit(self, entry: Dict):
        """Write audit entry to file"""
        with open(self.audit_file, "a") as f:
            f.write(json.dumps(entry) + "\n")