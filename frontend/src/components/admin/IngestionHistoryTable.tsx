import React from 'react';
import { IngestionRecord } from '../../types';
import { FileCheck2, User } from 'lucide-react';

interface IngestionHistoryProps {
  records: IngestionRecord[];
}

export const IngestionHistoryTable: React.FC<IngestionHistoryProps> = ({ records }) => {
  return (
    <div className="gov-card p-5 space-y-4">
      <div className="border-b border-gray-200 pb-3">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
          <FileCheck2 className="w-4 h-4 text-[#0B3D6E]" />
          Historical Dataset Import Log
        </h2>
        <p className="text-xs text-slate-500">
          Audit trail of past CSV ingestion runs and record quality findings
        </p>
      </div>

      {records.length === 0 ? (
        <div className="p-8 text-center bg-slate-50 border border-gray-300 rounded-xs space-y-1">
          <p className="text-xs font-bold text-slate-800 uppercase">No import history found</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="gov-table text-xs">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Imported Date</th>
                <th>Imported By</th>
                <th className="text-right">Total Rows</th>
                <th className="text-right">Accepted</th>
                <th className="text-right">Rejected</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {records.map((r) => (
                <tr key={r.id}>
                  <td className="font-mono font-bold text-[#0B3D6E]">{r.fileName}</td>
                  <td className="font-mono">{new Date(r.importedAt).toLocaleString()}</td>
                  <td className="font-bold text-slate-900">
                    <div className="flex items-center gap-1">
                      <User className="w-3.5 h-3.5 text-[#0B3D6E]" />
                      <span>{r.importedBy}</span>
                    </div>
                  </td>
                  <td className="text-right font-mono font-bold">{r.totalRows}</td>
                  <td className="text-right font-mono font-bold text-emerald-700">{r.acceptedRows}</td>
                  <td className="text-right font-mono font-bold text-red-700">{r.rejectedRows}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
