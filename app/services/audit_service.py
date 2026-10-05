from sqlalchemy.orm import Session
from sqlalchemy import select,desc
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


def list_audit_logs(db: Session):
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at))
    audits = db.scalars(stmt).all()
    return audits