import React, { useState, useEffect, useRef } from 'react';
import { DropZone, DroppedItem } from '../components/DropZone';
import { ProgressBar } from '../components/ProgressBar';
import { LiveFeed } from '../components/LiveFeed';
import { api } from '../services/api';
import { FileClassification, Job, LiveJobEvent } from '../types';
import { 
  Sparkles, 
  UploadCloud, 
  CheckCircle2, 
  ArrowRight, 
  FolderOpen, 
  RotateCcw,
  AlertTriangle
} from 'lucide-react';

interface DropScreenProps {
  onJobCompleted: (job: Job) => void;
}

export const DropScreen: React.FC<DropScreenProps> = ({ onJobCompleted }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [completedJob, setCompletedJob] = useState<Job | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [processedCount, setProcessedCount] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [liveFiles, setLiveFiles] = useState<FileClassification[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const timerRef = useRef<any>(null);
  const streamCleanupRef = useRef<(() => void) | null>(null);

  // Close the SSE stream if the screen ever unmounts (prevents leaked connections).
  useEffect(() => {
    return () => {
      if (streamCleanupRef.current) streamCleanupRef.current();
    };
  }, []);

  useEffect(() => {
    if (isProcessing) {
      const start = Date.now();
      timerRef.current = setInterval(() => {
        setElapsedSeconds((Date.now() - start) / 1000);
      }, 200);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isProcessing]);

  const startStream = (jobId: string) => {
    // Close any previous stream before starting a new one.
    if (streamCleanupRef.current) streamCleanupRef.current();

    streamCleanupRef.current = api.subscribeJobStream(
      jobId,
      (event: LiveJobEvent) => {
        if (event.event === 'job_started') {
          setTotalFiles(event.total_files);
          setUploadStatus(null);
        } else if (event.event === 'file_processed') {
          setProcessedCount(event.processed_count);
          setTotalFiles(event.total_files);
          setLiveFiles((prev) => [...prev, event.file]);
        } else if (event.event === 'job_completed') {
          setIsProcessing(false);
          setUploadStatus(null);
          setIsDone(true);
          streamCleanupRef.current = null;
          api.getJob(jobId).then((freshJob) => {
            setCompletedJob(freshJob);
          });
        } else if (event.event === 'job_error') {
          setIsProcessing(false);
          setUploadStatus(null);
          streamCleanupRef.current = null;
          alert(`Error processing job: ${event.error}`);
        }
      },
      (err) => {
        console.error('Job stream error:', err);
        setIsProcessing(false);
        setUploadStatus(null);
        streamCleanupRef.current = null;
      }
    );
  };

  const handleStartJob = async (folderPath: string) => {
    try {
      setIsProcessing(true);
      setIsDone(false);
      setCompletedJob(null);
      setUploadStatus(null);
      setProcessedCount(0);
      setTotalFiles(0);
      setLiveFiles([]);
      setElapsedSeconds(0);

      const job = await api.createJob({ source_path: folderPath });
      startStream(job.id);
    } catch (err: any) {
      setIsProcessing(false);
      setIsDone(false);
      setUploadStatus(null);
      alert(err.message || 'Failed to start job');
    }
  };

  const handleDropFiles = async (items: DroppedItem[]) => {
    try {
      setIsProcessing(true);
      setIsDone(false);
      setCompletedJob(null);
      setUploadStatus(`Preparing & uploading ${items.length} dropped file(s)...`);
      setProcessedCount(0);
      setTotalFiles(items.length);
      setLiveFiles([]);
      setElapsedSeconds(0);

      const job = await api.uploadFiles(items);
      startStream(job.id);
    } catch (err: any) {
      setIsProcessing(false);
      setIsDone(false);
      setUploadStatus(null);
      alert(err.message || 'Failed to process dropped files');
    }
  };

  const handleReset = () => {
    setIsProcessing(false);
    setIsDone(false);
    setCompletedJob(null);
    setProcessedCount(0);
    setTotalFiles(0);
    setLiveFiles([]);
    setElapsedSeconds(0);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Organize Documents
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-500/10 px-2.5 py-0.5 text-xs font-semibold text-brand-600 dark:text-brand-400 ring-1 ring-brand-500/20">
              <Sparkles className="h-3 w-3" /> CPU Engine
            </span>
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Drag & drop a folder, select multiple files, or browse your local disk to classify and sort automatically.
          </p>
        </div>
      </div>

      {/* Drop Zone Area (Shown when not in completed state) */}
      {!isDone ? (
        <DropZone
          onStartJob={handleStartJob}
          onDropFiles={handleDropFiles}
          isProcessing={isProcessing}
        />
      ) : (
        /* Organizing Done Banner */
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-8 text-center space-y-5 shadow-lg animate-in fade-in zoom-in-95 duration-200">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 ring-4 ring-emerald-500/20">
            <CheckCircle2 className="h-9 w-9" />
          </div>

          <div className="space-y-1.5">
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
              Organizing Done!
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 max-w-md mx-auto">
              Processed <span className="font-semibold text-slate-900 dark:text-white">{totalFiles}</span> files in{' '}
              <span className="font-mono font-semibold">{elapsedSeconds.toFixed(1)}s</span>.
            </p>
          </div>

          {completedJob && (
            <div className="flex flex-wrap items-center justify-center gap-3 text-xs">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 px-3 py-1 font-semibold border border-emerald-500/30">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {completedJob.sorted_files} Sorted Successfully
              </span>
              {completedJob.unsorted_files > 0 && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-300 px-3 py-1 font-semibold border border-amber-500/30">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  {completedJob.unsorted_files} Need Review
                </span>
              )}
            </div>
          )}

          {/* Action Buttons to let user go manually */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={() => completedJob && onJobCompleted(completedJob)}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white px-6 py-3 text-sm font-semibold shadow-lg shadow-brand-500/25 transition transform hover:scale-102"
            >
              <span>View Results & Review Documents</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            {completedJob && (
              <button
                onClick={() => api.openFolder(completedJob.output_path)}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 px-4 py-3 text-sm font-medium shadow-xs transition"
              >
                <FolderOpen className="h-4 w-4 text-brand-500" />
                <span>Open Folder in Explorer</span>
              </button>
            )}

            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-4 py-3 text-sm font-medium shadow-xs transition"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Organize Another Folder</span>
            </button>
          </div>
        </div>
      )}

      {/* Uploading Status Banner */}
      {uploadStatus && (
        <div className="flex items-center justify-center gap-2 rounded-xl bg-brand-500/10 border border-brand-500/20 p-3 text-sm text-brand-600 dark:text-brand-300 animate-pulse">
          <UploadCloud className="h-4 w-4" />
          <span>{uploadStatus}</span>
        </div>
      )}

      {/* Progress & Live Feed */}
      {(isProcessing || liveFiles.length > 0) && (
        <div className="space-y-4">
          <ProgressBar
            processed={processedCount}
            total={totalFiles}
            elapsedSeconds={elapsedSeconds}
          />
          <LiveFeed files={liveFiles} />
        </div>
      )}
    </div>
  );
};
