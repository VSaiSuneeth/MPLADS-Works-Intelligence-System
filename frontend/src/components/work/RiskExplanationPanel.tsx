import React from 'react';
import { RiskSignal } from '../../types';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';

interface RiskExplanationProps {
  signals: RiskSignal[];
  score: number;
  confidence: number;
}

export const RiskExplanationPanel: React.FC<RiskExplanationProps> = ({
  signals,
  score,
  confidence,
}) => {
  return (
    <div className="gov-card p-5 space-y-5">
      <div className="flex items-center justify-between border-b border-gray-200 pb-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-700" />
            Explainable Risk & Anomaly Signals
          </h2>
          <p className="text-xs text-slate-500">
            Transparent breakdown of deterministic compliance rules and statistical anomaly scores
          </p>
        </div>
        <div className="text-right font-mono text-xs">
          <span className="text-slate-500 block text-[10px] uppercase font-bold">Confidence Score</span>
          <span className="font-bold text-[#0B3D6E]">{confidence.toFixed(1)}% High Reliability</span>
        </div>
      </div>

      {signals.length === 0 ? (
        <div className="p-8 text-center bg-emerald-50 border border-emerald-200 rounded-xs text-emerald-950 space-y-1">
          <CheckCircle2 className="w-6 h-6 text-emerald-700 mx-auto" />
          <p className="text-xs font-bold uppercase">No Compliance Anomalies Flagged</p>
          <p className="text-xs text-emerald-800">This work currently satisfies all standard milestone and financial progress checks.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {signals.map((sig, idx) => (
            <div
              key={idx}
              className="p-4 bg-slate-50 border border-gray-300 rounded-xs space-y-2 text-xs"
            >
              <div className="flex items-center justify-between flex-wrap gap-2 border-b border-gray-200 pb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold text-xs bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded-xs">
                    {sig.code}
                  </span>
                  <span className="font-bold text-slate-900 uppercase">{sig.type.replace(/_/g, ' ')}</span>
                </div>
                <span className="font-mono font-bold text-amber-800 bg-amber-50 px-2 py-0.5 border border-amber-200 rounded-xs">
                  +{sig.contribution} Risk Points
                </span>
              </div>

              <div>
                <strong className="text-slate-900 block font-bold mb-0.5">What Happened:</strong>
                <p className="text-slate-800 font-medium leading-relaxed">{sig.whatHappened}</p>
              </div>

              {sig.whyItMatters && (
                <div>
                  <strong className="text-slate-900 block font-bold mb-0.5">Why It Matters:</strong>
                  <p className="text-slate-700 leading-relaxed">{sig.whyItMatters}</p>
                </div>
              )}

              {sig.recommendedAction && (
                <div className="pt-1.5 border-t border-gray-200 flex items-start space-x-2 text-slate-800">
                  <Info className="w-4 h-4 text-[#0B3D6E] shrink-0 mt-0.5" />
                  <div>
                    <strong className="font-bold text-[#0B3D6E] uppercase tracking-wider text-[10px] block">
                      Recommended Officer Action:
                    </strong>
                    <span>{sig.recommendedAction}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
