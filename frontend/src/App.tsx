import React, { useState, useEffect } from 'react';
import { DropScreen } from './screens/DropScreen';
import { ResultScreen } from './screens/ResultScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { Job } from './types';
import { FolderUp, CheckCircle, Settings, Sun, Moon } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'drop' | 'result' | 'settings'>('drop');
  const [lastCompletedJob, setLastCompletedJob] = useState<Job | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('docket_theme') as 'dark' | 'light') || 'light';
  });

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('docket_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  };

  const handleJobCompleted = (job: Job) => {
    setLastCompletedJob(job);
    setActiveTab('result');
  };

  return (
    <div className="flex h-full flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Top Desktop Navigation Bar */}
      <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-900 px-6">
        <div className="flex items-center gap-3">
          <img
            src="/lumeed-logo.png"
            alt="Lumeed"
            className="h-11 w-11 rounded-lg object-contain"
          />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-slate-900 dark:text-white text-base">Docket</span>
              <span className="rounded-full bg-brand-500/10 px-2 py-0.5 text-[11px] font-semibold text-brand-600 dark:text-brand-400 ring-1 ring-brand-500/20">
                Lean Core
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">by Lumeed — Local OCR & Automated Document Router</p>
          </div>
        </div>

        {/* 3 Screen Navigation Tabs */}
        <nav className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab('drop')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
              activeTab === 'drop'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <FolderUp className="h-4 w-4" />
            <span>1. Organize</span>
          </button>

          <button
            onClick={() => setActiveTab('result')}
            disabled={!lastCompletedJob}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
              activeTab === 'result'
                ? 'bg-brand-600 text-white shadow-sm'
                : lastCompletedJob
                ? 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                : 'text-slate-400 dark:text-slate-600 cursor-not-allowed opacity-50'
            }`}
          >
            <CheckCircle className="h-4 w-4" />
            <span>2. Results</span>
            {lastCompletedJob && (
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            )}
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold transition ${
              activeTab === 'settings'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <Settings className="h-4 w-4" />
            <span>3. Settings</span>
          </button>
        </nav>

        {/* Right Controls: Theme Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 shadow-xs hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          >
            {theme === 'dark' ? (
              <>
                <Sun className="h-4 w-4 text-amber-400" />
                <span className="hidden sm:inline">Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="h-4 w-4 text-indigo-500" />
                <span className="hidden sm:inline">Dark Mode</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Content View — screens stay mounted (hidden, not unmounted) so an
          in-progress job keeps running and its live progress survives tab switches. */}
      <main className="flex-1 overflow-y-auto p-6 md:p-8">
        <div className={activeTab === 'drop' ? undefined : 'hidden'}>
          <DropScreen onJobCompleted={handleJobCompleted} />
        </div>

        <div className={activeTab === 'result' ? undefined : 'hidden'}>
          {lastCompletedJob ? (
            <ResultScreen job={lastCompletedJob} onReset={() => setActiveTab('drop')} />
          ) : (
            <div className="py-24 text-center text-slate-400 dark:text-slate-500">
              No completed job yet. Drop a folder in the Organize tab to start!
            </div>
          )}
        </div>

        <div className={activeTab === 'settings' ? undefined : 'hidden'}>
          <SettingsScreen />
        </div>
      </main>
    </div>
  );
};
export default App;
