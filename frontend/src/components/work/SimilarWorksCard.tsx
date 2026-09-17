import React from 'react';
import { Link } from 'react-router-dom';
import { SimilarityCandidate } from '../../types';
import { Layers, ArrowRight, CheckCircle2, AlertOctagon } from 'lucide-react';

interface SimilarWorksProps {
  candidates: SimilarityCandidate[];
}

export const SimilarWorksCard: React.FC<SimilarWorksProps> = ({ candidates }) => {
  return (
    <div className="gov-card p-5 space-y-5">
      <div className="flex items-center justify-between border-b border-gray-200 pb-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#0B3D6E]" />
            Candidate Duplicate Sanction Matching
          </h2>
          <p className="text-xs text-slate-500">
            6-feature vector analysis comparing text similarity, Haversine geo-distance, and cost delta
          </p>
        </div>
        <span className="text-xs font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300 px-2.5 py-1 rounded-xs">
          {candidates.length} MATCHES FLAGGED
        </span>
      </div>

      {candidates.length === 0 ? (
        <div className="p-8 text-center bg-slate-50 border border-gray-300 rounded-xs space-y-1">
          <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto" />
          <p className="text-xs font-bold text-slate-800 uppercase">No Candidate Duplicate Works Identified</p>
          <p className="text-xs text-slate-600">This work has no high-similarity vector overlap with other district sanctions.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((cand) => {
            const pct = (cand.similarityScore * 100).toFixed(1);
            const fb = cand.featureBreakdown;
            const targetWorkId = cand.workId || cand.candidateWorkId;

            return (
              <div
                key={targetWorkId || cand.externalId}
                className="p-4 bg-slate-50 border border-gray-300 rounded-xs space-y-3 text-xs"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-gray-200 pb-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-xs bg-blue-50 text-[#0B3D6E] border border-blue-200 px-2 py-0.5 rounded-xs">
                        {cand.externalId}
                      </span>
                      <span className="font-mono font-bold text-amber-900 bg-amber-100 border border-amber-300 px-2 py-0.5 rounded-xs">
                        {pct}% SIMILARITY
                      </span>
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 bg-slate-200 text-slate-800 rounded-xs border border-gray-300">
                        {cand.candidateLabel.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <h3 className="font-bold text-slate-900 text-xs mt-1 hover:text-[#0B3D6E] transition">
                      <Link to={`/works/${targetWorkId}`}>{cand.title}</Link>
                    </h3>
                  </div>

                  <Link
                    to={`/works/${targetWorkId}`}
                    className="gov-btn-secondary py-1 px-3 text-xs shrink-0 flex items-center gap-1"
                  >
                    <span>Compare Work</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>

                {/* 6-Feature Score Breakdown Diff */}
                <div className="grid grid-cols-2 md:grid-cols-6 gap-2 bg-white p-3 border border-gray-300 rounded-xs text-[11px] font-mono">
                  <div>
                    <span className="text-slate-500 text-[9px] block uppercase font-bold">Text TF-IDF</span>
                    <span className="font-bold text-slate-900">{fb.textSimilarity.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] block uppercase font-bold">Geo Proximity</span>
                    <span className="font-bold text-slate-900">{fb.geoProximity.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] block uppercase font-bold">Category</span>
                    <span className="font-bold text-slate-900">{fb.categoryMatch.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] block uppercase font-bold">Agency</span>
                    <span className="font-bold text-slate-900">{fb.agencyMatch.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] block uppercase font-bold">Cost Delta</span>
                    <span className="font-bold text-slate-900">{fb.costSimilarity.toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[9px] block uppercase font-bold">Date Overlap</span>
                    <span className="font-bold text-slate-900">{fb.dateOverlap.toFixed(1)}%</span>
                  </div>
                </div>

                <div className="text-[10px] text-amber-900 bg-amber-50 p-2 border border-amber-200 rounded-xs flex items-center gap-1.5 font-medium">
                  <AlertOctagon className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                  <span>Candidate duplicate flags require physical site verification by district officers before administrative action.</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
