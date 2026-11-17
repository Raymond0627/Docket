import React from 'react';
import { Clock, Zap } from 'lucide-react';

interface ProgressBarProps {
  processed: number;
  total: number;
  elapsedSeconds?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ processed, total, elapsedSeconds = 0 }) => {
  const percent = total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : 0;
  const rate = elapsedSeconds > 0 ? (processed / elapsedSeconds).toFixed(1) : '0';

  return (
    <div className="w-full space-y-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 p-5 shadow-sm">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-brand-500 animate-ping" />
          <span className="font-medium text-slate-900 dark:text-white">Live Processing</span>
          <span className="rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs text-slate-700 dark:text-slate-300 font-mono">
            {processed} / {total} files
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1">
            <Zap className="h-3.5 w-3.5 text-amber-500 dark:text-amber-400" />
            <span>{rate} files/sec</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5 text-slate-400" />
            <span>{elapsedSeconds.toFixed(1)}s</span>
          </div>
          <span className="font-semibold text-brand-600 dark:text-brand-400 font-mono text-sm">{percent}%</span>
        </div>
      </div>

      {/* Progress Bar Container */}
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-600 via-indigo-500 to-emerald-400 transition-all duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
};
