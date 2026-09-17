from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import date, datetime

class AgencyOut(BaseModel):
    id: str
    name: str
    agencyType: Optional[str] = Field(None, validation_alias="agency_type")

    model_config = ConfigDict(from_attributes=True)

class JurisdictionOut(BaseModel):
    id: str
    stateName: str = Field(..., validation_alias="state_name")
    districtName: str = Field(..., validation_alias="district_name")
    districtCode: str = Field(..., validation_alias="district_code")

    model_config = ConfigDict(from_attributes=True)

class LifecycleEventOut(BaseModel):
    id: str
    eventType: str = Field(..., validation_alias="event_type")
    eventDate: Optional[date] = Field(None, validation_alias="event_date")
    status: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    isMissing: bool = Field(False, validation_alias="is_missing")

    model_config = ConfigDict(from_attributes=True)

class PaymentOut(BaseModel):
    id: str
    paymentReference: Optional[str] = Field(None, validation_alias="payment_reference")
    paymentDate: Optional[date] = Field(None, validation_alias="payment_date")
    amount: float
    paymentStatus: str = Field("COMPLETED", validation_alias="payment_status")

    model_config = ConfigDict(from_attributes=True)

class ProgressRecordOut(BaseModel):
    id: str
    progressPercent: float = Field(..., validation_alias="progress_percent")
    reportedDate: Optional[date] = Field(None, validation_alias="reported_date")
    statusText: Optional[str] = Field(None, validation_alias="status_text")

    model_config = ConfigDict(from_attributes=True)

from pydantic import field_validator

class FraudFlagOut(BaseModel):
    id: str
    evidenceId: str = Field(..., validation_alias="evidence_id")
    matchedEvidenceId: Optional[str] = Field(None, validation_alias="matched_evidence_id")
    matchedWorkId: Optional[str] = Field(None, validation_alias="matched_work_id")
    matchedWorkTitle: Optional[str] = None
    matchedWorkExternalId: Optional[str] = None
    flagType: str = Field(..., validation_alias="flag_type")
    severity: str
    confidenceScore: float = Field(..., validation_alias="confidence_score")
    distanceMeters: Optional[float] = Field(None, validation_alias="distance_meters")
    phashDistance: Optional[int] = Field(None, validation_alias="phash_distance")
    message: str
    createdAt: Optional[datetime] = Field(None, validation_alias="created_at")

    @field_validator("phashDistance", mode="before")
    @classmethod
    def parse_phash_dist(cls, v):
        if v is None:
            return None
        if isinstance(v, (bytes, bytearray)):
            try:
                return int.from_bytes(v, "little")
            except Exception:
                return None
        try:
            return int(v)
        except Exception:
            return None

    @field_validator("distanceMeters", mode="before")
    @classmethod
    def parse_dist_meters(cls, v):
        if v is None:
            return None
        try:
            return float(v)
        except Exception:
            return None

    @field_validator("confidenceScore", mode="before")
    @classmethod
    def parse_conf_score(cls, v):
        if v is None:
            return 0.0
        try:
            return float(v)
        except Exception:
            return 0.0

    model_config = ConfigDict(from_attributes=True)

class EvidenceOut(BaseModel):
    id: str
    evidenceType: str = Field(..., validation_alias="evidence_type")
    fileName: Optional[str] = Field(None, validation_alias="file_name")
    sourceUrl: Optional[str] = Field(None, validation_alias="source_url")
    capturedAt: Optional[datetime] = Field(None, validation_alias="captured_at")
    metadataJson: dict = Field(default_factory=dict, validation_alias="metadata_json")
    availabilityStatus: str = Field(..., validation_alias="availability_status")

    # Fraud & Provenance Fields
    fileHash: Optional[str] = Field(None, validation_alias="file_hash")
    phash: Optional[str] = None
    exifLatitude: Optional[float] = Field(None, validation_alias="exif_latitude")
    exifLongitude: Optional[float] = Field(None, validation_alias="exif_longitude")
    exifCapturedAt: Optional[datetime] = Field(None, validation_alias="exif_captured_at")
    cameraModel: Optional[str] = Field(None, validation_alias="camera_model")
    exifPresent: bool = Field(False, validation_alias="exif_present")
    gpsPresent: bool = Field(False, validation_alias="gps_present")
    fileSizeBytes: Optional[int] = Field(None, validation_alias="file_size_bytes")
    uploadedByUserId: Optional[str] = Field(None, validation_alias="uploaded_by_user_id")

    fraudFlags: List[FraudFlagOut] = Field(default_factory=list, validation_alias="fraud_flags")

    model_config = ConfigDict(from_attributes=True)

class DataQualityFindingOut(BaseModel):
    id: str
    fieldName: Optional[str] = Field(None, validation_alias="field_name")
    findingType: str = Field(..., validation_alias="finding_type")
    severity: str
    message: str
    evidenceJson: dict = Field(default_factory=dict, validation_alias="evidence_json")

    model_config = ConfigDict(from_attributes=True)

class WorkListItem(BaseModel):
    id: str
    externalId: str
    title: str
    category: Optional[str] = None
    locationText: Optional[str] = None
    stage: str
    sanctionAmount: Optional[float] = None
    expenditureAmount: Optional[float] = None
    latestProgressPercent: Optional[float] = None
    recommendationDate: Optional[date] = None
    sanctionDate: Optional[date] = None
    completionDate: Optional[date] = None
    agency: Optional[AgencyOut] = None
    jurisdiction: JurisdictionOut
    dataQualityFlagsCount: int = 0

    model_config = ConfigDict(from_attributes=True)

class PaginatedWorkResponse(BaseModel):
    items: List[WorkListItem]
    page: int
    pageSize: int
    total: int

from pydantic import AliasChoices

class WorkDetailOut(BaseModel):
    id: str
    externalId: str = Field(..., validation_alias=AliasChoices("externalId", "external_id"))
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    locationText: Optional[str] = Field(None, validation_alias=AliasChoices("locationText", "location_text"))
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stage: str = Field(..., validation_alias=AliasChoices("stage", "current_status"))
    sanctionAmount: Optional[float] = Field(None, validation_alias=AliasChoices("sanctionAmount", "sanction_amount"))
    expenditureAmount: Optional[float] = Field(None, validation_alias=AliasChoices("expenditureAmount", "expenditure_amount"))
    recommendationDate: Optional[date] = Field(None, validation_alias=AliasChoices("recommendationDate", "recommendation_date"))
    sanctionDate: Optional[date] = Field(None, validation_alias=AliasChoices("sanctionDate", "sanction_date"))
    targetCompletionDate: Optional[date] = Field(None, validation_alias=AliasChoices("targetCompletionDate", "completionDate", "completion_date"))
    agency: Optional[AgencyOut] = None
    jurisdiction: JurisdictionOut

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
