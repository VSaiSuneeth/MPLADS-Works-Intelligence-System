import React, { useState } from 'react';
import { Upload, CheckCircle2, AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { apiClient } from '../../api/client';

interface CsvUploaderProps {
  onSuccess: () => void;
}

export const CsvUploader: React.FC<CsvUploaderProps> = ({ onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [report, setReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setReport(null);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    setReport(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.post('/imports', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setReport(res.data);
      setFile(null);
      onSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to process CSV file upload.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="gov-card p-5 space-y-4">
      <div className="border-b border-gray-200 pb-3">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
          <Upload className="w-4 h-4 text-[#0B3D6E]" />
          MPLADS District Works CSV Dataset Ingestion
        </h2>
        <p className="text-xs text-slate-500">
          Upload district sanction CSV feeds with automatic SHA-256 record deduplication and data quality checks
        </p>
      </div>

      <form onSubmit={handleUpload} className="space-y-4">
        <div className="border-2 border-dashed border-gray-300 hover:border-[#0B3D6E] p-6 text-center rounded-xs bg-slate-50 transition">
          <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
            id="csv-file-input"
          />
          <label
            htmlFor="csv-file-input"
            className="gov-btn-secondary py-1.5 px-4 text-xs cursor-pointer inline-flex items-center gap-1.5"
          >
            <span>Choose CSV File</span>
          </label>

          {file && (
            <p className="text-xs font-mono font-bold text-[#0B3D6E] mt-2">
              Selected File: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-300 rounded-xs text-xs text-red-950 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-700 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!file || uploading}
            className="gov-btn-primary py-2 px-4 text-xs inline-flex items-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${uploading ? 'animate-spin' : ''}`} />
            <span>{uploading ? 'Ingesting Dataset...' : 'Start Data Ingestion'}</span>
          </button>
        </div>
      </form>

      {/* Live Ingestion Report Card */}
      {report && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-xs text-xs space-y-2">
          <div className="flex items-center space-x-2 text-emerald-950 font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-700" />
            <span className="uppercase tracking-wide">Data Ingestion Run Complete</span>
          </div>
          <div className="grid grid-cols-3 gap-2 font-mono text-[11px] pt-1">
            <div className="bg-white p-2 border border-emerald-200 rounded-xs">
              <span className="text-slate-500 block text-[9px]">TOTAL ROWS</span>
              <strong className="text-slate-900">{report.totalRows}</strong>
            </div>
            <div className="bg-white p-2 border border-emerald-200 rounded-xs">
              <span className="text-slate-500 block text-[9px]">ACCEPTED</span>
              <strong className="text-emerald-700">{report.acceptedRows}</strong>
            </div>
            <div className="bg-white p-2 border border-emerald-200 rounded-xs">
              <span className="text-slate-500 block text-[9px]">REJECTED</span>
              <strong className="text-red-700">{report.rejectedRows}</strong>
            </div>
          </div>
          <p className="text-[10px] text-emerald-900 font-mono">
            SHA-256 Idempotency: Re-uploaded records were updated without creating duplicate work rows.
          </p>
        </div>
      )}
    </div>
  );
};
