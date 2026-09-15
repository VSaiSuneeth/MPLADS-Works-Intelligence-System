from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AuditLogOut(BaseModel):
    id: str
    userId: Optional[str] = Field(None, alias="user_id")
    userName: str = Field(..., alias="user_name")
    action: str
    entityType: str = Field(..., alias="entity_type")
    entityId: Optional[str] = Field(None, alias="entity_id")
    detailsJson: Dict[str, Any] = Field(default_factory=dict, alias="details_json")
    ipAddress: Optional[str] = Field(None, alias="ip_address")
    createdAt: datetime = Field(..., alias="created_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class AuditLogListResponse(BaseModel):
    items: List[AuditLogOut]
    page: int
    pageSize: int
    total: int
