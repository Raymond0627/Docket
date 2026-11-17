import React, { useState, useMemo } from 'react';
import { DirectoryNode, FileClassification, RuleDefinition } from '../types';
import { Folder, FolderOpen, ChevronRight, ChevronDown, FileText, FileSpreadsheet, Image as ImageIcon, File } from 'lucide-react';

interface TreeViewProps {
  rootNode?: DirectoryNode | null;
  files?: FileClassification[];
  rules?: RuleDefinition[];
  hierarchyMode?: 'by_owner' | 'by_doc_type' | 'by_category' | 'raw_disk';
  onSelectFile?: (file: FileClassification) => void;
}

const TreeNode: React.FC<{
  node: DirectoryNode;
  level?: number;
  filesMap?: Map<string, FileClassification>;
  onSelectFile?: (file: FileClassification) => void;
}> = ({ node, level = 0, filesMap, onSelectFile }) => {
  const [isOpen, setIsOpen] = useState(level < 2);

  const isDirectory = node.type === 'directory';

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (ext === 'xlsx' || ext === 'xls') return <FileSpreadsheet className="h-4 w-4 text-emerald-500" />;
    if (['png', 'jpg', 'jpeg', 'webp', 'bmp'].includes(ext || '')) return <ImageIcon className="h-4 w-4 text-violet-500" />;
    if (ext === 'pdf' || ext === 'docx' || ext === 'doc') return <FileText className="h-4 w-4 text-blue-500" />;
    return <File className="h-4 w-4 text-slate-400" />;
  };

  const handleRowClick = () => {
    if (isDirectory) {
      setIsOpen(!isOpen);
    } else if (onSelectFile && filesMap) {
      const match = filesMap.get(node.path) || filesMap.get(node.name);
      if (match) onSelectFile(match);
    }
  };

  return (
    <div className="select-none text-sm">
      <div
        onClick={handleRowClick}
        style={{ paddingLeft: `${level * 18}px` }}
        className={`flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer transition ${
          isDirectory
            ? 'hover:bg-slate-100 dark:hover:bg-slate-800/60 font-medium text-slate-800 dark:text-slate-200'
            : 'hover:bg-slate-100 dark:hover:bg-slate-800/40 text-slate-700 dark:text-slate-300'
        }`}
      >
        {isDirectory ? (
          <>
            <span className="text-slate-400 dark:text-slate-500">
              {isOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            </span>
            {isOpen ? <FolderOpen className="h-4 w-4 text-brand-500" /> : <Folder className="h-4 w-4 text-brand-500" />}
            <span className="truncate">{node.name}</span>
            {node.children && (
              <span className="ml-auto rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-[11px] font-mono text-slate-500 dark:text-slate-400">
                {node.children.length}
              </span>
            )}
          </>
        ) : (
          <>
            <span className="w-3.5" />
            {getFileIcon(node.name)}
            <span className="truncate flex-1 hover:underline">{node.name}</span>
          </>
        )}
      </div>

      {isDirectory && isOpen && node.children && (
        <div>
          {node.children.map((child, idx) => (
            <TreeNode
              key={idx}
              node={child}
              level={level + 1}
              filesMap={filesMap}
              onSelectFile={onSelectFile}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const TreeView: React.FC<TreeViewProps> = ({
  rootNode,
  files = [],
  rules = [],
  hierarchyMode = 'by_owner',
  onSelectFile,
}) => {
  const filesMap = useMemo(() => {
    const map = new Map<string, FileClassification>();
    files.forEach((f) => {
      if (f.destination_path) map.set(f.destination_path, f);
      map.set(f.file_name, f);
      map.set(f.original_path, f);
    });
    return map;
  }, [files]);

  // Build dynamic tree based on hierarchyMode
  const dynamicTree = useMemo((): DirectoryNode => {
    if (hierarchyMode === 'raw_disk' && rootNode) {
      return rootNode;
    }

    const ruleCatMap = new Map<string, string>();
    rules.forEach((r) => ruleCatMap.set(r.name, r.category));

    const root: DirectoryNode = {
      name: 'Docket Output',
      path: 'root',
      type: 'directory',
      children: [],
    };

    if (hierarchyMode === 'by_owner') {
      // Group by Owner -> DocType -> Files
      const ownerGroups = new Map<string, Map<string, DirectoryNode[]>>();
      const unsortedNodes: DirectoryNode[] = [];

      files.forEach((f) => {
        const fileNode: DirectoryNode = {
          name: f.file_name,
          path: f.destination_path || f.original_path,
          type: 'file',
        };

        if (f.is_unsorted) {
          unsortedNodes.push(fileNode);
          return;
        }

        const owner = f.owner || 'General';
        const docType = f.doc_type || 'Unknown';

        if (!ownerGroups.has(owner)) ownerGroups.set(owner, new Map());
        const dtMap = ownerGroups.get(owner)!;
        if (!dtMap.has(docType)) dtMap.set(docType, []);
        dtMap.get(docType)!.push(fileNode);
      });

      // Assemble nodes
      ownerGroups.forEach((dtMap, ownerName) => {
        const ownerNode: DirectoryNode = {
          name: ownerName,
          path: `owner_${ownerName}`,
          type: 'directory',
          children: [],
        };
        dtMap.forEach((fileList, docTypeName) => {
          ownerNode.children!.push({
            name: docTypeName,
            path: `${ownerName}/${docTypeName}`,
            type: 'directory',
            children: fileList,
          });
        });
        root.children!.push(ownerNode);
      });

      if (unsortedNodes.length > 0) {
        root.children!.push({
          name: '⚠️ Unsorted (Needs Review)',
          path: 'Unsorted',
          type: 'directory',
          children: unsortedNodes,
        });
      }

    } else if (hierarchyMode === 'by_doc_type') {
      // Group by DocType -> Owner -> Files
      const docTypeGroups = new Map<string, Map<string, DirectoryNode[]>>();
      const unsortedNodes: DirectoryNode[] = [];

      files.forEach((f) => {
        const fileNode: DirectoryNode = {
          name: f.file_name,
          path: f.destination_path || f.original_path,
          type: 'file',
        };

        if (f.is_unsorted) {
          unsortedNodes.push(fileNode);
          return;
        }

        const docType = f.doc_type || 'Unknown';
        const owner = f.owner || 'General';

        if (!docTypeGroups.has(docType)) docTypeGroups.set(docType, new Map());
        const oMap = docTypeGroups.get(docType)!;
        if (!oMap.has(owner)) oMap.set(owner, []);
        oMap.get(owner)!.push(fileNode);
      });

      docTypeGroups.forEach((oMap, dtName) => {
        const dtNode: DirectoryNode = {
          name: dtName,
          path: `dt_${dtName}`,
          type: 'directory',
          children: [],
        };
        oMap.forEach((fileList, ownerName) => {
          dtNode.children!.push({
            name: ownerName,
            path: `${dtName}/${ownerName}`,
            type: 'directory',
            children: fileList,
          });
        });
        root.children!.push(dtNode);
      });

      if (unsortedNodes.length > 0) {
        root.children!.push({
          name: '⚠️ Unsorted (Needs Review)',
          path: 'Unsorted',
          type: 'directory',
          children: unsortedNodes,
        });
      }

    } else if (hierarchyMode === 'by_category') {
      // Group by Category -> DocType -> Owner -> Files
      const catGroups = new Map<string, Map<string, Map<string, DirectoryNode[]>>>();
      const unsortedNodes: DirectoryNode[] = [];

      files.forEach((f) => {
        const fileNode: DirectoryNode = {
          name: f.file_name,
          path: f.destination_path || f.original_path,
          type: 'file',
        };

        if (f.is_unsorted) {
          unsortedNodes.push(fileNode);
          return;
        }

        const category = ruleCatMap.get(f.doc_type) || 'General';
        const docType = f.doc_type || 'Unknown';
        const owner = f.owner || 'General';

        if (!catGroups.has(category)) catGroups.set(category, new Map());
        const dtMap = catGroups.get(category)!;
        if (!dtMap.has(docType)) dtMap.set(docType, new Map());
        const oMap = dtMap.get(docType)!;
        if (!oMap.has(owner)) oMap.set(owner, []);
        oMap.get(owner)!.push(fileNode);
      });

      catGroups.forEach((dtMap, catName) => {
        const catNode: DirectoryNode = {
          name: catName,
          path: `cat_${catName}`,
          type: 'directory',
          children: [],
        };
        dtMap.forEach((oMap, dtName) => {
          const dtNode: DirectoryNode = {
            name: dtName,
            path: `${catName}/${dtName}`,
            type: 'directory',
            children: [],
          };
          oMap.forEach((fileList, ownerName) => {
            dtNode.children!.push({
              name: ownerName,
              path: `${catName}/${dtName}/${ownerName}`,
              type: 'directory',
              children: fileList,
            });
          });
          catNode.children!.push(dtNode);
        });
        root.children!.push(catNode);
      });

      if (unsortedNodes.length > 0) {
        root.children!.push({
          name: '⚠️ Unsorted (Needs Review)',
          path: 'Unsorted',
          type: 'directory',
          children: unsortedNodes,
        });
      }
    }

    return root;
  }, [files, rules, hierarchyMode, rootNode]);

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 max-h-[480px] overflow-y-auto shadow-sm">
      <TreeNode
        node={dynamicTree}
        level={0}
        filesMap={filesMap}
        onSelectFile={onSelectFile}
      />
    </div>
  );
};
