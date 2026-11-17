import React, { useEffect, useState } from 'react';
import { Job, DirectoryNode, FileClassification, RuleDefinition } from '../types';
import { api } from '../services/api';
import { TreeView } from '../components/TreeView';
import { DocumentViewer } from '../components/DocumentViewer';
import { ECMSModal } from '../components/ECMSModal';
import { 
  FolderCheck, 
  FolderX, 
  Clock, 
  ExternalLink, 
  Download, 
  RotateCcw, 
  CheckCircle2, 
  AlertTriangle,
  FolderTree,
  ListFilter,
  Eye,
  ArrowUpDown,
  CloudUpload,
  Sparkles,
  RefreshCw
} from 'lucide-react';

interface ResultScreenProps {
  job: Job;
  onReset: () => void;
}

export const ResultScreen: React.FC<ResultScreenProps> = ({ job, onReset }) => {
  const [currentJob, setCurrentJob] = useState<Job>(job);
  const [treeData, setTreeData] = useState<DirectoryNode | null>(null);
  const [files, setFiles] = useState<FileClassification[]>([]);
  const [rules, setRules] = useState<RuleDefinition[]>([]);
  const [activeTab, setActiveTab] = useState<'files' | 'tree'>('files');
  const [filterMode, setFilterMode] = useState<'all' | 'unsorted' | 'sorted'>('all');
  const [sortField, setSortField] = useState<'owner' | 'doc_type'>('owner');
  const [hierarchyMode, setHierarchyMode] = useState<'by_owner' | 'by_doc_type' | 'by_category' | 'raw_disk'>('by_owner');
  const [selectedFileForViewer, setSelectedFileForViewer] = useState<FileClassification | null>(null);
  const [isECMSOpen, setIsECMSOpen] = useState(false);
  const [openingFolder, setOpeningFolder] = useState(false);
  const [reorganizingDisk, setReorganizingDisk] = useState(false);

  useEffect(() => {
    setCurrentJob(job);
    refreshData();
    api.getRules().then(setRules).catch(console.error);
  }, [job.id]);

  const refreshData = () => {
    api.getJobTree(currentJob.id).then(setTreeData).catch(console.error);
    api.getJobFiles(currentJob.id).then(setFiles).catch(console.error);
  };

  const handleOpenFolder = async () => {
    try {
      setOpeningFolder(true);
      await api.openFolder(currentJob.output_path);
    } catch (err: any) {
      alert(err.message || 'Could not open folder');
    } finally {
      setOpeningFolder(false);
    }
  };

  const handleExportCsv = () => {
    window.open(`/api/jobs/${currentJob.id}/csv`, '_blank');
  };

  const handleReclassified = (updatedFile: FileClassification) => {
    setFiles((prev) =>
      prev.map((f) => (f.original_path === updatedFile.original_path ? updatedFile : f))
    );
    setCurrentJob((prev) => ({
      ...prev,
      sorted_files: prev.sorted_files + 1,
      unsorted_files: Math.max(0, prev.unsorted_files - 1),
    }));
    api.getJobTree(currentJob.id).then(setTreeData).catch(console.error);
  };

  const handleApplyHierarchyToDisk = async () => {
    let template = '{owner}/{doc_type}/';
    if (hierarchyMode === 'by_doc_type') template = '{doc_type}/{owner}/';
    else if (hierarchyMode === 'by_category') template = '{category}/{doc_type}/{owner}/';

    try {
      setReorganizingDisk(true);
      const res = await api.reorganizeOutput(currentJob.id, template);
      if (res.files) {
        setFiles(res.files);
      }
      setCurrentJob((prev) => ({ ...prev, folder_template: template }));
      await api.getJobTree(currentJob.id).then(setTreeData);
      alert(`Output folders on disk reorganized to: ${template}`);
    } catch (err: any) {
      alert(err.message || 'Failed to reorganize folders on disk');
    } finally {
      setReorganizingDisk(false);
    }
  };

  const total = currentJob.sorted_files + currentJob.unsorted_files;
  const sortRate = total > 0 ? Math.round((currentJob.sorted_files / total) * 100) : 0;
  const unsortedCount = files.filter((f) => f.is_unsorted).length;

  const filteredFiles = files
    .filter((f) => {
      if (filterMode === 'unsorted') return f.is_unsorted;
      if (filterMode === 'sorted') return !f.is_unsorted;
      return true;
    })
    .sort((a, b) => {
      if (sortField === 'owner') {
        const cmp = a.owner.localeCompare(b.owner);
        return cmp !== 0 ? cmp : a.doc_type.localeCompare(b.doc_type);
      } else {
        const cmp = a.doc_type.localeCompare(b.doc_type);
        return cmp !== 0 ? cmp : a.owner.localeCompare(b.owner);
      }
    });

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Top Banner & Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            Sorting Results
            <CheckCircle2 className="h-6 w-6 text-emerald-500" />
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Files classified and organized into your destination folder structure.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* ECMS Upload Button */}
          <button
            onClick={() => setIsECMSOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 text-sm font-semibold shadow-md shadow-indigo-500/20 transition"
          >
            <CloudUpload className="h-4 w-4" />
            <span>Upload to ECMS</span>
          </button>

          <button
            onClick={handleOpenFolder}
            disabled={openingFolder}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2.5 text-sm font-medium text-slate-700 dark:text-white shadow-xs hover:bg-slate-50 dark:hover:bg-slate-700 transition"
          >
            <ExternalLink className="h-4 w-4 text-brand-500" />
            <span>Open in Explorer</span>
          </button>

          <button
            onClick={handleExportCsv}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3.5 py-2.5 text-sm font-medium text-slate-700 dark:text-white shadow-xs hover:bg-slate-50 dark:hover:bg-slate-700 transition"
          >
            <Download className="h-4 w-4 text-emerald-500" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 dark:bg-slate-800 text-white px-3.5 py-2.5 text-sm font-medium hover:bg-slate-800 dark:hover:bg-slate-700 transition shadow-xs"
          >
            <RotateCcw className="h-4 w-4" />
            <span>New Batch</span>
          </button>
        </div>
      </div>

      {/* Hero Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Sorted */}
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Sorted Documents
            </span>
            <FolderCheck className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">{currentJob.sorted_files}</span>
            <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">({sortRate}%)</span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Matched rules & routed to destination</p>
        </div>

        {/* Unsorted / Review Needed */}
        <div
          onClick={() => {
            setActiveTab('files');
            setFilterMode('unsorted');
          }}
          className={`rounded-2xl border p-5 shadow-xs transition cursor-pointer ${
            unsortedCount > 0
              ? 'border-amber-500/30 bg-amber-500/10 ring-1 ring-amber-500/20 hover:bg-amber-500/15'
              : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
              <span>Unsorted / Review Needed</span>
              {unsortedCount > 0 && (
                <span className="rounded-full bg-amber-500 px-1.5 py-0.2 text-[10px] text-white font-bold animate-pulse">
                  {unsortedCount}
                </span>
              )}
            </span>
            <FolderX className="h-5 w-5 text-amber-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">{currentJob.unsorted_files}</span>
            <span className="text-sm font-medium text-amber-600 dark:text-amber-400">({100 - sortRate}%)</span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {unsortedCount > 0 ? 'Click here to view, edit metadata & re-sort' : 'All files reviewed & sorted!'}
          </p>
        </div>

        {/* Duration */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Processing Duration
            </span>
            <Clock className="h-5 w-5 text-slate-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white font-mono">
              {currentJob.duration_seconds.toFixed(1)}s
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 truncate">Output: {currentJob.output_path}</p>
        </div>
      </div>

      {/* Explorer & Review Section */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 p-5 space-y-4 shadow-sm">
        
        {/* Navigation & Hierarchy Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800/80 pb-4">
          
          {/* Main View Mode Tabs */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('files')}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'files'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 ring-1 ring-brand-500/30'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <ListFilter className="h-4 w-4" />
              <span>Document Review List ({files.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('tree')}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === 'tree'
                  ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 ring-1 ring-brand-500/30'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <FolderTree className="h-4 w-4" />
              <span>Folder Output Tree</span>
            </button>
          </div>

          {/* Dynamic Hierarchy Selector (On Tree View) */}
          {activeTab === 'tree' ? (
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-slate-500 font-medium">Tree Hierarchy:</span>
              <div className="flex items-center rounded-xl bg-slate-100 dark:bg-slate-800 p-1 border border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setHierarchyMode('by_owner')}
                  className={`rounded-lg px-2.5 py-1 font-medium transition ${
                    hierarchyMode === 'by_owner'
                      ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  By Customer ({'{owner}/{doc}'})
                </button>
                <button
                  onClick={() => setHierarchyMode('by_doc_type')}
                  className={`rounded-lg px-2.5 py-1 font-medium transition ${
                    hierarchyMode === 'by_doc_type'
                      ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  By Doc Type ({'{doc}/{owner}'})
                </button>
                <button
                  onClick={() => setHierarchyMode('by_category')}
                  className={`rounded-lg px-2.5 py-1 font-medium transition ${
                    hierarchyMode === 'by_category'
                      ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400'
                  }`}
                >
                  By Category
                </button>
              </div>

              <button
                onClick={handleApplyHierarchyToDisk}
                disabled={reorganizingDisk}
                className="inline-flex items-center gap-1.5 rounded-xl border border-brand-500/30 bg-brand-500/10 hover:bg-brand-500/20 text-brand-600 dark:text-brand-400 px-3 py-1.5 font-medium transition"
                title="Physically re-routes files on disk to match this hierarchy"
              >
                {reorganizingDisk ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                <span>Apply to Disk</span>
              </button>
            </div>
          ) : (
            /* Filtering & Sorting Controls (When on files view) */
            <div className="flex flex-wrap items-center gap-3 text-xs">
              {/* Filter Pills */}
              <div className="flex items-center rounded-xl bg-slate-100 dark:bg-slate-800 p-1 border border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setFilterMode('all')}
                  className={`rounded-lg px-2.5 py-1 font-medium transition ${
                    filterMode === 'all'
                      ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                      : 'text-slate-500 dark:text-slate-400'
                  }`}
                >
                  All ({files.length})
                </button>
                <button
                  onClick={() => setFilterMode('unsorted')}
                  className={`flex items-center gap-1 rounded-lg px-2.5 py-1 font-medium transition ${
                    filterMode === 'unsorted'
                      ? 'bg-amber-500 text-white shadow-xs'
                      : 'text-amber-600 dark:text-amber-400'
                  }`}
                >
                  <AlertTriangle className="h-3 w-3" />
                  <span>Unsorted ({unsortedCount})</span>
                </button>
                <button
                  onClick={() => setFilterMode('sorted')}
                  className={`rounded-lg px-2.5 py-1 font-medium transition ${
                    filterMode === 'sorted'
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'text-slate-500 dark:text-slate-400'
                  }`}
                >
                  Sorted ({files.length - unsortedCount})
                </button>
              </div>

              {/* Sorting Mode */}
              <button
                onClick={() => setSortField((s) => (s === 'owner' ? 'doc_type' : 'owner'))}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition"
              >
                <ArrowUpDown className="h-3.5 w-3.5 text-brand-500" />
                <span>Sort: {sortField === 'owner' ? 'By Customer/User' : 'By Document Type'}</span>
              </button>
            </div>
          )}
        </div>

        {/* View Mode Content */}
        {activeTab === 'tree' ? (
          <TreeView
            rootNode={treeData}
            files={files}
            rules={rules}
            hierarchyMode={hierarchyMode}
            onSelectFile={(f) => setSelectedFileForViewer(f)}
          />
        ) : (
          <div className="overflow-x-auto max-h-[480px] overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 dark:bg-slate-950 text-slate-600 dark:text-slate-400 uppercase tracking-wider sticky top-0 z-10 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-4">File Name</th>
                  <th className="py-3 px-4">Document Type</th>
                  <th className="py-3 px-4">Customer / Owner</th>
                  <th className="py-3 px-4">Match %</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/60 bg-white dark:bg-slate-900/60 text-slate-700 dark:text-slate-300">
                {filteredFiles.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No files match the selected filter.
                    </td>
                  </tr>
                ) : (
                  filteredFiles.map((f, i) => (
                    <tr
                      key={i}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer"
                      onClick={() => setSelectedFileForViewer(f)}
                    >
                      <td className="py-3 px-4 font-medium text-slate-900 dark:text-white flex items-center gap-2">
                        <span className="truncate max-w-[200px]" title={f.file_name}>{f.file_name}</span>
                      </td>

                      <td className="py-3 px-4">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          {f.doc_type}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <span className="rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs text-slate-800 dark:text-slate-200">
                          {f.owner}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono font-medium">
                        {Math.round(f.confidence)}%
                      </td>

                      <td className="py-3 px-4">
                        {f.is_unsorted ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/20">
                            <AlertTriangle className="h-3 w-3" /> Unsorted
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/20">
                            <CheckCircle2 className="h-3 w-3" /> Sorted
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          {f.is_unsorted ? (
                            <button
                              onClick={() => setSelectedFileForViewer(f)}
                              className="inline-flex items-center gap-1 rounded-lg bg-amber-500 hover:bg-amber-600 text-white px-3 py-1 text-xs font-semibold shadow-xs transition"
                            >
                              <span>Edit Metadata & Re-sort</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => setSelectedFileForViewer(f)}
                              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 px-2.5 py-1 text-xs font-medium transition"
                            >
                              <Eye className="h-3.5 w-3.5" />
                              <span>View</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Built-in Document Viewer & Metadata Editor */}
      <DocumentViewer
        file={selectedFileForViewer}
        rules={rules}
        jobId={currentJob.id}
        isOpen={!!selectedFileForViewer}
        onClose={() => setSelectedFileForViewer(null)}
        onReclassified={handleReclassified}
      />

      {/* ECMS Readiness Modal */}
      <ECMSModal
        job={currentJob}
        files={files}
        isOpen={isECMSOpen}
        onClose={() => setIsECMSOpen(false)}
      />
    </div>
  );
};
