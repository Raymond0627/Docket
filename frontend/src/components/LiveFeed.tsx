import React, { useEffect, useRef } from 'react';
import { FileClassification } from '../types';
import { FileText, FileSpreadsheet, Image as ImageIcon, HelpCircle, Check, AlertTriangle } from 'lucide-react';

interface LiveFeedProps {
  files: FileClassification[];
}

export const LiveFeed: React.FC<LiveFeedProps> = ({ files }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [files.length]);

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (ext === 'xlsx' || ext === 'xls') {
      return <FileSpreadsheet className="h-4 w-4 text-emerald-400" />;
    }
    if (['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'].includes(ext || '')) {
      return <ImageIcon className="h-4 w-4 text-violet-400" />;
    }
    return <FileText className="h-4 w-4 text-blue-400" />;
  };

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 overflow-hidden shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800/80 px-5 py-3 bg-slate-50 dark:bg-slate-900/80">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Activity Stream</span>
          <span className="rounded-full bg-slate-200 dark:bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-700 dark:text-slate-300">
            {files.length} processed
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2.5 max-h-[360px]">
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center text-slate-400 dark:text-slate-500">
            <HelpCircle className="h-8 w-8 text-slate-300 dark:text-slate-600 mb-2" />
            <p className="text-sm">Processed files will appear here in real time.</p>
          </div>
        ) : (
          files.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-800/40 p-3 hover:bg-slate-100 dark:hover:bg-slate-800/70 transition"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white dark:bg-slate-800 ring-1 ring-slate-200 dark:ring-slate-700/60 shadow-xs">
                  {getFileIcon(file.file_name)}
                </div>

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-slate-900 dark:text-white">{file.file_name}</span>
                    <span className="shrink-0 rounded-md bg-slate-200 dark:bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-700 dark:text-slate-300 font-medium">
                      {file.owner}
                    </span>
                  </div>

                  <div className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 truncate">
                    <span className="truncate max-w-[280px]">{file.destination_path}</span>
                  </div>
                </div>
              </div>

              {/* Badges */}
              <div className="flex items-center gap-2 shrink-0">
                {file.is_unsorted ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/20">
                    <AlertTriangle className="h-3 w-3" />
                    <span>Unsorted ({Math.round(file.confidence)}%)</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20">
                    <Check className="h-3 w-3" />
                    <span>{file.doc_type} ({Math.round(file.confidence)}%)</span>
                  </span>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
