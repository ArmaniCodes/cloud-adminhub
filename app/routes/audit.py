from fastapi import APIRouter, Depends
from app.schemas.audit import AuditLogResponse
from app.security.auth import require_role
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.audit_service import list_audit_logs
router = APIRouter()

@router.get('/audit-logs', response_model= list[AuditLogResponse])
def get_audit_logs(
    _admin = Depends(require_role('admin'))
    , db: Session = Depends(get_db)
):
    return list_audit_logs(db)