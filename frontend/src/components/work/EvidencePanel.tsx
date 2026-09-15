import React, { useState } from 'react';
import { FileText, Image, AlertTriangle, Download, Eye, X, MapPin, ShieldCheck, Upload, AlertOctagon, ExternalLink } from 'lucide-react';
import { EvidenceItem } from '../../types';
import { uploadEvidenceApi } from '../../api/client';

interface EvidencePanelProps {
  workId?: string;
  evidenceList: EvidenceItem[];
  missingEvidenceWarning?: boolean;
  onEvidenceUploaded?: () => void;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  workId,
  evidenceList,
  missingEvidenceWarning = false,
  onEvidenceUploaded,
}) => {
  const [selectedArtifact, setSelectedArtifact] = useState<EvidenceItem | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !workId) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      await uploadEvidenceApi(workId, file, 'PHOTOGRAPH');
      setUploadSuccess(`Successfully uploaded '${file.name}' and executed real-time fraud analysis!`);
      if (onEvidenceUploaded) {
        onEvidenceUploaded();
      }
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Failed to upload evidence file.');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDownload = (item: EvidenceItem, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (item.sourceUrl) {
      window.open(item.sourceUrl, '_blank');
      return;
    }
    const content = `MPLADS OFFICIAL EVIDENCE ARTIFACT RECORD
======================================================
Artifact ID   : ${item.id}
File Name     : ${item.fileName}
File Hash     : ${item.fileHash || 'N/A'}
pHash         : ${item.phash || 'N/A'}
EXIF GPS      : ${item.gpsPresent ? `${item.exifLatitude}°, ${item.exifLongitude}°` : 'Absent/Stripped'}
Camera        : ${item.cameraModel || 'N/A'}
Uploaded Date : ${item.uploadedAt || 'N/A'}
======================================================
`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = item.fileName.endsWith('.txt') ? item.fileName : `${item.fileName}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="gov-card p-5 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-gray-200 pb-3 gap-2">
        <div>
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide flex items-center gap-2">
            <span>Physical Evidence & Photo Fraud Intelligence</span>
            <span className="bg-blue-100 text-blue-800 text-[10px] px-2 py-0.5 rounded font-mono font-bold">
              AI Fraud Engine Active
            </span>
          </h2>
          <p className="text-xs text-slate-500">
            SHA-256 Hash Verification, pHash Perceptual Similarity, and Geotag EXIF Provenance Checks
          </p>
        </div>

        <div className="flex items-center gap-3">
          {workId && (
            <label className="cursor-pointer gov-btn-primary text-xs flex items-center gap-1.5 py-1.5 px-3">
              <Upload className="w-3.5 h-3.5" />
              <span>{isUploading ? 'Analyzing...' : 'Upload Site Photo'}</span>
              <input
                type="file"
                accept="image/*,.pdf"
                className="hidden"
                onChange={handleFileUpload}
                disabled={isUploading}
              />
            </label>
          )}
          <span className="text-xs font-mono font-bold bg-[#0B3D6E] text-white px-2.5 py-1 rounded-xs border border-[#0B3D6E]">
            {evidenceList.length} ARTIFACTS
          </span>
        </div>
      </div>

      {uploadSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xs text-xs text-emerald-900 font-medium">
          ✓ {uploadSuccess}
        </div>
      )}

      {uploadError && (
        <div className="p-3 bg-red-50 border border-red-300 rounded-xs text-xs text-red-900 font-medium">
          ⚠ {uploadError}
        </div>
      )}

      {missingEvidenceWarning && (
        <div className="p-3 bg-amber-50 border border-amber-300 rounded-xs text-xs text-amber-950 flex items-start space-x-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <strong className="font-bold uppercase tracking-wider text-amber-950">
              Missing Physical Evidence Warning (COMP-EVID-001):
            </strong>
            <p className="mt-0.5 text-amber-900 font-medium">
              Work stage is marked COMPLETED but lacks geotagged site completion photographs or signed physical inspection certificates.
            </p>
          </div>
        </div>
      )}

      {evidenceList.length === 0 ? (
        <div className="p-8 text-center bg-slate-50 border border-gray-300 rounded-xs space-y-2">
          <FileText className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="text-xs font-bold text-slate-700 uppercase">No physical evidence artifacts uploaded yet.</p>
          <p className="text-[11px] text-slate-500">Upload a geotagged photo to test cross-work duplicate fraud detection.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {evidenceList.map((item) => {
            const fileName = item.fileName || 'evidence.jpg';
            const fmt = (item.fileFormat || fileName.split('.').pop() || '').toLowerCase();
            const isImage = fmt.includes('png') || fmt.includes('jpg') || fmt.includes('jpeg') || fmt.includes('webp');
            const Icon = isImage ? Image : FileText;
            const flags = item.fraudFlags || [];
            const hasFraud = flags.length > 0;
            const highestSeverity = flags.find(f => f.severity === 'CRITICAL') ? 'CRITICAL' : flags.find(f => f.severity === 'HIGH') ? 'HIGH' : flags.find(f => f.severity === 'MEDIUM') ? 'MEDIUM' : 'LOW';

            return (
              <div
                key={item.id}
                className={`bg-white border rounded-xs p-4 space-y-3 transition shadow-xs ${
                  hasFraud && (highestSeverity === 'CRITICAL' || highestSeverity === 'HIGH')
                    ? 'border-red-400 bg-red-50/20'
                    : hasFraud
                    ? 'border-amber-300 bg-amber-50/20'
                    : 'border-gray-300 hover:border-[#0B3D6E]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start space-x-3">
                    <div className="w-12 h-12 rounded-xs bg-slate-100 border border-slate-300 flex items-center justify-center shrink-0 overflow-hidden relative">
                      {isImage && item.sourceUrl ? (
                        <img src={item.sourceUrl} alt={fileName} className="w-full h-full object-cover" />
                      ) : (
                        <Icon className="w-6 h-6 text-slate-600" />
                      )}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-xs font-bold text-slate-900">{fileName}</h3>
                        <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-100 text-slate-700 border border-slate-300 rounded-xs uppercase">
                          {item.evidenceType || 'PHOTOGRAPH'}
                        </span>
                        {hasFraud && (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-xs uppercase border flex items-center gap-1 ${
                            highestSeverity === 'CRITICAL' ? 'bg-red-700 text-white border-red-800' :
                            highestSeverity === 'HIGH' ? 'bg-red-600 text-white border-red-700' :
                            highestSeverity === 'MEDIUM' ? 'bg-amber-600 text-white border-amber-700' :
                            'bg-blue-600 text-white border-blue-700'
                          }`}>
                            <AlertOctagon className="w-3 h-3" />
                            <span>{highestSeverity} FRAUD ALERT</span>
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-600 font-mono">
                        {item.fileSizeBytes && (
                          <span>SIZE: {(item.fileSizeBytes / 1024).toFixed(1)} KB</span>
                        )}
                        {item.cameraModel && (
                          <span>CAMERA: {item.cameraModel}</span>
                        )}
                        {item.gpsPresent && item.exifLatitude != null ? (
                          <span className="text-emerald-700 font-bold flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-emerald-600 inline" />
                            GPS EXIF: {Number(item.exifLatitude).toFixed(4)}°, {Number(item.exifLongitude).toFixed(4)}°
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">GPS EXIF: Absent / Stripped</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5 shrink-0">
                    <button
                      onClick={() => setSelectedArtifact(item)}
                      className="p-1.5 text-slate-700 hover:text-white hover:bg-[#0B3D6E] bg-slate-100 border border-gray-300 rounded-xs transition flex items-center gap-1 text-[10px] font-bold"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                    <button
                      onClick={(e) => handleDownload(item, e)}
                      className="p-1.5 text-slate-700 hover:text-white hover:bg-emerald-700 bg-slate-100 border border-gray-300 rounded-xs transition flex items-center gap-1 text-[10px] font-bold"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Fraud Banners for each Fraud Flag */}
                {flags.map((flag) => (
                  <div
                    key={flag.id}
                    className={`p-3 rounded-xs border text-xs space-y-1.5 ${
                      flag.severity === 'CRITICAL'
                        ? 'bg-red-50 border-red-300 text-red-950'
                        : flag.severity === 'HIGH'
                        ? 'bg-orange-50 border-orange-300 text-orange-950'
                        : flag.severity === 'MEDIUM'
                        ? 'bg-amber-50 border-amber-300 text-amber-950'
                        : 'bg-blue-50 border-blue-300 text-blue-950'
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
                        <span className="uppercase tracking-wider">
                          ⚠ CROSS-WORK FRAUD ALERT: {flag.flagType.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <span className="font-mono text-[11px] bg-white px-2 py-0.5 border rounded-xs">
                        CONFIDENCE: {flag.confidenceScore}% | SEVERITY: {flag.severity}
                      </span>
                    </div>

                    <p className="text-xs font-medium leading-relaxed">
                      {flag.message}
                    </p>

                    {flag.matchedWorkId && (
                      <div className="pt-1 flex items-center gap-2 text-[11px] font-semibold">
                        <span>Matched Work:</span>
                        <a
                          href={`/works/${flag.matchedWorkId}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[#0B3D6E] underline hover:text-blue-900 font-mono inline-flex items-center gap-1"
                        >
                          <span>{flag.matchedWorkExternalId || flag.matchedWorkId} ({flag.matchedWorkTitle || 'View Work Detail'})</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {/* Artifact Lightbox Modal */}
      {selectedArtifact && (
        <div className="fixed inset-0 z-50 bg-slate-900/80 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-300 border-t-4 border-t-[#0B3D6E] rounded-xs max-w-3xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-gray-200 pb-3">
              <div>
                <span className="text-[10px] font-mono font-bold text-white bg-[#0B3D6E] px-2 py-0.5 rounded-xs uppercase">
                  {selectedArtifact.evidenceType}
                </span>
                <h2 className="text-sm font-bold text-slate-900 mt-1">{selectedArtifact.fileName}</h2>
              </div>
              <button
                onClick={() => setSelectedArtifact(null)}
                className="p-1 text-slate-500 hover:text-slate-900 rounded-xs transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-950 p-4 rounded-xs border border-slate-800 flex flex-col items-center justify-center space-y-3 relative">
              {selectedArtifact.sourceUrl ? (
                <img
                  src={selectedArtifact.sourceUrl}
                  alt={selectedArtifact.fileName}
                  className="max-h-[350px] object-contain rounded border border-slate-700"
                />
              ) : (
                <div className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xs p-4 text-center space-y-3">
                  <Image className="w-12 h-12 text-blue-400 mx-auto" />
                  <p className="text-xs font-mono text-slate-300">File: {selectedArtifact.fileName}</p>
                </div>
              )}

              <div className="w-full p-3 bg-slate-900 border border-slate-800 rounded-xs text-[11px] font-mono text-emerald-400 space-y-1">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>
                    GPS EXIF: {selectedArtifact.gpsPresent && selectedArtifact.exifLatitude != null ? `${selectedArtifact.exifLatitude}° N, ${selectedArtifact.exifLongitude}° E` : 'Absent / Stripped'}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>SHA-256 Hash: {selectedArtifact.fileHash || 'N/A'}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Perceptual pHash: {selectedArtifact.phash || 'N/A'}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-gray-200">
              <button
                type="button"
                onClick={() => setSelectedArtifact(null)}
                className="gov-btn-secondary text-xs"
              >
                Close Preview
              </button>
              <button
                type="button"
                onClick={() => handleDownload(selectedArtifact)}
                className="gov-btn-primary text-xs flex items-center gap-1"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Artifact File</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
