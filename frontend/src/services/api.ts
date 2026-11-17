import { AppSettings, Job, JobCreatePayload, RuleDefinition, FileClassification, DirectoryNode, LiveJobEvent } from '../types';

const API_BASE = '/api';

export const api = {
  async getSettings(): Promise<AppSettings> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async updateSettings(settings: AppSettings): Promise<AppSettings> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  async getRules(): Promise<RuleDefinition[]> {
    const res = await fetch(`${API_BASE}/rules`);
    if (!res.ok) throw new Error('Failed to fetch rules');
    return res.json();
  },

  async updateRules(rules: RuleDefinition[]): Promise<RuleDefinition[]> {
    const res = await fetch(`${API_BASE}/rules`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(rules),
    });
    if (!res.ok) throw new Error('Failed to update rules');
    return res.json();
  },

  async createJob(payload: JobCreatePayload): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start job' }));
      throw new Error(err.detail || 'Failed to start job');
    }
    return res.json();
  },

  async uploadFiles(items: { file: File; relativePath: string }[]): Promise<Job> {
    const formData = new FormData();
    items.forEach((item) => {
      formData.append('files', item.file);
      formData.append('relative_paths', item.relativePath);
    });
    const res = await fetch(`${API_BASE}/jobs/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to upload files' }));
      throw new Error(err.detail || 'Failed to upload files');
    }
    return res.json();
  },

  async getJob(id: string): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}`);
    if (!res.ok) throw new Error('Failed to fetch job');
    return res.json();
  },

  async getJobFiles(id: string): Promise<FileClassification[]> {
    const res = await fetch(`${API_BASE}/jobs/${id}/files`);
    if (!res.ok) throw new Error('Failed to fetch job files');
    return res.json();
  },

  async getJobTree(id: string): Promise<DirectoryNode> {
    const res = await fetch(`${API_BASE}/jobs/${id}/tree`);
    if (!res.ok) throw new Error('Failed to fetch job tree');
    return res.json();
  },

  async openFolder(folderPath: string): Promise<{ success: boolean; path: string }> {
    const res = await fetch(`${API_BASE}/system/open-folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_path: folderPath }),
    });
    if (!res.ok) throw new Error('Failed to open folder in explorer');
    return res.json();
  },

  async selectFolder(): Promise<string> {
    const res = await fetch(`${API_BASE}/system/select-folder`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to select folder');
    const data = await res.json();
    return data.selected_path || '';
  },

  getFilePreviewUrl(filePath: string): string {
    return `${API_BASE}/files/preview?path=${encodeURIComponent(filePath)}`;
  },

  async reclassifyFile(
    jobId: string,
    payload: { original_path: string; new_doc_type: string; new_owner: string; target_folder?: string }
  ): Promise<{ success: boolean; file: FileClassification }> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/reclassify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to reclassify file' }));
      throw new Error(err.detail || 'Failed to reclassify file');
    }
    return res.json();
  },

  async analyzeFile(jobId: string, originalPath: string): Promise<{ success: boolean; file: FileClassification }> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ original_path: originalPath }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'AI analysis failed' }));
      throw new Error(err.detail || 'AI analysis failed');
    }
    return res.json();
  },

  async reorganizeOutput(jobId: string, folderTemplate: string): Promise<{ success: boolean; files: FileClassification[] }> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/reorganize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_template: folderTemplate }),
    });
    if (!res.ok) throw new Error('Failed to reorganize folder output');
    return res.json();
  },

  async testGeminiKey(apiKey: string, modelName?: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/ai/test-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, model_name: modelName }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to connect to Google Gemini' }));
      throw new Error(err.detail || 'Failed to connect to Google Gemini');
    }
    return res.json();
  },

  async testNewProviderKey(apiKey: string, modelName?: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/ai/test-key`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, model_name: modelName }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to connect to New Provider AI' }));
      throw new Error(err.detail || 'Failed to connect to New Provider AI');
    }
    return res.json();
  },

  async analyzeDocumentWithGemini(filePath: string): Promise<{
    doc_type: string;
    owner: string;
    category: string;
    reference_number: string;
    summary: string;
    confidence: number;
  }> {
    const res = await fetch(`${API_BASE}/ai/analyze-document`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Gemini analysis failed' }));
      throw new Error(err.detail || 'Gemini analysis failed');
    }
    return res.json();
  },

  async chatWithGemini(filePath: string, prompt: string, history?: any[]): Promise<{ answer: string }> {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, prompt, chat_history: history }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Gemini chat failed' }));
      throw new Error(err.detail || 'Gemini chat failed');
    }
    return res.json();
  },

  subscribeJobStream(jobId: string, onEvent: (event: LiveJobEvent) => void, onError?: (err: any) => void): () => void {
    const eventSource = new EventSource(`${API_BASE}/jobs/${jobId}/stream`);
    eventSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data) as LiveJobEvent;
        onEvent(parsed);
        if (parsed.event === 'job_completed' || parsed.event === 'job_error') {
          eventSource.close();
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };
    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      if (onError) onError(err);
      eventSource.close();
    };
    return () => {
      eventSource.close();
    };
  }
};