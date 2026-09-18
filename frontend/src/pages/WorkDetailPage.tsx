import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { WorkDetail, LifecycleEvent, WorkRiskDetail, SimilarityCandidate } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';
import { TimelineView } from '../components/work/TimelineView';
import { RiskExplanationPanel } from '../components/work/RiskExplanationPanel';
import { EvidencePanel } from '../components/work/EvidencePanel';
import { SimilarWorksCard } from '../components/work/SimilarWorksCard';
import {
  ArrowLeft,
  MapPin,
  Building2,
  PlusCircle,
  AlertTriangle,
  Layers,
} from 'lucide-react';

export const WorkDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'overview' | 'signals' | 'timeline' | 'evidence' | 'duplicates'>('overview');

  // Fetch Work Detail
  const { data: work, isLoading: workLoading } = useQuery<WorkDetail>({
    queryKey: ['work-detail', id],
    queryFn: async () => {
      const res = await apiClient.get<WorkDetail>(`/works/${id}`);
      return res.data;
    },
    enabled: !!id,
  });

  // Fetch Risk Detail
  const { data: riskDetail } = useQuery<WorkRiskDetail>({
    queryKey: ['work-risk', id],
    queryFn: async () => {
      const res = await apiClient.get<WorkRiskDetail>(`/risk/works/${id}`);
      return res.data;
    },
    enabled: !!id,
  });

  // Fetch Timeline
  const { data: timelineEvents = [] } = useQuery<LifecycleEvent[]>({
    queryKey: ['work-timeline', id],
    queryFn: async () => {
      const res = await apiClient.get<LifecycleEvent[]>(`/works/${id}/timeline`);
      return res.data;
    },
    enabled: !!id,
  });

  // Fetch Evidence
  const { data: evidenceList = [] } = useQuery<any[]>({
    queryKey: ['work-evidence', id],
    queryFn: async () => {
      const res = await apiClient.get(`/works/${id}/evidence`);
      return res.data;
    },
    enabled: !!id,
  });

  // Fetch Similar Candidates
  const { data: candidatesData } = useQuery<any>({
    queryKey: ['work-similar', id],
    queryFn: async () => {
      const res = await apiClient.get(`/works/${id}/similar`);
      return res.data;
    },
    enabled: !!id,
  });

  const candidates: SimilarityCandidate[] = candidatesData?.candidates || [];

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const createCaseMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/cases', {
        workId: work?.id,
        priority: 'HIGH',
        summary: `Operational review for ${work?.externalId}: ${work?.title}`,
        initialNotes: `Initiated formal inquiry from Work Detail investigation canvas.`,
      });
      return res.data;
    },
    onSuccess: (newCase: any) => {
      queryClient.invalidateQueries({ queryKey: ['cases-list'] });
      const cId = newCase.id;
      navigate(`/cases?caseId=${cId}`);
    },
  });

  if (workLoading) {
    return (
      <div className="space-y-6">
        <div className="h-32 bg-white border border-gray-300 rounded-xs animate-pulse"></div>
        <div className="h-64 bg-white border border-gray-300 rounded-xs animate-pulse"></div>
      </div>
    );
  }

  if (!work) {
    return (
      <div className="gov-card p-8 text-center space-y-3">
        <p className="text-sm font-bold text-red-700">Work record not found.</p>
        <Link to="/queue" className="gov-btn-secondary text-xs">
          Return to Risk Queue
        </Link>
      </div>
    );
  }

  const hasMissingCertWarning = riskDetail?.signals.some((s) => s.code === 'COMP-EVID-001') || false;

  return (
    <div className="space-y-6 font-sans">
      {/* Back Navigation */}
      <div>
        <Link
          to="/queue"
          className="text-xs text-slate-600 hover:text-[#0B3D6E] font-bold inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Prioritized Risk Queue</span>
        </Link>
      </div>

      {/* Main Work Identity Banner */}
      <div className="gov-card p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 border-b border-gray-200 pb-4">
          <div className="space-y-1.5 max-w-3xl">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono font-bold text-[#0B3D6E] bg-blue-50 px-2 py-0.5 border border-blue-200 rounded-xs">
                {work.externalId}
              </span>
              {riskDetail && <RiskBadge priority={riskDetail.priority} score={riskDetail.score} size="md" />}
              <span className="text-xs font-mono font-bold bg-slate-100 text-slate-800 border border-gray-300 px-2 py-0.5 rounded-xs uppercase">
                STAGE: {work.stage}
              </span>
            </div>

            <h1 className="text-lg font-serif font-bold text-slate-900 leading-snug">
              {work.title}
            </h1>

            <div className="flex items-center gap-4 text-xs text-slate-600 flex-wrap">
              <span className="flex items-center gap-1 font-medium">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                District: {work.jurisdiction.districtName} ({work.jurisdiction.stateName})
              </span>
              {work.agency && (
                <span className="flex items-center gap-1 font-medium">
                  <Building2 className="w-3.5 h-3.5 text-slate-500" />
                  Executing Agency: {work.agency.name}
                </span>
              )}
              {work.category && (
                <span className="flex items-center gap-1 font-medium">
                  <Layers className="w-3.5 h-3.5 text-slate-500" />
                  Category: {work.category}
                </span>
              )}
            </div>
          </div>

          {/* Case Trigger Action */}
          <div className="shrink-0 flex items-center gap-2">
            <button
              onClick={() => createCaseMutation.mutate()}
              disabled={createCaseMutation.isPending}
              className="gov-btn-primary py-2 px-4 text-xs inline-flex items-center gap-1"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{createCaseMutation.isPending ? 'Opening Case...' : 'Create Review Case'}</span>
            </button>
          </div>
        </div>

        {/* Financial & Physical Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-0.5">
            <span className="text-slate-600 text-[10px] uppercase font-bold tracking-wider block">
              Sanction Amount
            </span>
            <span className="font-mono font-bold text-slate-900 text-sm">
              {work.sanctionAmount ? `₹${work.sanctionAmount.toLocaleString('en-IN')}` : 'N/A'}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-0.5">
            <span className="text-slate-600 text-[10px] uppercase font-bold tracking-wider block">
              Disbursed Expenditure
            </span>
            <span className="font-mono font-bold text-[#0B3D6E] text-sm">
              {work.expenditureAmount ? `₹${work.expenditureAmount.toLocaleString('en-IN')}` : 'N/A'}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-0.5">
            <span className="text-slate-600 text-[10px] uppercase font-bold tracking-wider block">
              Physical Progress Pct
            </span>
            <span className="font-mono font-bold text-indigo-900 text-sm">
              {work.physicalProgressPct !== undefined ? `${work.physicalProgressPct.toFixed(1)}%` : 'N/A'}
            </span>
          </div>

          <div className="p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-0.5">
            <span className="text-slate-600 text-[10px] uppercase font-bold tracking-wider block">
              Sanction Date
            </span>
            <span className="font-mono font-bold text-slate-800 text-xs">
              {work.sanctionDate ? new Date(work.sanctionDate).toLocaleDateString('en-IN') : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* 5 Tabs Header */}
      <div className="flex items-center space-x-2 border-b border-gray-300 pb-2 overflow-x-auto min-w-0 text-xs font-bold uppercase tracking-wider">
        {[
          { key: 'overview', label: 'Overview' },
          { key: 'signals', label: `Risk Signals (${riskDetail?.signals.length || 0})` },
          { key: 'timeline', label: `Lifecycle Timeline (${timelineEvents.length})` },
          { key: 'evidence', label: `Evidence Gallery (${evidenceList.length})` },
          { key: 'duplicates', label: `Candidate Duplicates (${candidates.length})` },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-3 py-1.5 rounded-xs whitespace-nowrap transition border ${
              activeTab === tab.key
                ? 'bg-[#0B3D6E] text-white border-[#0B3D6E]'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Top Fraud Warning Badge if Evidence has Fraud Flags */}
      {evidenceList.some((e: any) => e.fraudFlags && e.fraudFlags.length > 0) && (
        <div className="p-4 bg-red-600 text-white rounded-xs shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start sm:items-center gap-3 min-w-0">
            <AlertTriangle className="w-6 h-6 shrink-0 text-white animate-pulse" />
            <div className="min-w-0">
              <h3 className="text-xs font-bold uppercase tracking-wider">
                ⚠ CROSS-WORK EVIDENCE FRAUD DETECTED FOR THIS WORK
              </h3>
              <p className="text-[11px] text-red-100 font-medium leading-normal">
                Photo evidence uploaded for this work matches identical bytes, perceptual pHash, or EXIF geotags of works in another district.
              </p>
            </div>
          </div>
          <button
            onClick={() => setActiveTab('evidence')}
            className="px-3 py-1.5 bg-white text-red-700 hover:bg-red-50 text-xs font-bold rounded-xs shrink-0 font-mono uppercase self-start sm:self-auto"
          >
            Review Evidence Flags ({evidenceList.flatMap((e: any) => e.fraudFlags || []).length})
          </button>
        </div>
      )}

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="gov-card p-5 space-y-3">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">Work Scope & Location Details</h2>
            <p className="text-xs text-slate-700 leading-relaxed">{work.description || 'No detailed scope description recorded for this work item.'}</p>
            <div className="pt-2 text-xs font-mono text-slate-600">
              <span>Physical Location: <strong>{work.locationText || 'District Work Location'}</strong></span>
            </div>
          </div>

          {riskDetail && (
            <RiskExplanationPanel
              signals={riskDetail.signals}
              score={riskDetail.score}
              confidence={riskDetail.confidence}
            />
          )}
        </div>
      )}

      {activeTab === 'signals' && riskDetail && (
        <RiskExplanationPanel
          signals={riskDetail.signals}
          score={riskDetail.score}
          confidence={riskDetail.confidence}
        />
      )}

      {activeTab === 'timeline' && <TimelineView events={timelineEvents} />}

      {activeTab === 'evidence' && (
        <EvidencePanel
          workId={id}
          evidenceList={evidenceList}
          missingEvidenceWarning={hasMissingCertWarning}
          onEvidenceUploaded={() => queryClient.invalidateQueries({ queryKey: ['work-evidence', id] })}
        />
      )}

      {activeTab === 'duplicates' && <SimilarWorksCard candidates={candidates} />}
    </div>
  );
};
