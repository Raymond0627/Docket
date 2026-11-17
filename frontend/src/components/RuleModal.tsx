import React, { useState } from 'react';
import { RuleDefinition } from '../types';
import { X, Plus } from 'lucide-react';

interface RuleModalProps {
  rule: RuleDefinition | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (savedRule: RuleDefinition) => void;
}

export const RuleModal: React.FC<RuleModalProps> = ({ rule, isOpen, onClose, onSave }) => {
  if (!isOpen) return null;

  const [formData, setFormData] = useState<RuleDefinition>(
    rule || {
      id: `rule_${Date.now()}`,
      name: '',
      category: 'Identification',
      target_folder: '',
      keywords: [],
      regex_patterns: [],
      min_confidence: 70,
      enabled: true,
    }
  );

  const [newKeyword, setNewKeyword] = useState('');
  const [newRegex, setNewRegex] = useState('');

  const handleAddKeyword = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newKeyword.trim()) return;
    if (!formData.keywords.includes(newKeyword.trim())) {
      setFormData({ ...formData, keywords: [...formData.keywords, newKeyword.trim()] });
    }
    setNewKeyword('');
  };

  const handleRemoveKeyword = (kw: string) => {
    setFormData({ ...formData, keywords: formData.keywords.filter((k) => k !== kw) });
  };

  const handleAddRegex = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newRegex.trim()) return;
    if (!formData.regex_patterns.includes(newRegex.trim())) {
      setFormData({ ...formData, regex_patterns: [...formData.regex_patterns, newRegex.trim()] });
    }
    setNewRegex('');
  };

  const handleRemoveRegex = (pattern: string) => {
    setFormData({ ...formData, regex_patterns: formData.regex_patterns.filter((p) => p !== pattern) });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    onSave({
      ...formData,
      target_folder: formData.target_folder.trim() || formData.name.trim(),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 px-6 py-4 bg-slate-50 dark:bg-slate-950/60">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            {rule ? `Edit Rule: ${rule.name}` : 'New Document Rule'}
          </h3>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Document Type Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Driver's License"
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 text-sm text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 text-sm text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
              >
                <option value="Identification">Identification</option>
                <option value="Financial">Financial</option>
                <option value="Employment">Employment</option>
                <option value="Billing">Billing</option>
                <option value="Legal">Legal</option>
                <option value="General">General</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Target Folder Name</label>
            <input
              type="text"
              value={formData.target_folder}
              onChange={(e) => setFormData({ ...formData, target_folder: e.target.value })}
              placeholder="e.g. Driver License"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 text-sm text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
            />
          </div>

          {/* Keywords Section */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Matching Keywords (Fuzzy matched against OCR)
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
                placeholder="Add keyword (e.g. Land Transportation Office)..."
                className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-1.5 text-sm text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleAddKeyword()}
                className="inline-flex items-center gap-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-white transition"
              >
                <Plus className="h-3.5 w-3.5" /> Add
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-1">
              {formData.keywords.map((kw, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-lg bg-slate-100 dark:bg-slate-800 px-2.5 py-1 text-xs text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/80"
                >
                  <span>{kw}</span>
                  <button type="button" onClick={() => handleRemoveKeyword(kw)} className="hover:text-rose-500">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Regex Patterns */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Regex Patterns (High-confidence patterns like ID number format)
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newRegex}
                onChange={(e) => setNewRegex(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddRegex())}
                placeholder="e.g. [A-Z]\d{2}-\d{2}-\d{6}"
                className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-1.5 text-sm text-slate-900 dark:text-white font-mono focus:border-brand-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleAddRegex()}
                className="inline-flex items-center gap-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-white transition"
              >
                <Plus className="h-3.5 w-3.5" /> Add
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto p-1">
              {formData.regex_patterns.map((rg, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-lg bg-slate-100 dark:bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/80"
                >
                  <span>{rg}</span>
                  <button type="button" onClick={() => handleRemoveRegex(rg)} className="hover:text-rose-500">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Min Confidence Slider */}
          <div>
            <div className="flex justify-between text-xs text-slate-700 dark:text-slate-300 mb-1">
              <span>Minimum Confidence Threshold</span>
              <span className="font-mono text-brand-600 dark:text-brand-400 font-bold">{formData.min_confidence}%</span>
            </div>
            <input
              type="range"
              min="30"
              max="95"
              step="5"
              value={formData.min_confidence}
              onChange={(e) => setFormData({ ...formData, min_confidence: Number(e.target.value) })}
              className="w-full accent-brand-500"
            />
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-xl bg-brand-600 px-5 py-2 text-sm font-medium text-white hover:bg-brand-500 transition shadow-lg shadow-brand-500/20"
            >
              Save Rule
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
