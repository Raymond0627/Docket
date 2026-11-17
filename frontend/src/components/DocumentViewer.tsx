import React, { useState, useRef } from 'react';
import { FileClassification, RuleDefinition } from '../types';
import { api } from '../services/api';
import { ChatMarkdown } from './ChatMarkdown';
import { 
  X, 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Check, 
  AlertTriangle, 
  FileText, 
  User, 
  Folder, 
  ArrowRight, 
  ExternalLink, 
  ShieldCheck, 
  Hash, 
  Layers, 
  Sparkles, 
  Send, 
  Bot
} from 'lucide-react';

interface DocumentViewerProps {
  file: FileClassification | null;
  rules: RuleDefinition[];
  jobId: string;
  isOpen: boolean;
  onClose: () => void;
  onReclassified: (updatedFile: FileClassification) => void;
}

interface ChatMessage {
  sender: 'user' | 'gemini';
  text: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  file,
  rules,
  jobId,
  isOpen,
  onClose,
  onReclassified,
}) => {
  if (!isOpen || !file) return null;

  const [zoom, setZoom] = useState(1);
  const [activePane, setActivePane] = useState<'gemini' | 'metadata'>('gemini');

  // Metadata form state
  const [selectedType, setSelectedType] = useState(
    rules.some((r) => r.name === file.doc_type) ? file.doc_type : (rules[0]?.name || '')
  );
  const [isCustomType, setIsCustomType] = useState(false);
  const [customTypeInput, setCustomTypeInput] = useState('');
  const [ownerInput, setOwnerInput] = useState(file.owner === 'General' ? '' : file.owner);
  const [categoryInput, setCategoryInput] = useState('Identification');
  const [refNumberInput, setRefNumberInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Gemini AI Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isSendingChat, setIsSendingChat] = useState(false);
  const chatInputRef = useRef<HTMLInputElement>(null);

  const previewPath = file.destination_path || file.original_path;
  const ext = file.file_name.split('.').pop()?.toLowerCase() || '';
  const isImage = ['png', 'jpg', 'jpeg', 'webp', 'bmp'].includes(ext);
  const isPdf = ext === 'pdf';
  const previewUrl = api.getFilePreviewUrl(previewPath);

  const finalDocType = isCustomType && customTypeInput.trim() ? customTypeInput.trim() : selectedType;
  const activeRule = rules.find((r) => r.name === finalDocType);
  const targetFolder = activeRule?.target_folder || finalDocType;
  const effectiveOwner = ownerInput.trim() || 'General';

  // Chat with Document using Gemini Vision
  const handleSendChat = async (promptToSend?: string) => {
    const text = promptToSend || chatInput.trim();
    if (!text || isSendingChat) return;

    const newMessages: ChatMessage[] = [...chatMessages, { sender: 'user', text }];
    setChatMessages(newMessages);
    setChatInput('');
    setIsSendingChat(true);
    chatInputRef.current?.focus();

    try {
      const res = await api.chatWithGemini(previewPath, text, chatMessages);
      setChatMessages([...newMessages, { sender: 'gemini', text: res.answer }]);
    } catch (err: any) {
      setChatMessages([
        ...newMessages,
        { sender: 'gemini', text: `Lumeed AI Error: ${err.message || 'Failed to connect. Please make sure your AI API key is configured in Settings.'}` },
      ]);
    } finally {
      setIsSendingChat(false);
      chatInputRef.current?.focus();
    }
  };

  const handleApproveReclassify = async () => {
    try {
      setIsSubmitting(true);
      const res = await api.reclassifyFile(jobId, {
        original_path: file.original_path,
        new_doc_type: finalDocType,
        new_owner: effectiveOwner,
        target_folder: targetFolder,
      });
      if (res.file) {
        onReclassified(res.file);
      }
      onClose();
    } catch (err: any) {
      alert(err.message || 'Failed to reclassify file');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      const res = await api.analyzeFile(jobId, file.original_path);
      if (res.file) onReclassified(res.file);
      onClose();
    } catch (err: any) {
      alert(err.message || 'AI analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 sm:p-6 animate-in fade-in duration-200">
      <div className="flex flex-col h-[92vh] w-full max-w-6xl rounded-2xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden">
        
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 px-6 py-3 bg-slate-50 dark:bg-slate-950/60">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400 ring-1 ring-brand-500/20">
              <FileText className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold text-slate-900 dark:text-white truncate text-sm">
                {file.file_name}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                {previewPath}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 text-xs font-semibold shadow-xs transition disabled:opacity-50"
            >
              {isAnalyzing ? (
                <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Sparkles className="h-3.5 w-3.5" />
              )}
              <span>Analyze & Auto-sort</span>
            </button>
            <button
              onClick={() => window.open(previewUrl, '_blank')}
              className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition"
              title="Open raw file in new tab"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span>Raw</span>
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content Split: Left (Document Preview) + Right (Ask Gemini / Metadata) */}
        <div className="flex flex-1 flex-col md:flex-row overflow-hidden">
          
          {/* Left / Center Document Preview Pane */}
          <div className="relative flex-1 flex flex-col items-center justify-center bg-slate-100 dark:bg-slate-950/80 p-4 overflow-hidden border-b md:border-b-0 md:border-r border-slate-200 dark:border-slate-800">
            {isImage ? (
              <div className="relative w-full h-full flex items-center justify-center overflow-auto p-2">
                <img
                  src={previewUrl}
                  alt={file.file_name}
                  style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
                  className="max-h-full max-w-full rounded-lg object-contain shadow-md transition-transform duration-150"
                />
                
                {/* Floating Image Zoom Controls */}
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-1.5 rounded-xl bg-slate-900/90 dark:bg-slate-800/90 backdrop-blur-md px-3 py-1.5 text-white shadow-lg border border-slate-700">
                  <button
                    onClick={() => setZoom((z) => Math.max(0.4, z - 0.2))}
                    className="p-1 hover:text-brand-400 transition"
                    title="Zoom Out"
                  >
                    <ZoomOut className="h-4 w-4" />
                  </button>
                  <span className="text-xs font-mono px-1">{Math.round(zoom * 100)}%</span>
                  <button
                    onClick={() => setZoom((z) => Math.min(3, z + 0.2))}
                    className="p-1 hover:text-brand-400 transition"
                    title="Zoom In"
                  >
                    <ZoomIn className="h-4 w-4" />
                  </button>
                  <div className="h-3 w-px bg-slate-700 mx-1" />
                  <button
                    onClick={() => setZoom(1)}
                    className="p-1 hover:text-brand-400 transition"
                    title="Reset Zoom"
                  >
                    <Maximize2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ) : isPdf ? (
              <iframe
                src={previewUrl}
                className="w-full h-full rounded-lg border-0 bg-white"
                title={file.file_name}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-8 text-slate-500 dark:text-slate-400 space-y-3">
                <FileText className="h-16 w-16 text-slate-400" />
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-200">
                    {ext.toUpperCase()} Document
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Direct text extract processed by engine.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel: Gemini Chat & Metadata Tabs */}
          <div className="w-full md:w-96 flex flex-col justify-between bg-white dark:bg-slate-900 overflow-hidden">
            
            {/* Tab Bar Toggle */}
            <div className="flex border-b border-slate-200 dark:border-slate-800 p-2 gap-1.5 bg-slate-50/80 dark:bg-slate-950/40">
              <button
                onClick={() => setActivePane('gemini')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold transition ${
                  activePane === 'gemini'
                    ? 'bg-gradient-to-r from-indigo-500/15 to-violet-500/15 text-indigo-600 dark:text-indigo-400 shadow-xs ring-1 ring-indigo-500/30 font-bold'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
                <span>Ask Lumeed AI</span>
              </button>

              <button
                onClick={() => setActivePane('metadata')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold transition ${
                  activePane === 'metadata'
                    ? 'bg-white dark:bg-slate-800 text-brand-600 dark:text-brand-400 shadow-xs ring-1 ring-slate-200 dark:ring-slate-700'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Metadata & Routing</span>
              </button>
            </div>

            {/* TAB 1: ASK GOOGLE GEMINI (CHAT & ASK DETAILS) */}
            {activePane === 'gemini' ? (
              <div className="flex-1 flex flex-col justify-between overflow-hidden p-4">
                
                {/* Chat Message Stream */}
                <div className="flex-1 overflow-y-auto space-y-3 p-1">
                  {chatMessages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center text-center py-6 text-slate-500 dark:text-slate-400 space-y-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500 ring-1 ring-indigo-500/20">
                        <Bot className="h-6 w-6" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          Ask Lumeed AI anything about this document!
                        </p>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Lumeed AI reads the full document image or PDF directly.
                        </p>
                      </div>

                      {/* Quick Question Prompts */}
                      <div className="flex flex-col gap-1.5 pt-2 w-full">
                        {[
                          'What is this document about?',
                          'Is this ID or document valid / expired?',
                          'What is the salary and deductions breakdown?',
                          'Extract all names, dates, and ID numbers',
                          'What is the account or reference number?'
                        ].map((chip, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSendChat(chip)}
                            className="text-left text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 hover:border-indigo-300 dark:hover:border-indigo-700 px-3 py-2 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition flex items-center justify-between"
                          >
                            <span>{chip}</span>
                            <span className="text-[10px] text-indigo-500 font-mono">Ask &rarr;</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex items-end gap-2 ${
                          msg.sender === 'user' ? 'flex-row-reverse' : ''
                        }`}
                      >
                        {/* Chat head */}
                        <div
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                            msg.sender === 'user'
                              ? 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                              : 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30'
                          }`}
                        >
                          {msg.sender === 'user' ? (
                            <User className="h-3.5 w-3.5" />
                          ) : (
                            <Sparkles className="h-3.5 w-3.5" />
                          )}
                        </div>
                        <div
                          className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                            msg.sender === 'user'
                              ? 'bg-brand-600 text-white rounded-br-none shadow-xs'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-none border border-slate-200 dark:border-slate-700'
                          }`}
                        >
                          {msg.sender === 'user' ? (
                            msg.text
                          ) : (
                            <ChatMarkdown content={msg.text} />
                          )}
                        </div>
                      </div>
                    ))
                  )}

                  {isSendingChat && (
                    <div className="flex items-end gap-2">
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/30">
                        <Sparkles className="h-3.5 w-3.5" />
                      </div>
                      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-none border border-slate-200 bg-slate-100 px-3.5 py-2.5 dark:border-slate-700 dark:bg-slate-800">
                        <span className="flex items-end gap-0.5">
                          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:0ms]" />
                          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:150ms]" />
                          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-indigo-400 [animation-delay:300ms]" />
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">typing...</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Chat Input Bar */}
                <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendChat();
                    }}
                    className="flex gap-2"
                  >
                    <input
                      type="text"
                      placeholder="Ask Lumeed AI about details in this document..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      ref={chatInputRef}
                      className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 text-xs text-slate-900 dark:text-white focus:border-indigo-500 focus:outline-none"
                    />
                    <button
                      type="submit"
                      disabled={isSendingChat || !chatInput.trim()}
                      className="rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white p-2 text-xs font-semibold shadow-xs disabled:opacity-50 transition"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </form>
                </div>

              </div>
            ) : (
              /* TAB 2: METADATA & RE-ROUTE */
              <div className="flex-1 flex flex-col justify-between overflow-hidden">
                <div className="flex-1 overflow-y-auto p-5 space-y-4">
                  
                  {/* Status Badge */}
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3.5 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">
                        Classification Status
                      </span>
                      {file.status === 'queued' || file.status === 'processing' ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-600 dark:text-indigo-400 ring-1 ring-indigo-500/20">
                          <Sparkles className="h-3 w-3" /> Background OCR/AI
                        </span>
                      ) : file.is_unsorted ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/20">
                          <AlertTriangle className="h-3 w-3" /> Unsorted
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20">
                          <Check className="h-3 w-3" /> Classified
                        </span>
                      )}
                    </div>

                    <div className="flex items-baseline justify-between">
                      <span className="text-sm font-bold text-slate-900 dark:text-white">
                        {file.doc_type}
                      </span>
                      <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                        {Math.round(file.confidence)}% confidence
                      </span>
                    </div>
                  </div>

                  {/* Metadata Fields */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                        Document Type
                      </label>
                      <button
                        type="button"
                        onClick={() => setIsCustomType(!isCustomType)}
                        className="text-[11px] text-brand-600 dark:text-brand-400 hover:underline"
                      >
                        {isCustomType ? 'Pick from list' : '+ Custom'}
                      </button>
                    </div>

                    {!isCustomType ? (
                      <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
                      >
                        {rules.map((r) => (
                          <option key={r.id} value={r.name}>
                            {r.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        placeholder="e.g. Sales Invoice"
                        value={customTypeInput}
                        onChange={(e) => setCustomTypeInput(e.target.value)}
                        className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
                      />
                    )}

                    {/* Customer / Person Name */}
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 flex items-center justify-between">
                        <span>Customer / Person Name</span>
                        <span className="text-[10px] text-slate-400">Required</span>
                      </label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                        <input
                          type="text"
                          placeholder="e.g. Raymond Gudito"
                          value={ownerInput}
                          onChange={(e) => setOwnerInput(e.target.value)}
                          className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
                        />
                      </div>
                    </div>

                    {/* Category & Reference Number */}
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                          Category
                        </label>
                        <div className="relative">
                          <Layers className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                          <select
                            value={categoryInput}
                            onChange={(e) => setCategoryInput(e.target.value)}
                            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 pl-8 pr-2 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
                          >
                            <option value="Identification">ID</option>
                            <option value="Financial">Financial</option>
                            <option value="Employment">Employment</option>
                            <option value="Billing">Billing</option>
                            <option value="Legal">Legal</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                          Ref / ID No.
                        </label>
                        <div className="relative">
                          <Hash className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                          <input
                            type="text"
                            placeholder="e.g. N01-20-..."
                            value={refNumberInput}
                            onChange={(e) => setRefNumberInput(e.target.value)}
                            className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 pl-8 pr-2.5 py-2 text-xs text-slate-900 dark:text-white focus:border-brand-500 focus:outline-none"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Destination Folder Preview */}
                    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 p-3 text-xs space-y-1">
                      <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400 font-medium text-[11px]">
                        <Folder className="h-3.5 w-3.5 text-brand-500" />
                        <span>Destination Folder Preview:</span>
                      </div>
                      <p className="font-mono text-[11px] text-brand-600 dark:text-brand-300 break-all">
                        .../{effectiveOwner}/{targetFolder}/{file.file_name}
                      </p>
                    </div>
                  </div>

                </div>

                {(file.status === 'queued' || file.status === 'processing') && (
                  <div className="px-4 pt-3 text-[11px] text-indigo-600 dark:text-indigo-400">
                    Saving now stops this file's background OCR/AI processing and routes it immediately.
                  </div>
                )}

                {/* Bottom Actions for Metadata re-sort */}
                <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex gap-2 bg-slate-50/50 dark:bg-slate-950/40">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleApproveReclassify}
                    disabled={isSubmitting}
                    className="flex-2 inline-flex items-center justify-center gap-1.5 rounded-xl bg-brand-600 py-2.5 text-xs font-semibold text-white hover:bg-brand-500 shadow-md shadow-brand-500/20 transition disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    ) : (
                      <>
                        <span>Save & Re-sort Now</span>
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  );
};
