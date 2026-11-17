import React from 'react';
import { Job, FileClassification } from '../types';
import { X, CloudUpload, CheckCircle, Code } from 'lucide-react';

interface ECMSModalProps {
  job: Job;
  files: FileClassification[];
  isOpen: boolean;
  onClose: () => void;
}

export const ECMSModal: React.FC<ECMSModalProps> = ({ job, files, isOpen, onClose }) => {
  if (!isOpen) return null;

  const sortedFiles = files.filter((f) => !f.is_unsorted);

  // Sample JSON payload that the ECMS adapter will stream
  const samplePayload = {
    job_id: job.id,
    output_hierarchy: job.folder_template,
    total_sorted_documents: sortedFiles.length,
    documents: sortedFiles.slice(0, 4).map((f) => ({
      file_name: f.file_name,
      document_type: f.doc_type,
      owner_entity: f.owner,
      destination_path: f.destination_path,
      confidence_score: f.confidence,
    })),
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 px-6 py-4 bg-slate-50 dark:bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/20">
              <CloudUpload className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>Upload to ECMS</span>
                <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/20">
                  Phase 3 Ready
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Enterprise Content Management System Dispatcher
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          
          {/* Status Alert Banner */}
          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4 space-y-2">
            <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-semibold text-sm">
              <CheckCircle className="h-4 w-4" />
              <span>Tree Structure & Metadata Packaged</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Your {sortedFiles.length} organized files and metadata tags are structured and ready for direct upload to your ECMS repository.
            </p>
          </div>

          {/* Supported ECMS Adapters */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Ready ECMS Target Connectors (Phase 3)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
              {[
                { name: 'Microsoft SharePoint', type: 'REST / Graph API' },
                { name: 'Laserfiche', type: 'Document Repo' },
                { name: 'Alfresco ECM', type: 'CMIS / Webhook' },
                { name: 'OpenText', type: 'Enterprise API' },
                { name: 'Custom REST API', type: 'JSON Stream' },
                { name: 'Local File Archive', type: 'Active' },
              ].map((ecms, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 p-3"
                >
                  <div className="font-semibold text-slate-900 dark:text-white">{ecms.name}</div>
                  <div className="mt-0.5 text-[10px] text-slate-500 dark:text-slate-400">{ecms.type}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Export Payload Preview */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-700 dark:text-slate-300 font-semibold">
              <span className="flex items-center gap-1.5">
                <Code className="h-3.5 w-3.5 text-indigo-500" />
                <span>Payload Metadata Schema Preview</span>
              </span>
              <span className="font-mono text-slate-400 text-[11px]">{sortedFiles.length} items</span>
            </div>
            <pre className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-950 p-3 text-[11px] font-mono text-slate-700 dark:text-slate-300 overflow-x-auto max-h-48">
              {JSON.stringify(samplePayload, null, 2)}
            </pre>
          </div>

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-800 px-6 py-4 bg-slate-50 dark:bg-slate-950/60">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Phase 1 & 2 complete. Pluggable adapter hooks in place.
          </span>
          <button
            onClick={onClose}
            className="rounded-xl bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white px-5 py-2 text-xs font-semibold shadow-xs transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
