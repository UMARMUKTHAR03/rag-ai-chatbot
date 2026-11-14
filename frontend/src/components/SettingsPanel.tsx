import React, { useState } from 'react';
import { Settings as SettingsIcon, Server, ShieldCheck, Cpu, Globe2, Save, Check } from 'lucide-react';
import { ApiService } from '../services/api';
import { HealthData } from '../types';

interface SettingsPanelProps {
  health: HealthData | null;
  onRefreshHealth: () => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ health, onRefreshHealth }) => {
  const [apiUrl, setApiUrl] = useState(ApiService.getBaseUrl());
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    ApiService.setBaseUrl(apiUrl);
    setSaved(true);
    onRefreshHealth();
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto w-full p-4 sm:p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-emerald-400" />
          Settings & Connectivity Configuration
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Configure backend API connection endpoints and inspect server health status.
        </p>
      </div>

      {/* Backend API Configuration */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Server className="w-4 h-4 text-emerald-400" />
          Backend API Endpoint
        </h3>

        <div className="flex gap-2">
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="https://omnimind-ai-backend-bgzb.onrender.com or http://127.0.0.1:8000"
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white font-mono focus:outline-none focus:border-emerald-500"
          />
          <button
            onClick={handleSave}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
          >
            {saved ? <Check className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
            {saved ? 'Saved' : 'Save'}
          </button>
        </div>

        <div className="flex flex-wrap gap-2 pt-2">
          <button
            onClick={() => {
              setApiUrl('http://127.0.0.1:8000');
              ApiService.setBaseUrl('http://127.0.0.1:8000');
              onRefreshHealth();
            }}
            className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300"
          >
            Local: http://127.0.0.1:8000
          </button>
          <button
            onClick={() => {
              setApiUrl('https://omnimind-ai-backend-bgzb.onrender.com');
              ApiService.setBaseUrl('https://omnimind-ai-backend-bgzb.onrender.com');
              onRefreshHealth();
            }}
            className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300"
          >
            Production Render: https://omnimind-ai-backend-bgzb.onrender.com
          </button>
        </div>
      </div>

      {/* Provider Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Gemini */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-white text-sm flex items-center gap-2">
              <Globe2 className="w-4 h-4 text-emerald-400" />
              Google Gemini
            </h4>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-mono capitalize ${
                health?.providers.gemini.status === 'online'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}
            >
              {health?.providers.gemini.status || 'unknown'}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Multimodal language & vision reasoning with Google Gemini 3.8 Flash (and Gemini 3.5 Flash-Lite).
          </p>

          <div className="text-[11px] font-mono text-slate-400 space-y-1">
            <p>Chat Models: {health?.providers.gemini.chat_models?.join(', ') || 'gemini-3.8-flash'}</p>
            <p>Vision: Supported (Native Image Analysis)</p>
          </div>
        </div>

        {/* Groq */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-white text-sm flex items-center gap-2">
              <Cpu className="w-4 h-4 text-teal-400" />
              Groq Cloud
            </h4>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-mono capitalize ${
                health?.providers.groq.status === 'online'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}
            >
              {health?.providers.groq.status || 'unknown'}
            </span>
          </div>

          <p className="text-xs text-slate-400">
            Ultra-fast inference with OpenAI GPT-OSS 120B / 20B & Whisper Large v3 speech transcription on LPUs.
          </p>

          <div className="text-[11px] font-mono text-slate-400 space-y-1">
            <p>Chat Models: {health?.providers.groq.chat_models?.join(', ') || 'openai/gpt-oss-120b'}</p>
            <p>Audio STT: whisper-large-v3-turbo</p>
          </div>
        </div>
      </div>

      {/* Security & Data Scope Notice */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex items-start gap-3 text-xs text-slate-400">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-slate-300">Session Scoping & Data Retention Notice:</span>
          <p className="text-slate-400 leading-relaxed">
            Uploaded files and vector indices are scoped per active browser session ID. Temporary document chunks and session vectors are stored in ephemeral server storage (<code className="text-emerald-400">/tmp</code>) and are deleted when the session is cleared or during backend hibernation.
          </p>
          <p className="text-slate-400 leading-relaxed">
            OmniMind AI operates in public demonstration mode without persistent user authentication or cryptographic session authorization. Do not upload confidential, sensitive, or personally identifiable data.
          </p>
        </div>
      </div>
    </div>
  );
};
