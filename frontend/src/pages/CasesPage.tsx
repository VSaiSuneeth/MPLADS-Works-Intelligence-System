import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { CaseItem } from '../types';
import { useAuth } from '../context/AuthContext';
import {
  FolderGit2,
  X,
  Send,
  PlusCircle,
  Plus,
} from 'lucide-react';

interface CaseListResponse {
  items: CaseItem[];
  page: number;
  pageSize: number;
  total: number;
}

export const CasesPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { selectedJurisdictionId } = useAuth();
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'ALL');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  // Auto-open modal if caseId parameter is passed in URL
  useEffect(() => {
    const qCaseId = searchParams.get('caseId') || searchParams.get('selectedCaseId');
    if (qCaseId) {
      setSelectedCaseId(qCaseId);
    }
  }, [searchParams]);

  // Create Case Form State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newCaseWorkId, setNewCaseWorkId] = useState('');
  const [newCasePriority, setNewCasePriority] = useState('HIGH');
  const [newCaseSummary, setNewCaseSummary] = useState('');
  const [newCaseNotes, setNewCaseNotes] = useState('');

  // Fetch Works dropdown for case creation
  const { data: worksData } = useQuery<any>({
    queryKey: ['works-for-cases', selectedJurisdictionId],
    queryFn: async () => {
      let url = `/works?pageSize=100`;
      if (selectedJurisdictionId) url += `&jurisdictionId=${selectedJurisdictionId}`;
      const res = await apiClient.get(url);
      return res.data;
    },
    enabled: isCreateModalOpen,
  });

  const createCaseMutation = useMutation({
    mutationFn: async (payload: { workId: string; priority: string; summary: string; initialNotes: string }) => {
      const res = await apiClient.post('/cases', payload);
      return res.data;
    },
    onSuccess: (newCase: any) => {
      queryClient.invalidateQueries({ queryKey: ['cases-list'] });
      setIsCreateModalOpen(false);
      setNewCaseWorkId('');
      setNewCaseSummary('');
      setNewCaseNotes('');
      if (newCase?.id) {
        setSelectedCaseId(newCase.id);
      }
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseWorkId || !newCaseSummary.trim()) return;
    createCaseMutation.mutate({
      workId: newCaseWorkId,
      priority: newCasePriority,
      summary: newCaseSummary,
      initialNotes: newCaseNotes || `Case opened for physical verification.`,
    });
  };

  // New Action Form State
  const [actionType, setActionType] = useState('ADD_NOTE');
  const [newStatus, setNewStatus] = useState('');
  const [actionNotes, setActionNotes] = useState('');

  // Fetch Cases
  const { data, isLoading, error } = useQuery<CaseListResponse>({
    queryKey: ['cases-list', selectedJurisdictionId, statusFilter],
    queryFn: async () => {
      let url = `/cases?status=${statusFilter}`;
      if (selectedJurisdictionId) url += `&jurisdictionId=${selectedJurisdictionId}`;
      const res = await apiClient.get<CaseListResponse>(url);
      return res.data;
    },
  });

  // Fetch Selected Case Detail
  const { data: caseDetail } = useQuery<any>({
    queryKey: ['case-detail', selectedCaseId],
    queryFn: async () => {
      const res = await apiClient.get(`/cases/${selectedCaseId}`);
      return res.data;
    },
    enabled: !!selectedCaseId,
  });

  // Action Mutation
  const actionMutation = useMutation({
    mutationFn: async (payload: { actionType: string; newStatus?: string; notes: string }) => {
      const res = await apiClient.post(`/cases/${selectedCaseId}/actions`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases-list'] });
      queryClient.invalidateQueries({ queryKey: ['case-detail', selectedCaseId] });
      setActionNotes('');
      setNewStatus('');
    },
  });

  const handleActionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionNotes.trim() || !selectedCaseId) return;

    actionMutation.mutate({
      actionType,
      newStatus: newStatus || undefined,
      notes: actionNotes,
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CLARIFICATION_REQUESTED':
        return 'bg-[#B45309] text-white border-[#92400E]';
      case 'RESOLVED':
      case 'VERIFIED':
        return 'bg-[#15803D] text-white border-[#166534]';
      case 'ASSIGNED':
      case 'UNDER_REVIEW':
        return 'bg-[#0B3D6E] text-white border-[#0A2540]';
      default:
        return 'bg-slate-700 text-white border-slate-800';
    }
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-300 pb-4">
        <div>
          <h1 className="text-xl font-serif font-bold text-[#0A2540] tracking-tight flex items-center gap-2">
            <FolderGit2 className="w-5 h-5 text-[#0B3D6E]" />
            Review Workload & Operational Cases
          </h1>
          <p className="text-xs text-slate-600 font-sans">
            Track active inquiry workload, issue official agency clarification requests, and maintain complete audit trail
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="gov-btn-primary py-2 px-4 text-xs shrink-0 flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>Open New Review Case</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-300 pb-2 overflow-x-auto text-xs font-bold uppercase tracking-wider">
        {[
          { key: 'ALL', label: 'ALL CASES' },
          { key: 'OPEN', label: 'OPEN REVIEW WORKLOAD' },
          { key: 'CLARIFICATION_REQUESTED', label: 'CLARIFICATIONS REQUESTED' },
          { key: 'RESOLVED', label: 'RESOLVED / CLOSED' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setStatusFilter(tab.key);
              setSearchParams({ status: tab.key });
            }}
            className={`px-3 py-1.5 rounded-xs whitespace-nowrap transition border ${
              statusFilter === tab.key
                ? 'bg-[#0B3D6E] text-white border-[#0B3D6E]'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Cases List */}
      {isLoading ? (
        <div className="h-64 bg-white border border-gray-300 rounded-xs animate-pulse"></div>
      ) : error || !data || data.items.length === 0 ? (
        <div className="gov-card p-12 text-center space-y-4">
          <p className="text-sm font-bold text-slate-800 uppercase tracking-wide">No review cases found matching criteria</p>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            Cases are automatically opened when an officer flags a high-priority work for physical audit or clarification. You can also open a new case manually.
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="gov-btn-primary py-2 px-4 text-xs inline-flex items-center gap-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Open New Case Now</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {data.items.map((c: any) => {
            const caseNum = c.caseNumber || c.case_number;
            const workExtId = c.workExternalId || c.work_external_id;
            const workTitle = c.workTitle || c.work_title;
            const creator = c.createdByName || c.created_by_name;
            const assignee = c.assignedToName || c.assigned_to_name;
            const createdDate = c.createdAt || c.created_at;

            return (
              <div
                key={c.id}
                className="gov-card p-4 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 max-w-3xl">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono font-bold text-[#0B3D6E] bg-blue-50 px-2 py-0.5 rounded-xs border border-blue-200">
                      {caseNum}
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-xs border border-gray-300">
                      WORK: {workExtId}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-xs border uppercase tracking-wider ${getStatusBadge(c.status)}`}>
                      STATUS: {c.status.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-slate-900 leading-snug">
                    <Link to={`/works/${c.workId || c.work_id}`} className="hover:text-[#0B3D6E] transition">
                      {workTitle}
                    </Link>
                  </h3>

                  <p className="text-xs text-slate-700 line-clamp-1 font-medium">{c.summary}</p>

                  <div className="flex items-center gap-4 text-[11px] text-slate-500 font-sans flex-wrap pt-0.5">
                    <span>Opened by <strong>{creator}</strong></span>
                    <span>Assigned: <strong>{assignee || 'Unassigned'}</strong></span>
                    <span>Opened Date: <strong>{createdDate ? new Date(createdDate).toLocaleDateString() : 'N/A'}</strong></span>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedCaseId(c.id)}
                  className="gov-btn-primary py-1.5 px-4 text-xs shrink-0"
                >
                  Inspect & Respond
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Case Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-300 border-t-4 border-t-[#0B3D6E] rounded-xs max-w-xl w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-200 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900 leading-tight uppercase tracking-wide">
                  Open New Operational Review Case
                </h2>
                <p className="text-xs text-slate-500">Initiate formal inquiry for work physical audit or clarification</p>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1 text-slate-500 hover:text-slate-900 rounded-xs transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">
                  Select Infrastructure Work *
                </label>
                <select
                  value={newCaseWorkId}
                  onChange={(e) => {
                    setNewCaseWorkId(e.target.value);
                    const selectedWork = worksData?.items?.find((w: any) => w.id === e.target.value);
                    if (selectedWork && !newCaseSummary) {
                      setNewCaseSummary(`Operational review for ${selectedWork.externalId}: ${selectedWork.title}`);
                    }
                  }}
                  className="gov-input font-medium"
                  required
                >
                  <option value="">-- Choose Work Record --</option>
                  {worksData?.items?.map((w: any) => (
                    <option key={w.id} value={w.id}>
                      {w.externalId} — {w.title} ({w.stage})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">
                  Case Priority Level *
                </label>
                <select
                  value={newCasePriority}
                  onChange={(e) => setNewCasePriority(e.target.value)}
                  className="gov-input font-medium"
                >
                  <option value="CRITICAL">CRITICAL PRIORITY</option>
                  <option value="HIGH">HIGH PRIORITY</option>
                  <option value="MEDIUM">MEDIUM PRIORITY</option>
                  <option value="LOW">LOW PRIORITY</option>
                </select>
              </div>

              <div>
                <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">
                  Review Summary Title *
                </label>
                <input
                  type="text"
                  value={newCaseSummary}
                  onChange={(e) => setNewCaseSummary(e.target.value)}
                  placeholder="e.g. Physical progress lagging behind expenditure disbursement"
                  className="gov-input font-medium"
                  required
                />
              </div>

              <div>
                <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">
                  Initial Officer Observation / Notes
                </label>
                <textarea
                  value={newCaseNotes}
                  onChange={(e) => setNewCaseNotes(e.target.value)}
                  placeholder="Enter initial officer notes or reason for opening review case..."
                  className="gov-input min-h-[80px]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="gov-btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createCaseMutation.isPending}
                  className="gov-btn-primary text-xs flex items-center gap-1"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{createCaseMutation.isPending ? 'Opening Case...' : 'Open Case'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Case Action Modal */}
      {selectedCaseId && caseDetail && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-300 border-t-4 border-t-[#0B3D6E] rounded-xs max-w-2xl w-full p-6 space-y-5 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-gray-200 pb-3">
              <div>
                <span className="text-xs font-mono font-bold text-[#0B3D6E]">{caseDetail.caseNumber || caseDetail.case_number}</span>
                <h2 className="text-sm font-bold text-slate-900 leading-tight">{caseDetail.workTitle || caseDetail.work_title}</h2>
              </div>
              <button
                onClick={() => setSelectedCaseId(null)}
                className="p-1 text-slate-500 hover:text-slate-900 rounded-xs transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Case State */}
            <div className="p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-1.5 text-xs">
              <div className="flex justify-between text-slate-700 font-mono font-bold">
                <span>STATUS: <strong className="text-[#0B3D6E]">{caseDetail.status}</strong></span>
                <span>PRIORITY: <strong className="text-amber-800">{caseDetail.priority}</strong></span>
              </div>
              <p className="text-slate-800 font-medium leading-relaxed">Review Summary: {caseDetail.summary}</p>
            </div>

            {/* Action History Timeline */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 border-b border-gray-200 pb-1">
                Action Log & Discrepancy Clarification Stream
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {(caseDetail.actions || []).map((act: any) => {
                  const actor = act.actorName || act.actor_name || 'Officer';
                  const actType = act.actionType || act.action_type || 'ACTION';
                  const actDate = act.createdAt || act.created_at;

                  return (
                    <div key={act.id} className="p-3 bg-slate-50 border border-gray-300 rounded-xs space-y-1 text-xs">
                      <div className="flex justify-between text-[11px] text-slate-600">
                        <span className="font-bold text-slate-900">{actor} ({actType})</span>
                        <span className="font-mono text-slate-500">{actDate ? new Date(actDate).toLocaleString() : ''}</span>
                      </div>
                      <p className="text-slate-800 font-medium leading-relaxed">{act.notes}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Add Action Form */}
            <form onSubmit={handleActionSubmit} className="space-y-3 border-t border-gray-200 pt-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                Record Officer Action / Inquiry Response
              </h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">Action Type</label>
                  <select
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value)}
                    className="gov-input font-medium"
                  >
                    <option value="ADD_NOTE">Log Officer Note</option>
                    <option value="REQUEST_CLARIFICATION">Request Agency Clarification</option>
                    <option value="UPDATE_STATUS">Update Case Status</option>
                    <option value="MARK_RESOLVED">Mark Discrepancy Resolved</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-700 font-bold block mb-1 uppercase tracking-wider text-[10px]">Set New Status (Optional)</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    className="gov-input font-medium"
                  >
                    <option value="">Keep Current Status</option>
                    <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                    <option value="CLARIFICATION_REQUESTED">CLARIFICATION_REQUESTED</option>
                    <option value="VERIFIED">VERIFIED</option>
                    <option value="RESOLVED">RESOLVED</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>
                </div>
              </div>

              <div>
                <textarea
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder="Enter official observation, inquiry text, or physical inspection findings..."
                  className="gov-input min-h-[80px]"
                  required
                />
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedCaseId(null)}
                  className="gov-btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionMutation.isPending}
                  className="gov-btn-primary text-xs flex items-center gap-1"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Official Action</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
