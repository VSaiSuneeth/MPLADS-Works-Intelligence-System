import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { TopRiskWorksCard } from '../components/dashboard/TopRiskWorksCard';
import { GeospatialMapCard } from '../components/dashboard/GeospatialMapCard';
import {
  FileSpreadsheet,
  FolderGit2,
  Clock,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { selectedJurisdictionId } = useAuth();

  const { data, isLoading, error } = useQuery<any>({
    queryKey: ['dashboard-summary', selectedJurisdictionId],
    queryFn: async () => {
      let url = '/dashboard/summary';
      if (selectedJurisdictionId) url += `?jurisdictionId=${selectedJurisdictionId}`;
      const res = await apiClient.get(url);
      return res.data;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-24 bg-white border border-gray-300 rounded-sm animate-pulse"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-white border border-gray-300 rounded-sm animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="gov-card p-8 text-center text-red-700 space-y-2">
        <AlertTriangle className="w-8 h-8 mx-auto" />
        <p className="font-bold text-xs">Failed to load Governance Dashboard metrics.</p>
      </div>
    );
  }

  const totals = data.totals || { totalWorks: 0, openCases: 0, executionWorks: 0, completedWorks: 0 };
  const riskDistribution = data.riskDistribution || { critical: 0, high: 0, medium: 0, low: 0 };
  const topRiskCandidates = data.topRiskWorks || data.top_risk_works || data.topRiskCandidates || [];
  const mapWorksList = data.mapWorks || data.map_works || topRiskCandidates;
  const dataFreshness = data.dataFreshness || { datasetLabel: 'SYNTHETIC_DEMO' };

  return (
    <div className="space-y-6 font-sans">
      {/* Controlled Data Provenance Banner */}
      <div className="p-3 bg-amber-50 border border-amber-300 rounded-sm text-xs text-amber-950 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-amber-700 shrink-0" />
          <span>
            <strong>Controlled Data Provenance:</strong> {dataFreshness.datasetLabel || dataFreshness.dataset_label || 'SYNTHETIC_DEMO'} — District operational review candidates.
          </span>
        </div>
        <span className="font-mono text-[10px] text-amber-800 bg-amber-100 px-2 py-0.5 rounded-sm border border-amber-200">
          MoSPI Verified Seed Feed
        </span>
      </div>

      {/* Header */}
      <div className="border-b border-gray-300 pb-3">
        <h1 className="text-xl font-serif font-bold text-[#0A2540] tracking-tight">
          District Governance & Operational Review Dashboard
        </h1>
        <p className="text-xs text-slate-600">
          Executive situational awareness across MPLADS sanctioned works, active review workload, and priority risk bands
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="gov-card p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-sm bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0B3D6E] shrink-0">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Sanctioned Works
            </span>
            <span className="text-xl font-mono font-bold text-slate-900">{totals.totalWorks || 0}</span>
          </div>
        </div>

        <div className="gov-card p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-sm bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-800 shrink-0">
            <FolderGit2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Active Open Cases
            </span>
            <span className="text-xl font-mono font-bold text-amber-900">{totals.openCases || 0}</span>
          </div>
        </div>

        <div className="gov-card p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-sm bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-800 shrink-0">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              In Execution Stage
            </span>
            <span className="text-xl font-mono font-bold text-indigo-900">{totals.executionWorks || 0}</span>
          </div>
        </div>

        <div className="gov-card p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-sm bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-800 shrink-0">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Completed Works
            </span>
            <span className="text-xl font-mono font-bold text-emerald-900">{totals.completedWorks || 0}</span>
          </div>
        </div>
      </div>

      {/* Geospatial Risk Distribution Map */}
      <GeospatialMapCard works={mapWorksList} />

      {/* Priority Breakdown & Risk Queue Top Candidates */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Bands Summary */}
        <div className="gov-card p-5 space-y-4">
          <div className="border-b border-gray-200 pb-2">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Risk Priority Distribution
            </h2>
            <p className="text-xs text-slate-500">Categorized risk bands for prioritized officer review</p>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="p-3 bg-[#991B1B]/10 border border-[#991B1B]/30 rounded-sm flex justify-between items-center text-[#991B1B]">
              <span className="font-bold uppercase">Critical Priority (≥80 pts)</span>
              <span className="text-sm font-bold">{riskDistribution.critical || 0}</span>
            </div>

            <div className="p-3 bg-[#C2410C]/10 border border-[#C2410C]/30 rounded-sm flex justify-between items-center text-[#C2410C]">
              <span className="font-bold uppercase">High Priority (60-79 pts)</span>
              <span className="text-sm font-bold">{riskDistribution.high || 0}</span>
            </div>

            <div className="p-3 bg-[#B45309]/10 border border-[#B45309]/30 rounded-sm flex justify-between items-center text-[#B45309]">
              <span className="font-bold uppercase">Medium Priority (30-59 pts)</span>
              <span className="text-sm font-bold">{riskDistribution.medium || 0}</span>
            </div>

            <div className="p-3 bg-[#15803D]/10 border border-[#15803D]/30 rounded-sm flex justify-between items-center text-[#15803D]">
              <span className="font-bold uppercase">Low Priority (&lt;30 pts)</span>
              <span className="text-sm font-bold">{riskDistribution.low || 0}</span>
            </div>
          </div>
        </div>

        {/* Top Risk Candidate Works */}
        <div className="lg:col-span-2">
          <TopRiskWorksCard works={topRiskCandidates} />
        </div>
      </div>
    </div>
  );
};
