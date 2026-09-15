import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient, getAllEvidenceFraudFlagsApi } from '../api/client';
import { AuditLogItem, EvidenceFraudFlagItem } from '../types';
import { History, User, RefreshCw, ShieldAlert, AlertTriangle, ExternalLink } from 'lucide-react';

interface AuditLogResponse {
  items: AuditLogItem[];
  page: number;
  pageSize: number;
  total: number;
}

export const AuditPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'audit_trail' | 'evidence_fraud'>('audit_trail');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery<AuditLogResponse>({
    queryKey: ['audit-logs', page],
    queryFn: async () => {
      const res = await apiClient.get<AuditLogResponse>(`/audit-logs?page=${page}&pageSize=25`);
      return res.data;
    },
  });

  const { data: fraudFlags = [], isLoading: flagsLoading, refetch: refetchFlags } = useQuery<EvidenceFraudFlagItem[]>({
    queryKey: ['system-evidence-fraud-flags'],
    queryFn: async () => {
      const res = await getAllEvidenceFraudFlagsApi();
      return res.data;
    },
  });

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-300 pb-3">
        <div>
          <h1 className="text-xl font-serif font-bold text-[#0A2540] tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-[#0B3D6E]" />
            System Audit Trail & Photo Fraud Intelligence Register
          </h1>
          <p className="text-xs text-slate-600">
            Immutable append-only activity log and cross-work photo duplicate fraud flags
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (activeTab === 'audit_trail') refetch();
              else refetchFlags();
            }}
            className="gov-btn-secondary py-1.5 px-3 text-xs flex items-center gap-1 shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Stream</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-gray-300 pb-2">
        <button
          onClick={() => setActiveTab('audit_trail')}
          className={`px-3 py-1.5 text-xs font-bold uppercase rounded-xs transition border flex items-center gap-1.5 ${
            activeTab === 'audit_trail'
              ? 'bg-[#0B3D6E] text-white border-[#0B3D6E]'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border-gray-300'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Audit Log Stream ({data?.total || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('evidence_fraud')}
          className={`px-3 py-1.5 text-xs font-bold uppercase rounded-xs transition border flex items-center gap-1.5 ${
            activeTab === 'evidence_fraud'
              ? 'bg-red-700 text-white border-red-800'
              : 'bg-red-50 text-red-900 border-red-200 hover:bg-red-100'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5 text-red-500" />
          <span>Evidence Photo Fraud Register ({fraudFlags.length})</span>
        </button>
      </div>

      {/* Tab 1: Audit Log */}
      {activeTab === 'audit_trail' && (
        <>
          {isLoading ? (
            <div className="h-64 bg-white border border-gray-300 rounded-xs animate-pulse"></div>
          ) : error || !data || data.items.length === 0 ? (
            <div className="gov-card p-12 text-center space-y-2">
              <p className="text-sm font-bold text-slate-800 uppercase">No audit log entries recorded yet</p>
            </div>
          ) : (
            <div className="gov-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="gov-table text-xs">
                  <thead>
                    <tr>
                      <th className="w-48">Timestamp</th>
                      <th>Actor / Officer</th>
                      <th>Action Code</th>
                      <th>Entity Type</th>
                      <th>Details & Metadata Payload</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {data.items.map((log: any) => {
                      const actor = log.userName || log.user_name || 'System Process';
                      const entity = log.entityType || log.entity_type || 'Entity';
                      const details = log.detailsJson || log.details_json || {};
                      const createdDate = log.createdAt || log.created_at;

                      return (
                        <tr key={log.id}>
                          <td className="font-mono text-xs text-slate-700 font-bold whitespace-nowrap">
                            {(() => {
                              if (!createdDate) return 'N/A';
                              try {
                                const isoStr = createdDate.includes(' ') && !createdDate.includes('T') ? createdDate.replace(' ', 'T') : createdDate;
                                const d = new Date(isoStr);
                                return isNaN(d.getTime()) ? createdDate : d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
                              } catch {
                                return createdDate;
                              }
                            })()}
                          </td>

                          <td className="font-bold text-slate-900">
                            <div className="flex items-center gap-1.5">
                              <User className="w-3.5 h-3.5 text-[#0B3D6E] shrink-0" />
                              <span>{actor}</span>
                            </div>
                          </td>

                          <td className="font-mono font-bold text-amber-900">
                            <span className="bg-amber-100 border border-amber-300 px-2 py-0.5 rounded-xs text-xs">
                              {log.action}
                            </span>
                          </td>

                          <td className="text-slate-800">
                            <span className="bg-slate-100 border border-gray-300 px-2 py-0.5 rounded-xs font-mono text-xs font-bold uppercase">
                              {entity}
                            </span>
                          </td>

                          <td className="font-mono text-xs text-slate-700 max-w-md truncate">
                            {JSON.stringify(details)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="p-3 bg-slate-50 border-t border-gray-200 flex items-center justify-between text-xs text-slate-600 font-mono">
                <div>Total Stream Records: <strong>{data.total}</strong></div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page <= 1}
                    className="gov-btn-secondary py-1 px-3 text-xs disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page * data.pageSize >= data.total}
                    className="gov-btn-secondary py-1 px-3 text-xs disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Tab 2: System-wide Evidence Fraud Flags */}
      {activeTab === 'evidence_fraud' && (
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-300 rounded-xs text-xs text-red-950 flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold uppercase tracking-wider text-red-950">
                AI Cross-Work Evidence Photo Fraud Register
              </h3>
              <p className="mt-1 text-red-900 font-medium">
                Displays all active photo fraud alerts across all MPLADS works (SHA-256 exact byte matches, pHash perceptual duplicate photos, EXIF GPS & timestamp collisions across works, and geotag location mismatches).
              </p>
            </div>
          </div>

          {flagsLoading ? (
            <div className="h-64 bg-white border border-gray-300 rounded-xs animate-pulse"></div>
          ) : fraudFlags.length === 0 ? (
            <div className="gov-card p-12 text-center space-y-2">
              <p className="text-sm font-bold text-slate-800 uppercase">No evidence fraud flags recorded across the system.</p>
            </div>
          ) : (
            <div className="gov-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="gov-table text-xs">
                  <thead>
                    <tr>
                      <th>Flag Type</th>
                      <th>Severity</th>
                      <th>Confidence</th>
                      <th>Target / Source Evidence</th>
                      <th>Matched Work Item</th>
                      <th>Detection Explanation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {fraudFlags.map((flag) => (
                      <tr key={flag.id} className={flag.severity === 'CRITICAL' ? 'bg-red-50/40' : ''}>
                        <td className="font-mono font-bold text-red-900">
                          <span className="bg-red-100 border border-red-300 px-2 py-0.5 rounded-xs text-xs uppercase">
                            {flag.flagType.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={`px-2 py-0.5 rounded-xs font-bold text-[10px] uppercase border ${
                            flag.severity === 'CRITICAL' ? 'bg-red-700 text-white border-red-800' :
                            flag.severity === 'HIGH' ? 'bg-orange-600 text-white border-orange-700' :
                            flag.severity === 'MEDIUM' ? 'bg-amber-600 text-white border-amber-700' :
                            'bg-blue-600 text-white border-blue-700'
                          }`}>
                            {flag.severity}
                          </span>
                        </td>
                        <td className="font-mono font-bold text-slate-900">
                          {flag.confidenceScore}%
                        </td>
                        <td className="font-mono text-xs">
                          <span className="text-slate-600 block">{flag.evidenceId}</span>
                        </td>
                        <td>
                          {flag.matchedWorkId ? (
                            <a
                              href={`/works/${flag.matchedWorkId}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#0B3D6E] font-bold underline hover:text-blue-900 flex items-center gap-1 font-mono"
                            >
                              <span>{flag.matchedWorkExternalId || flag.matchedWorkId}</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-slate-400 font-mono">Self / Work Site</span>
                          )}
                        </td>
                        <td className="text-slate-800 font-medium max-w-md">
                          {flag.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

