from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int
    action: str
    target_user_id: int | None
    created_at: datetime
    details: str

    model_config = ConfigDict(from_attributes = True)