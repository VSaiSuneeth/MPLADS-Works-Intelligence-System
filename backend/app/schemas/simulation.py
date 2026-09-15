from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

class SimulationRequest(BaseModel):
    work_id: Optional[str] = Field(None, alias="workId")
    title: Optional[str] = Field("Simulated Work Proposal", alias="title")
    category: Optional[str] = Field("Water Supply & Sanitation", alias="category")
    project_cost: float = Field(..., ge=0, alias="projectCost", description="Sanctioned project cost in INR")
    expenditure_amount: float = Field(..., ge=0, alias="expenditureAmount", description="Actual or expected expenditure in INR")
    completion_pct: float = Field(..., ge=0, le=100, alias="completionPct", description="Physical progress percentage (0-100)")
    sanction_date: Optional[str] = Field(None, alias="sanctionDate", description="Sanction date YYYY-MM-DD")
    expected_completion_date: Optional[str] = Field(None, alias="expectedCompletionDate", description="Target completion date YYYY-MM-DD")
    current_status: Optional[str] = Field("EXECUTION", alias="currentStatus", description="Work execution stage")

    model_config = ConfigDict(populate_by_name=True)

class ScenarioMetrics(BaseModel):
    overallScore: float
    priorityBand: str  # CRITICAL, HIGH, MEDIUM, LOW
    financialRiskScore: float
    financialRiskSeverity: str
    delayRiskScore: float
    delayRiskSeverity: str
    expenditureRatioPct: float
    completionPct: float
    costOverrunPct: float
    daysElapsed: int
    daysTotalPlanned: int
    daysOverdue: int
    signals: List[Dict[str, Any]]

    model_config = ConfigDict(populate_by_name=True)

class ImpactDelta(BaseModel):
    overallScoreDelta: float
    financialRiskDelta: float
    delayRiskDelta: float
    priorityBandChange: str
    isRiskIncreased: bool
    keyDrivers: List[str]
    recommendedAction: str

    model_config = ConfigDict(populate_by_name=True)

class SimulationResponse(BaseModel):
    workId: Optional[str] = None
    workTitle: str
    category: str
    currentScenario: ScenarioMetrics
    simulatedScenario: ScenarioMetrics
    impactDelta: ImpactDelta

    model_config = ConfigDict(populate_by_name=True)
