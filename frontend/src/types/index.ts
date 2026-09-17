export type RiskPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface Jurisdiction {
  id: string;
  stateCode?: string;
  stateName: string;
  districtCode: string;
  districtName: string;
}

export interface User {
  id: string;
  username: string;
  fullName: string;
  email?: string;
  roles: string[];
  jurisdictions: string[];
  defaultJurisdictionId?: string;
}

export interface RiskSignal {
  code: string;
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  contribution: number;
  confidenceImpact: number;
  label?: string;
  whatHappened?: string;
  whyItMatters?: string;
  evidence?: any;
  recommendedAction?: string;
}

export interface RiskQueueItem {
  workId: string;
  externalId: string;
  title: string;
  category?: string;
  locationText?: string;
  stage: string;
  sanctionAmount?: number;
  score: number;
  priority: RiskPriority;
  confidence: number;
  topSignals: { code: string; severity: string; label: string }[];
  jurisdiction: {
    id: string;
    stateName: string;
    districtName: string;
  };
}

export interface WorkDetail {
  id: string;
  externalId: string;
  title: string;
  description?: string;
  category?: string;
  stage: string;
  sanctionAmount?: number;
  expenditureAmount?: number;
  physicalProgressPct?: number;
  recommendationDate?: string;
  sanctionDate?: string;
  targetCompletionDate?: string;
  actualCompletionDate?: string;
  locationText?: string;
  latitude?: number;
  longitude?: number;
  jurisdiction: Jurisdiction;
  agency?: {
    id: string;
    code: string;
    name: string;
    agencyType?: string;
  };
}

export interface LifecycleEvent {
  id: string;
  eventType: string;
  eventDate?: string;
  status?: string;
  amount?: number;
  description?: string;
  isMissing: boolean;
}

export interface EvidenceFraudFlagItem {
  id: string;
  evidenceId: string;
  matchedEvidenceId?: string;
  matchedWorkId?: string;
  matchedWorkTitle?: string;
  matchedWorkExternalId?: string;
  flagType: string;
  severity: RiskPriority;
  confidenceScore: number;
  distanceMeters?: number;
  phashDistance?: number;
  message: string;
  createdAt?: string;
}

export interface EvidenceItem {
  id: string;
  evidenceType: string;
  fileName: string;
  fileFormat?: string;
  fileSize?: number;
  uploadedAt?: string;
  uploaderName?: string;
  sourceUrl?: string;
  fileHash?: string;
  phash?: string;
  exifLatitude?: number;
  exifLongitude?: number;
  exifCapturedAt?: string;
  cameraModel?: string;
  exifPresent?: boolean;
  gpsPresent?: boolean;
  fileSizeBytes?: number;
  uploadedByUserId?: string;
  fraudFlags?: EvidenceFraudFlagItem[];
}

export interface SimilarityCandidate {
  workId: string;
  candidateWorkId?: string;
  externalId: string;
  title: string;
  category?: string;
  stage: string;
  sanctionAmount?: number;
  similarityScore: number;
  candidateLabel: string;
  featureBreakdown: {
    textSimilarity: number;
    geoProximity: number;
    categoryMatch: number;
    agencyMatch: number;
    costSimilarity: number;
    dateOverlap: number;
  };
}

export interface WorkRiskDetail {
  workId: string;
  externalId: string;
  title: string;
  score: number;
  confidence: number;
  priority: RiskPriority;
  signals: RiskSignal[];
}

export interface CaseActionItem {
  id: string;
  actorId: string;
  actorName: string;
  actionType: string;
  fromStatus?: string;
  toStatus?: string;
  notes: string;
  createdAt: string;
}

export interface CaseItem {
  id: string;
  caseNumber: string;
  workId: string;
  workExternalId: string;
  workTitle: string;
  createdBy: string;
  createdByName: string;
  assignedTo?: string;
  assignedToName?: string;
  status: string;
  priority: string;
  summary: string;
  createdAt: string;
  actions?: CaseActionItem[];
}

export interface AuditLogItem {
  id: string;
  userId?: string;
  userName: string;
  action: string;
  entityType: string;
  entityId?: string;
  detailsJson?: any;
  createdAt: string;
}

export interface IngestionRecord {
  id: string;
  fileName: string;
  importedAt: string;
  importedBy: string;
  totalRows: number;
  acceptedRows: number;
  rejectedRows: number;
  qualityFindingsCount: number;
}

export interface SimulationRequest {
  workId?: string;
  title?: string;
  category?: string;
  projectCost: number;
  expenditureAmount: number;
  completionPct: number;
  sanctionDate?: string;
  expectedCompletionDate?: string;
  currentStatus?: string;
}

export interface ScenarioMetrics {
  overallScore: number;
  priorityBand: RiskPriority;
  financialRiskScore: number;
  financialRiskSeverity: RiskPriority;
  delayRiskScore: number;
  delayRiskSeverity: RiskPriority;
  expenditureRatioPct: number;
  completionPct: number;
  costOverrunPct: number;
  daysElapsed: number;
  daysTotalPlanned: number;
  daysOverdue: number;
  signals: { code: string; severity: string; message: string }[];
}

export interface ImpactDelta {
  overallScoreDelta: number;
  financialRiskDelta: number;
  delayRiskDelta: number;
  priorityBandChange: string;
  isRiskIncreased: boolean;
  keyDrivers: string[];
  recommendedAction: string;
}

export interface SimulationResponse {
  workId?: string;
  workTitle: string;
  category: string;
  currentScenario: ScenarioMetrics;
  simulatedScenario: ScenarioMetrics;
  impactDelta: ImpactDelta;
}

export interface SimulationProjectItem {
  workId: string;
  externalId: string;
  title: string;
  category: string;
  projectCost: number;
  expenditureAmount: number;
  completionPct: number;
  sanctionDate?: string;
  expectedCompletionDate?: string;
  currentStatus: string;
}
