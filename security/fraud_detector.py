"""
Fraud Detection - Anomaly detection and risk scoring
"""

import logging
from typing import Dict
from datetime import datetime, timedelta
from collections import defaultdict
from config.settings import settings
from transaction_engine.workflow_engine import Transaction

logger = logging.getLogger(__name__)

class FraudDetector:
    def __init__(self):
        # Track transaction velocity per user
        self.user_transactions = defaultdict(list)
        
        self.velocity_limit = settings.FRAUD_VELOCITY_LIMIT
        self.amount_threshold = settings.FRAUD_AMOUNT_THRESHOLD
    
    async def check(self, transaction: 'Transaction', user_context: Dict) -> Dict:
        """
        Check transaction for fraud indicators
        Returns: {"is_suspicious": bool, "reason": str, "score": float}
        """
        risk_score = 0.0
        reasons = []
        
        user_id = user_context["user_id"]
        
        # Check 1: Velocity - too many transactions in short time
        recent_txs = self._get_recent_transactions(user_id, hours=1)
        if len(recent_txs) >= self.velocity_limit:
            risk_score += 0.4
            reasons.append("High transaction velocity")
        
        # Check 2: Amount - unusually large amount
        if transaction.params.get("amount", 0) > self.amount_threshold:
            risk_score += 0.3
            reasons.append("Large transaction amount")
        
        # Check 3: Location (would check IP geolocation in production)
        # For demo, skip this check
        
        # Check 4: Device fingerprint (in production)
        # For demo, skip this check
        
        # Record this transaction
        self.user_transactions[user_id].append({
            "timestamp": datetime.now(),
            "transaction_id": transaction.tx_id
        })
        
        is_suspicious = risk_score >= 0.5
        
        if is_suspicious:
            logger.warning(f"Suspicious transaction detected: {transaction.tx_id}")
        
        return {
            "is_suspicious": is_suspicious,
            "reason": "; ".join(reasons) if reasons else "No issues detected",
            "risk_score": risk_score
        }
    
    def _get_recent_transactions(self, user_id: str, hours: int = 1) -> list:
        """Get transactions from last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        return [
            tx for tx in self.user_transactions.get(user_id, [])
            if tx["timestamp"] > cutoff
        ]