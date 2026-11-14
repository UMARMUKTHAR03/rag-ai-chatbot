export type ModelProvider = 'gemini' | 'groq';

export interface Citation {
  source: string;
  location: string;
  file_type: string;
  similarity_score: number;
  snippet: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  citations?: Citation[];
  imageUrl?: string;
  audioUrl?: string;
  isStreaming?: boolean;
}

export interface UploadedDoc {
  document_id: string;
  filename: string;
  chunk_count: number;
  source: string;
}

export interface HealthData {
  app_name: string;
  version: string;
  tagline: string;
  providers: {
    groq: {
      provider: string;
      configured: boolean;
      status: string;
      chat_models: string[];
      vision_models: string[];
      audio_models: string[];
    };
    gemini: {
      provider: string;
      configured: boolean;
      status: string;
      chat_models: string[];
      vision_models: string[];
      audio_models: string[];
    };
  };
  supported_modalities: string[];
}
