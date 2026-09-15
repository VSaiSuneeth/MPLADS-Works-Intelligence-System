from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict
from datetime import datetime

class DataFreshnessOut(BaseModel):
    lastIngestionAt: Optional[str] = Field(None, alias="last_ingestion_at")
    sourceLabel: str = Field(..., alias="source_label")
    datasetLabel: str = Field(..., alias="dataset_label")
    isOfficialData: bool = Field(..., alias="is_official_data")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TotalsOut(BaseModel):
    totalWorks: int
    openCases: int
    completedWorks: int
    executionWorks: int

class RiskDistributionOut(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

class TopRiskWorkOut(BaseModel):
    workId: str
    externalId: str
    title: str
    category: Optional[str] = None
    stage: str
    sanctionAmount: Optional[float] = None
    score: float
    priority: str
    confidence: float
    topSignalLabel: str
    districtName: str

class DashboardSummaryResponse(BaseModel):
    jurisdictionId: Optional[str] = None
    districtName: Optional[str] = None
    dataFreshness: DataFreshnessOut
    totals: TotalsOut
    riskDistribution: RiskDistributionOut
    topRiskWorks: List[TopRiskWorkOut]
