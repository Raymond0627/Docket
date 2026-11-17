import React, { useState } from 'react';
import { FolderUp, ArrowRight, FolderSearch, AlertCircle, Files } from 'lucide-react';
import { api } from '../services/api';

export interface DroppedItem {
  file: File;
  relativePath: string;
}

interface DropZoneProps {
  onStartJob: (folderPath: string) => void;
  onDropFiles: (items: DroppedItem[]) => void;
  isProcessing: boolean;
  disabled?: boolean;
}

async function extractFilesFromDataTransfer(dataTransfer: DataTransfer): Promise<DroppedItem[]> {
  const items = dataTransfer.items;
  const results: DroppedItem[] = [];

  async function traverseEntry(entry: any, path: string = ''): Promise<void> {
    if (!entry) return;
    if (entry.isFile) {
      await new Promise<void>((resolve) => {
        entry.file(
          (file: File) => {
            results.push({
              file,
              relativePath: path ? `${path}/${file.name}` : file.name,
            });
            resolve();
          },
          () => resolve()
        );
      });
    } else if (entry.isDirectory) {
      const dirReader = entry.createReader();
      const readAllEntries = async (): Promise<any[]> => {
        let allEntries: any[] = [];
        let batch: any[];
        do {
          batch = await new Promise<any[]>((resolve) => {
            dirReader.readEntries(
              (entries: any[]) => resolve(entries),
              () => resolve([])
            );
          });
          allEntries = allEntries.concat(batch);
        } while (batch.length > 0);
        return allEntries;
      };

      const entries = await readAllEntries();
      const newPath = path ? `${path}/${entry.name}` : entry.name;
      for (const child of entries) {
        await traverseEntry(child, newPath);
      }
    }
  }

  if (items && items.length > 0 && typeof items[0].webkitGetAsEntry === 'function') {
    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry();
      if (entry) {
        await traverseEntry(entry);
      }
    }
  } else if (dataTransfer.files && dataTransfer.files.length > 0) {
    for (let i = 0; i < dataTransfer.files.length; i++) {
      const file = dataTransfer.files[i];
      results.push({ file, relativePath: file.name });
    }
  }

  return results;
}

export const DropZone: React.FC<DropZoneProps> = ({ onStartJob, onDropFiles, isProcessing, disabled }) => {
  const [folderPath, setFolderPath] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dropStatus, setDropStatus] = useState<string | null>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!folderPath.trim()) {
      setError('Please enter or select a valid folder path');
      return;
    }
    setError(null);
    onStartJob(folderPath.trim());
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && !isProcessing) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled || isProcessing) return;

    setError(null);

    // 1. Check for dropped folder path string
    const textData = e.dataTransfer.getData('text/plain');
    if (textData && (textData.includes(':\\') || textData.startsWith('/') || textData.startsWith('\\\\'))) {
      const cleanPath = textData.trim().replace(/^"|"$/g, '');
      setFolderPath(cleanPath);
      onStartJob(cleanPath);
      return;
    }

    // 2. Extract files & recursively traverse dropped folders
    try {
      setDropStatus('Scanning dropped items...');
      const droppedItems = await extractFilesFromDataTransfer(e.dataTransfer);
      setDropStatus(null);

      if (droppedItems.length === 0) {
        setError('No supported files found in dropped items.');
        return;
      }

      // Immediately pass to upload & process handler
      onDropFiles(droppedItems);
    } catch (err: any) {
      setDropStatus(null);
      setError(`Failed to process dropped items: ${err.message}`);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed p-8 transition-all duration-200 text-center ${
          isDragging
            ? 'border-brand-500 bg-brand-500/10 scale-[1.01]'
            : 'border-slate-300 dark:border-slate-700/80 bg-white dark:bg-slate-900/60 hover:border-slate-400 dark:hover:border-slate-600 shadow-sm'
        }`}
      >
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 ring-1 ring-brand-500/20">
            {isDragging ? <Files className="h-8 w-8 animate-bounce" /> : <FolderUp className="h-8 w-8 animate-pulse" />}
          </div>

          <div className="space-y-1">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              {isDragging ? 'Drop folders or files now' : 'Drag & drop folder or multiple files here'}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Drop whole directories or select multiple PDFs, Word documents, Excel sheets, and scans.
            </p>
          </div>

          {dropStatus && (
            <div className="text-xs text-brand-600 dark:text-brand-400 animate-pulse font-medium">
              {dropStatus}
            </div>
          )}

          {/* Windows Path Input & Native Browse Button */}
          <form onSubmit={handleSubmit} className="mt-4 flex w-full max-w-xl items-center gap-2">
            <div className="relative flex-1">
              <FolderSearch className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 dark:text-slate-500" />
              <input
                type="text"
                placeholder="Enter path or click Browse..."
                value={folderPath}
                onChange={(e) => {
                  setFolderPath(e.target.value);
                  if (error) setError(null);
                }}
                disabled={isProcessing || disabled}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 pl-10 pr-24 py-2.5 text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 transition focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
              />
              <button
                type="button"
                onClick={async () => {
                  try {
                    const picked = await api.selectFolder();
                    if (picked) {
                      setFolderPath(picked);
                      setError(null);
                    }
                  } catch (e) {
                    console.error(e);
                  }
                }}
                disabled={isProcessing || disabled}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-lg border border-slate-200 dark:border-transparent bg-slate-200 hover:bg-slate-300 dark:bg-slate-700/80 dark:hover:bg-slate-600 px-2.5 py-1 text-xs font-medium text-slate-700 dark:text-slate-200 transition"
              >
                Browse...
              </button>
            </div>

            <button
              type="submit"
              disabled={isProcessing || disabled || !folderPath.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-brand-500/20 transition hover:bg-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>Start Organizing</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="mt-2 flex items-center gap-1.5 text-xs text-rose-500 dark:text-rose-400">
              <AlertCircle className="h-3.5 w-3.5" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
