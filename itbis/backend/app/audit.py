
from app.models import AuditLog


def log_action(db, action, user_id=None, details=None):
    """Record a sensitive action in the audit log."""
    try:
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            details=details
        )

        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)

        return audit_entry

    except Exception:
        db.rollback()
        raise
