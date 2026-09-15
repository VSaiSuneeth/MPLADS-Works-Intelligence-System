import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { CsvUploader } from '../components/admin/CsvUploader';
import { IngestionHistoryTable } from '../components/admin/IngestionHistoryTable';
import { FileSpreadsheet, RefreshCw, CheckCircle2 } from 'lucide-react';

export const AdminPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: records = [], refetch } = useQuery<any[]>({
    queryKey: ['imports-history'],
    queryFn: async () => {
      const res = await apiClient.get('/imports');
      return res.data;
    },
  });

  const recalculateMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post('/risk/recalculate');
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-queue'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });

  return (
    <div className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-300 pb-3">
        <div>
          <h1 className="text-xl font-serif font-bold text-[#0A2540] tracking-tight flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-[#0B3D6E]" />
            Data Import & Risk Engine Recalculation Portal
          </h1>
          <p className="text-xs text-slate-600">
            Ingest district CSV feeds, review record quality findings, and trigger manual risk engine scoring
          </p>
        </div>

        <button
          onClick={() => recalculateMutation.mutate()}
          disabled={recalculateMutation.isPending}
          className="gov-btn-primary py-2 px-4 text-xs flex items-center gap-1.5 shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${recalculateMutation.isPending ? 'animate-spin' : ''}`} />
          <span>{recalculateMutation.isPending ? 'Recalculating...' : 'Recalculate All Risk Scores'}</span>
        </button>
      </div>

      {recalculateMutation.isSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xs text-xs text-emerald-950 flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
          <span>Risk scores and statistical anomaly distributions recalculated successfully across all works.</span>
        </div>
      )}

      {/* CSV Uploader */}
      <CsvUploader onSuccess={() => refetch()} />

      {/* Import History Table */}
      <IngestionHistoryTable records={records} />
    </div>
  );
};
