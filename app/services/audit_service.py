from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def create_audit_log(
        actor_user_id: int,
        action: str,
        target_user_id: int,
        details: str,
        db: Session
):
    audit_log = AuditLog(actor_user_id = actor_user_id, action = action, target_user_id = target_user_id, details = details)
    db.add(audit_log)
    return audit_log


