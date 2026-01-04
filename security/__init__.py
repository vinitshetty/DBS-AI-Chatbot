"""
Security Module - Authentication, fraud detection, and audit logging
Handles all security-related functionality for the chatbot
"""

# Import classes only when explicitly requested to avoid circular imports
def __getattr__(name):
    if name == 'AuthService':
        from security.auth_service import AuthService
        return AuthService
    elif name == 'FraudDetector':
        from security.fraud_detector import FraudDetector
        return FraudDetector
    elif name == 'AuditLogger':
        from security.audit_logger import AuditLogger
        return AuditLogger
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'AuthService',
    'FraudDetector',
    'AuditLogger'
]