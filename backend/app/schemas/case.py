from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CaseActionCreate(BaseModel):
    actionType: str = Field(..., alias="action_type")
    newStatus: Optional[str] = Field(None, alias="new_status")
    assignedToId: Optional[str] = Field(None, alias="assigned_to_id")
    notes: str

    model_config = ConfigDict(populate_by_name=True)

class CaseActionOut(BaseModel):
    id: str
    caseId: str = Field(..., alias="case_id")
    actorId: Optional[str] = Field(None, alias="actor_id")
    actorName: str
    actionType: str = Field(..., alias="action_type")
    previousStatus: Optional[str] = Field(None, alias="previous_status")
    newStatus: Optional[str] = Field(None, alias="new_status")
    notes: str
    createdAt: datetime = Field(..., alias="created_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class CaseCreate(BaseModel):
    workId: str = Field(..., alias="work_id")
    priority: str = "HIGH"
    summary: str
    initialNotes: Optional[str] = Field(None, alias="initial_notes")

    model_config = ConfigDict(populate_by_name=True)

class CaseOut(BaseModel):
    id: str
    caseNumber: str = Field(..., alias="case_number")
    workId: str = Field(..., alias="work_id")
    workExternalId: str
    workTitle: str
    status: str
    priority: str
    summary: str
    createdByName: str
    assignedToId: Optional[str] = Field(None, alias="assigned_to_id")
    assignedToName: Optional[str] = Field(None, alias="assigned_to_name")
    createdAt: datetime = Field(..., alias="created_at")
    updatedAt: datetime = Field(..., alias="updated_at")
    actions: List[CaseActionOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class CaseListResponse(BaseModel):
    items: List[CaseOut]
    page: int
    pageSize: int
    total: int
