import React from 'react';
import { Link } from 'react-router-dom';
import { RiskQueueItem } from '../../types';
import { RiskBadge } from '../common/RiskBadge';
import { ArrowRight, AlertTriangle, Building2, MapPin } from 'lucide-react';

interface WorkTableProps {
  items: RiskQueueItem[];
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (newPage: number) => void;
}

export const WorkTable: React.FC<WorkTableProps> = ({
  items,
  page,
  pageSize,
  total,
  onPageChange,
}) => {
  const safeItems = Array.isArray(items) ? items : [];
  const totalPages = Math.ceil((total || 0) / (pageSize || 1)) || 1;

  if (safeItems.length === 0) {
    return (
      <div className="gov-card p-12 text-center space-y-3">
        <p className="text-sm font-bold text-slate-800 uppercase tracking-wide">
          No works match the selected search & filter criteria
        </p>
        <p className="text-xs text-slate-600">
          Try clearing search terms or resetting priority/stage filters.
        </p>
      </div>
    );
  }

  return (
    <div className="gov-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="gov-table">
          <thead>
            <tr>
              <th className="w-32">Work ID</th>
              <th>Work Title & District Scope</th>
              <th>Stage</th>
              <th className="text-right">Sanction Amount</th>
              <th>Risk Priority</th>
              <th>Primary Anomaly Finding</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {safeItems.map((w) => {
              const topSignal = w.topSignals && w.topSignals.length > 0 ? w.topSignals[0] : null;

              return (
                <tr key={w.workId}>
                  {/* External ID */}
                  <td className="font-mono font-bold text-[#0B3D6E] align-top text-xs">
                    {w.externalId}
                  </td>

                  {/* Title & Location */}
                  <td className="align-top max-w-sm space-y-1">
                    <Link
                      to={`/works/${w.workId}`}
                      className="font-bold text-slate-900 hover:text-[#0B3D6E] transition line-clamp-2"
                    >
                      {w.title}
                    </Link>
                    <div className="flex items-center gap-3 text-xs text-slate-600 flex-wrap">
                      <span className="flex items-center gap-1 font-medium">
                        <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                        {w.jurisdiction?.districtName || 'N/A'}
                      </span>
                      {w.category && (
                        <span className="flex items-center gap-1 font-medium truncate max-w-[160px]">
                          <Building2 className="w-3 h-3 text-slate-500 shrink-0" />
                          {w.category}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Stage */}
                  <td className="align-top">
                    <span className="px-2 py-0.5 rounded-xs text-[10px] font-bold font-mono bg-slate-100 text-slate-800 border border-gray-300 uppercase">
                      {w.stage}
                    </span>
                  </td>

                  {/* Sanction Amount */}
                  <td className="align-top text-right font-mono font-bold text-slate-900">
                    {w.sanctionAmount ? `₹${w.sanctionAmount.toLocaleString('en-IN')}` : 'N/A'}
                  </td>

                  {/* Risk Priority */}
                  <td className="align-top">
                    <RiskBadge priority={w.priority} score={w.score} size="sm" />
                  </td>

                  {/* Anomaly Signal */}
                  <td className="align-top max-w-xs">
                    {topSignal ? (
                      <div className="text-[11px] text-amber-900 font-semibold bg-amber-50 border border-amber-200 p-1.5 rounded-xs flex items-start gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                        <span className="line-clamp-2">{topSignal.label}</span>
                      </div>
                    ) : (
                      <span className="text-slate-400 text-xs italic">No anomaly flagged</span>
                    )}
                  </td>

                  {/* Review Link */}
                  <td className="align-top text-right">
                    <Link
                      to={`/works/${w.workId}`}
                      className="gov-btn-primary py-1 px-3 text-xs inline-flex items-center gap-1"
                    >
                      <span>Review</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <div className="p-3 bg-slate-50 border-t border-gray-200 flex items-center justify-between text-xs text-slate-600 font-mono">
        <div>
          Showing page <strong>{page}</strong> of <strong>{totalPages}</strong> ({total} total works)
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="gov-btn-secondary py-1 px-3 text-xs disabled:opacity-50"
          >
            Previous
          </button>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="gov-btn-secondary py-1 px-3 text-xs disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
