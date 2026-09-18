import React from 'react';
import { Link } from 'react-router-dom';
import { RiskBadge } from '../common/RiskBadge';
import { ArrowRight, AlertTriangle, Building2, MapPin, CheckCircle2 } from 'lucide-react';

interface TopRiskWorkItem {
  workId: string;
  externalId: string;
  title: string;
  category?: string;
  stage: string;
  sanctionAmount?: number;
  score: number;
  priority: any;
  confidence: number;
  topSignalLabel: string;
  districtName: string;
}

interface TopRiskWorksProps {
  works?: TopRiskWorkItem[];
}

export const TopRiskWorksCard: React.FC<TopRiskWorksProps> = ({ works = [] }) => {
  const safeWorks = Array.isArray(works) ? works : [];

  return (
    <div className="gov-card p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-gray-200 pb-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Top Priority Review Candidates
          </h2>
          <p className="text-xs text-slate-500">
            Sanctioned works flagged for urgent operational review and physical verification
          </p>
        </div>
        <Link
          to="/queue?priority=CRITICAL"
          className="gov-btn-secondary py-1 text-xs flex items-center gap-1"
        >
          <span>View Full Risk Queue</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {safeWorks.length === 0 ? (
        <div className="p-8 text-center bg-slate-50 border border-gray-200 rounded-sm space-y-1">
          <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto" />
          <p className="text-xs font-bold text-slate-800 uppercase">No Critical Priority Candidates Flagged</p>
          <p className="text-xs text-slate-500">All district works are currently operating within low-to-medium risk thresholds.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {safeWorks.map((w) => (
            <div
              key={w.workId}
              className="p-3.5 bg-slate-50 border border-gray-300 hover:border-gray-400 rounded-sm transition flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 max-w-3xl">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono font-bold text-[#0B3D6E] bg-blue-50 px-2 py-0.5 border border-blue-200 rounded-sm">
                    {w.externalId}
                  </span>
                  <RiskBadge priority={w.priority} score={w.score} size="sm" />
                  <span className="text-[10px] font-bold text-slate-700 uppercase bg-slate-200 border border-slate-300 px-2 py-0.5 rounded-sm font-mono">
                    STAGE: {w.stage}
                  </span>
                </div>

                <h3 className="text-xs font-bold text-slate-900 leading-snug hover:text-[#0B3D6E] transition">
                  <Link to={`/works/${w.workId}`}>{w.title}</Link>
                </h3>

                <div className="flex items-center gap-4 text-xs text-slate-600 flex-wrap">
                  <span className="flex items-center gap-1 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    {w.districtName}
                  </span>
                  {w.category && (
                    <span className="flex items-center gap-1 font-medium">
                      <Building2 className="w-3.5 h-3.5 text-slate-500" />
                      {w.category}
                    </span>
                  )}
                  {w.sanctionAmount && (
                    <span className="font-mono font-bold text-slate-800">
                      Sanction: ₹{w.sanctionAmount.toLocaleString('en-IN')}
                    </span>
                  )}
                </div>

                {/* Primary Anomaly Signal */}
                {w.topSignalLabel && (
                  <div className="pt-1 flex items-start gap-1.5 text-xs text-amber-900 font-semibold bg-amber-50 border border-amber-200 p-1.5 rounded-sm">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0 mt-0.5" />
                    <span className="break-words min-w-0 leading-snug">{w.topSignalLabel}</span>
                  </div>
                )}
              </div>

              {/* Action Link */}
              <div className="shrink-0 flex items-center gap-2 pt-2 md:pt-0 border-t md:border-t-0 border-gray-200">
                <Link
                  to={`/works/${w.workId}`}
                  className="gov-btn-primary py-1.5 text-xs flex items-center justify-center gap-1 w-full md:w-auto"
                >
                  <span>Investigate</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
