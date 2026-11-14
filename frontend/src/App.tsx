import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ChatWorkspace } from './components/ChatWorkspace';
import { KnowledgeLibrary } from './components/KnowledgeLibrary';
import { RetrievalInspector } from './components/RetrievalInspector';
import { SettingsPanel } from './components/SettingsPanel';
import { HealthData, ModelProvider, UploadedDoc } from './types';
import { ApiService } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'library' | 'inspector' | 'settings'>('chat');
  const [provider, setProvider] = useState<ModelProvider>('gemini');
  const [health, setHealth] = useState<HealthData | null>(null);
  const [docs, setDocs] = useState<UploadedDoc[]>([]);
  const [sessionId] = useState<string>(() => {
    let s = localStorage.getItem('omnimind_session_id');
    if (!s) {
      s = `sess_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem('omnimind_session_id', s);
    }
    return s;
  });

  const fetchHealth = async () => {
    try {
      const data = await ApiService.getHealth();
      setHealth(data);
    } catch {
      setHealth({
        app_name: 'OmniMind AI',
        version: '2.0.0',
        tagline: 'One AI. Every Modality. All Your Knowledge.',
        providers: {
          groq: { provider: 'Groq', configured: false, status: 'offline', chat_models: [], vision_models: [], audio_models: [] },
          gemini: { provider: 'Gemini', configured: false, status: 'offline', chat_models: [], vision_models: [], audio_models: [] }
        },
        supported_modalities: ['text', 'pdf', 'docx', 'pptx', 'csv', 'xlsx', 'image', 'audio']
      });
    }
  };

  const fetchDocs = async () => {
    try {
      const documents = await ApiService.getDocuments(sessionId, provider);
      setDocs(documents);
    } catch {
      setDocs([]);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchDocs();
  }, [provider]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
      <Header
        health={health}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedProvider={provider}
        setSelectedProvider={setProvider}
      />

      <main className="flex-1 flex flex-col">
        {activeTab === 'chat' && (
          <ChatWorkspace
            provider={provider}
            sessionId={sessionId}
            uploadedDocs={docs}
            onRefreshDocs={fetchDocs}
          />
        )}

        {activeTab === 'library' && (
          <KnowledgeLibrary
            provider={provider}
            sessionId={sessionId}
            docs={docs}
            onRefresh={fetchDocs}
          />
        )}

        {activeTab === 'inspector' && (
          <RetrievalInspector
            provider={provider}
            sessionId={sessionId}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsPanel
            health={health}
            onRefreshHealth={fetchHealth}
          />
        )}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-3 text-center text-xs text-slate-500">
        OmniMind AI v2.0 • Multimodal Knowledge Assistant • Developed by UMAR MUKTHAR
      </footer>
    </div>
  );
}

export default App;
