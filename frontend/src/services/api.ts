import { HealthData, ModelProvider, ChatMessage, UploadedDoc, Citation } from '../types';

const STORAGE_KEY_API_URL = 'omnimind_api_base_url';
const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export class ApiService {
  private static baseUrl = localStorage.getItem(STORAGE_KEY_API_URL) || DEFAULT_API_URL;

  public static getBaseUrl(): string {
    return this.baseUrl;
  }

  public static setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
    localStorage.setItem(STORAGE_KEY_API_URL, this.baseUrl);
  }

  public static async getHealth(): Promise<HealthData> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new Error(`Health check failed with HTTP ${res.status}`);
    const json = await res.json();
    return json.data;
  }

  public static async getModels(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/models`);
    if (!res.ok) throw new Error(`Failed to fetch models with HTTP ${res.status}`);
    const json = await res.json();
    return json.data;
  }

  public static async uploadDocuments(
    files: File[],
    provider: ModelProvider = 'gemini',
    sessionId: string = 'default'
  ): Promise<{ session_id: string; total_chunks: number; files: any[] }> {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    formData.append('model_provider', provider);
    formData.append('session_id', sessionId);

    const res = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || 'Failed to upload documents');
    }
    const json = await res.json();
    return json.data;
  }

  public static async getDocuments(sessionId: string = 'default', provider: ModelProvider = 'gemini'): Promise<UploadedDoc[]> {
    const res = await fetch(`${this.baseUrl}/documents?session_id=${encodeURIComponent(sessionId)}&model_provider=${provider}`);
    if (!res.ok) return [];
    const json = await res.json();
    return json.data?.documents || [];
  }

  public static async deleteDocument(docId: string, sessionId: string = 'default', provider: ModelProvider = 'gemini') {
    const res = await fetch(`${this.baseUrl}/documents/${encodeURIComponent(docId)}?session_id=${encodeURIComponent(sessionId)}&model_provider=${provider}`, {
      method: 'DELETE',
    });
    return res.ok;
  }

  public static async clearSession(sessionId: string = 'default') {
    const res = await fetch(`${this.baseUrl}/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
    });
    return res.ok;
  }

  public static async chat(
    message: string,
    history: ChatMessage[],
    provider: ModelProvider = 'gemini',
    modelName?: string,
    sessionId: string = 'default',
    useRag: boolean = true
  ): Promise<{ answer: string; citations: Citation[]; model: string; provider: string; context_used: boolean }> {
    const payload = {
      message,
      model_provider: provider,
      model_name: modelName,
      session_id: sessionId,
      conversation_history: history.map((h) => ({ role: h.role, content: h.content })),
      use_rag: useRag,
    };

    const res = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || `Chat request failed (${res.status})`);
    }

    const json = await res.json();
    return json.data;
  }

  public static async analyzeImage(
    imageFile: File,
    prompt: string,
    provider: ModelProvider = 'gemini',
    sessionId: string = 'default'
  ): Promise<{ description: string; model: string; provider: string }> {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('prompt', prompt);
    formData.append('model_provider', provider);
    formData.append('session_id', sessionId);
    formData.append('index_description_for_rag', 'true');

    const res = await fetch(`${this.baseUrl}/images/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || 'Image analysis failed');
    }

    const json = await res.json();
    return json.data;
  }

  public static async transcribeAudio(
    audioFile: File | Blob,
    filename: string = 'recording.wav',
    provider: ModelProvider = 'groq',
    sessionId: string = 'default'
  ): Promise<{ text: string; duration: number; model: string }> {
    const formData = new FormData();
    formData.append('audio', audioFile, filename);
    formData.append('model_provider', provider);
    formData.append('session_id', sessionId);
    formData.append('index_transcription_for_rag', 'true');

    const res = await fetch(`${this.baseUrl}/audio/transcribe`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: res.statusText }));
      throw new Error(err.message || 'Audio transcription failed');
    }

    const json = await res.json();
    return json.data;
  }

  public static async searchRetrieval(query: string, sessionId: string = 'default', provider: ModelProvider = 'gemini'): Promise<any[]> {
    const res = await fetch(`${this.baseUrl}/retrieval/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId, model_provider: provider, top_k: 5 }),
    });
    if (!res.ok) return [];
    const json = await res.json();
    return json.data || [];
  }
}
