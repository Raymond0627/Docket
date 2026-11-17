import React, { useEffect, useRef, useState } from 'react';
import { AppSettings, RuleDefinition } from '../types';
import { api } from '../services/api';
import { RuleModal } from '../components/RuleModal';
import { 
  Settings2, 
  FolderCheck, 
  Sliders, 
  Layers, 
  Plus, 
  Edit3, 
  Copy, 
  Move,
  CheckCircle2,
  Sparkles,
  Key,
  Eye,
  EyeOff
} from 'lucide-react';

export const SettingsScreen: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [rules, setRules] = useState<RuleDefinition[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [editingRule, setEditingRule] = useState<RuleDefinition | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [testingGemini, setTestingGemini] = useState(false);
  const [geminiStatus, setGeminiStatus] = useState<{ success: boolean; message: string } | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const isFirstRender = useRef(true);

  useEffect(() => {
    api.getSettings().then(setSettings).catch(console.error);
    api.getRules().then(setRules).catch(console.error);
  }, []);

  // Auto-save settings whenever they change
  useEffect(() => {
    if (!settings) return;
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    const timer = setTimeout(() => {
      api.updateSettings(settings).then(() => showToast('Settings saved automatically')).catch(console.error);
    }, 600);
    return () => clearTimeout(timer);
  }, [settings]);

  const handleTestGemini = async () => {
    if (!settings?.gemini_api_key?.trim()) {
      alert('Please enter a Google Gemini API Key first.');
      return;
    }
    try {
      setTestingGemini(true);
      setGeminiStatus(null);
      const res = await api.testGeminiKey(settings.gemini_api_key, settings.gemini_model || 'gemini-3.5-flash-lite');
      setGeminiStatus({ success: true, message: res.message });
    } catch (err: any) {
      setGeminiStatus({ success: false, message: err.message || 'Connection failed' });
    } finally {
      setTestingGemini(false);
    }
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleToggleRule = async (ruleId: string) => {
    const updated = rules.map((r) => (r.id === ruleId ? { ...r, enabled: !r.enabled } : r));
    setRules(updated);
    try {
      await api.updateRules(updated);
    } catch (err: any) {
      alert('Failed to update rules');
    }
  };

  const handleSaveRule = async (savedRule: RuleDefinition) => {
    let updated: RuleDefinition[];
    const exists = rules.some((r) => r.id === savedRule.id);
    if (exists) {
      updated = rules.map((r) => (r.id === savedRule.id ? savedRule : r));
    } else {
      updated = [...rules, savedRule];
    }
    setRules(updated);
    setIsModalOpen(false);
    try {
      await api.updateRules(updated);
      showToast('Rule saved successfully!');
    } catch (err: any) {
      alert('Failed to save rule');
    }
  };

  const categories = ['All', 'Identification', 'Financial', 'Employment', 'Billing', 'Legal'];

  const filteredRules = selectedCategory === 'All'
    ? rules
    : rules.filter((r) => r.category === selectedCategory);

  if (!settings) {
    return <div className="py-20 text-center text-slate-500">Loading settings...</div>;
  }

  // Live Template Preview
  const templatePreview = settings.folder_template
    .replace('{owner}', 'Raymond Gudito')
    .replace('{doc_type}', 'Driver License') + 'dl_sample.pdf';

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white shadow-xl animate-in slide-in-from-bottom-5">
          <CheckCircle2 className="h-4 w-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Configuration & Rules
            <Settings2 className="h-6 w-6 text-brand-500" />
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Tune document routing behavior, default paths, and the 15+ Philippine document rules.
          </p>
        </div>

      </div>

      {/* General Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Output Directory & File Mode */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
            <FolderCheck className="h-4 w-4 text-brand-500" />
            <span>Output & File Operations</span>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Default Destination Directory</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={settings.output_path}
                onChange={(e) => setSettings({ ...settings, output_path: e.target.value })}
                className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 text-sm text-slate-900 dark:text-white font-mono focus:border-brand-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={async () => {
                  try {
                    const picked = await api.selectFolder();
                    if (picked) setSettings({ ...settings, output_path: picked });
                  } catch (e) {
                    console.error(e);
                  }
                }}
                className="rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 px-3.5 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 transition"
              >
                Browse...
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">File Action Mode</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setSettings({ ...settings, file_mode: 'copy' })}
                className={`flex items-center gap-2 p-3 rounded-xl border text-xs font-medium transition ${
                  settings.file_mode === 'copy'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-white ring-1 ring-brand-500/30'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Copy className="h-4 w-4 text-brand-500" />
                <div className="text-left">
                  <div className="font-semibold">Copy (Safe)</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">Leaves source untouched</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setSettings({ ...settings, file_mode: 'move' })}
                className={`flex items-center gap-2 p-3 rounded-xl border text-xs font-medium transition ${
                  settings.file_mode === 'move'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-white ring-1 ring-brand-500/30'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Move className="h-4 w-4 text-amber-500" />
                <div className="text-left">
                  <div className="font-semibold">Move</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">Cleans source folder</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Confidence & Template */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 space-y-4 shadow-sm">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-semibold text-sm">
            <Sliders className="h-4 w-4 text-brand-500" />
            <span>Classification Sensitivity & Template</span>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1.5">
              <span>Default Confidence Threshold</span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">{settings.confidence_threshold}%</span>
            </div>
            <input
              type="range"
              min="40"
              max="95"
              step="5"
              value={settings.confidence_threshold}
              onChange={(e) => setSettings({ ...settings, confidence_threshold: Number(e.target.value) })}
              className="w-full accent-brand-500"
            />
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Files scoring below this cutoff are routed to <span className="font-mono text-amber-600 dark:text-amber-400">Unsorted/{'{owner}'}/</span>.
            </p>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1.5">
              <span>OCR Render DPI</span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">{settings.ocr_dpi ?? 150} DPI</span>
            </div>
            <input
              type="range"
              min="50"
              max="300"
              step="25"
              value={settings.ocr_dpi ?? 150}
              onChange={(e) => setSettings({ ...settings, ocr_dpi: Number(e.target.value) })}
              className="w-full accent-brand-500"
            />
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Raise for small/unreadable scans (slower); lower for speed. Default 150.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">Folder Sorting Hierarchy (Presets)</label>
            <div className="flex flex-wrap gap-2 mb-2">
              <button
                type="button"
                onClick={() => setSettings({ ...settings, folder_template: '{owner}/{doc_type}/' })}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
                  settings.folder_template === '{owner}/{doc_type}/'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300'
                    : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                1. Sort by User / Owner ({'{owner}/{doc_type}'})
              </button>
              <button
                type="button"
                onClick={() => setSettings({ ...settings, folder_template: '{doc_type}/{owner}/' })}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
                  settings.folder_template === '{doc_type}/{owner}/'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300'
                    : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                2. Sort by Doc Type ({'{doc_type}/{owner}'})
              </button>
              <button
                type="button"
                onClick={() => setSettings({ ...settings, folder_template: '{category}/{owner}/{doc_type}/' })}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
                  settings.folder_template === '{category}/{owner}/{doc_type}/'
                    ? 'border-brand-500 bg-brand-50 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300'
                    : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                3. By Category ({'{category}/{owner}'})
              </button>
            </div>

            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Custom Folder Template</label>
            <input
              type="text"
              value={settings.folder_template}
              onChange={(e) => setSettings({ ...settings, folder_template: e.target.value })}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 text-sm text-slate-900 dark:text-white font-mono focus:border-brand-500 focus:outline-none"
            />
            <div className="mt-2 rounded-lg bg-slate-100 dark:bg-slate-950/80 p-2 text-[11px] font-mono text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-400">Preview: </span>
              <span className="text-brand-600 dark:text-brand-300">{templatePreview}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Google Gemini AI Configuration Card */}
      <div className="rounded-2xl border border-indigo-500/25 dark:border-indigo-500/30 bg-gradient-to-br from-indigo-50/50 via-white to-violet-50/30 dark:from-indigo-950/20 dark:via-slate-900/60 dark:to-violet-950/20 p-6 space-y-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                <span>Google Gemini AI (Chat with Selected Documents)</span>
                <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/20">
                  Multimodal Q&A
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Ask Gemini questions, extract custom details, verify validity, and chat with any document in the Document Viewer.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleTestGemini}
            disabled={testingGemini || !settings.gemini_api_key?.trim()}
            className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 px-3.5 py-2 text-xs font-semibold transition disabled:opacity-50"
          >
            {testingGemini ? (
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            ) : (
              <Key className="h-3.5 w-3.5" />
            )}
            <span>Test Connection</span>
          </button>
        </div>

        {geminiStatus && (
          <div
            className={`rounded-xl p-3 text-xs flex items-center gap-2 border animate-in fade-in duration-200 ${
              geminiStatus.success
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300'
            }`}
          >
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{geminiStatus.message}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Google Gemini API Key
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                placeholder="AIzaSy..."
                value={settings.gemini_api_key || ''}
                onChange={(e) => setSettings({ ...settings, gemini_api_key: e.target.value })}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 pr-10 pl-3.5 py-2 text-xs text-slate-900 dark:text-white font-mono focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Enter your Gemini API key to enable document Q&A and interactive chat in the Document Viewer.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Model
            </label>
            <select
              value={settings.gemini_model || 'gemini-3.5-flash-lite'}
              onChange={(e) => setSettings({ ...settings, gemini_model: e.target.value })}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-900 dark:text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite (Recommended)</option>
              <option value="gemini-3.6-flash">gemini-3.6-flash</option>
              <option value="gemini-3.8-flash">gemini-3.8-flash</option>
            </select>
          </div>
        </div>
      </div>

      {/* Rules Catalog */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-brand-500" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Document Classification Catalog ({rules.length})</h3>
          </div>

          <div className="flex items-center gap-2">
            {/* Category Filter Pills */}
            <div className="flex items-center gap-1 rounded-xl bg-slate-100 dark:bg-slate-900 p-1 border border-slate-200 dark:border-slate-800 text-xs">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`rounded-lg px-2.5 py-1 font-medium transition ${
                    selectedCategory === cat
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <button
              onClick={() => {
                setEditingRule(null);
                setIsModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2 text-xs font-medium text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-700 shadow-xs transition"
            >
              <Plus className="h-3.5 w-3.5 text-brand-500" />
              <span>Add Rule</span>
            </button>
          </div>
        </div>

        {/* Rules List (compact) */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800/80">
          {filteredRules.map((r) => (
            <div
              key={r.id}
              className={`flex items-center gap-3 px-4 py-2.5 transition ${
                r.enabled
                  ? 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                  : 'opacity-50 bg-slate-50/60 dark:bg-slate-950/40'
              }`}
            >
              {/* Toggle */}
              <button
                type="button"
                onClick={() => handleToggleRule(r.id)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  r.enabled ? 'bg-brand-600' : 'bg-slate-300 dark:bg-slate-700'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    r.enabled ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </button>

              {/* Name + meta (single horizontal line) */}
              <span className="font-semibold text-sm text-slate-900 dark:text-white truncate min-w-0 shrink">{r.name}</span>
              <span className="rounded-md bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-[10px] text-brand-700 dark:text-brand-300 font-medium shrink-0">
                {r.category}
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate min-w-0 flex-1">
                📁 {r.target_folder}
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 shrink-0">
                {r.keywords.length} kw • {r.regex_patterns.length} rx
              </span>

              {/* Edit */}
              <button
                onClick={() => {
                  setEditingRule(r);
                  setIsModalOpen(true);
                }}
                className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-medium text-slate-500 dark:text-slate-400 hover:text-brand-600 dark:hover:text-brand-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition shrink-0"
              >
                <Edit3 className="h-3 w-3" />
                <span>Edit</span>
              </button>
            </div>
          ))}
          {filteredRules.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-slate-500 dark:text-slate-400">No rules in this category.</div>
          )}
        </div>
      </div>

      {/* Rule Editor Modal */}
      <RuleModal
        rule={editingRule}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveRule}
      />
    </div>
  );
};
