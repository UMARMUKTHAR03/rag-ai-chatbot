import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Paperclip, 
  Image as ImageIcon, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  RotateCcw, 
  Copy, 
  Check, 
  BookOpen, 
  ExternalLink, 
  Sparkles, 
  Trash2,
  FileText
} from 'lucide-react';
import { ChatMessage, ModelProvider, UploadedDoc } from '../types';
import { ApiService } from '../services/api';

interface ChatWorkspaceProps {
  provider: ModelProvider;
  sessionId: string;
  uploadedDocs: UploadedDoc[];
  onRefreshDocs: () => void;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  provider,
  sessionId,
  uploadedDocs,
  onRefreshDocs,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am **OmniMind AI**, your unified multimodal knowledge assistant. You can upload documents (PDF, DOCX, PPTX, CSV, Excel), send images for vision analysis, record or upload speech audio, or ask open-domain questions with grounded RAG citations.',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [activeSpeechText, setActiveSpeechText] = useState<string | null>(null);

  // Attachment states
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<File | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSpeak = (text: string) => {
    if (!('speechSynthesis' in window)) {
      alert('Browser speech synthesis is not supported in this browser.');
      return;
    }

    if (isSpeaking && activeSpeechText === text) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setActiveSpeechText(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.replace(/[#*`_\[\]]/g, ''));
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      setIsSpeaking(false);
      setActiveSpeechText(null);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setActiveSpeechText(null);
    };

    setIsSpeaking(true);
    setActiveSpeechText(text);
    window.speechSynthesis.speak(utterance);
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const url = URL.createObjectURL(file);
      setImagePreview(url);
    }
  };

  const handleDocSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedDoc(file);
      try {
        setIsLoading(true);
        await ApiService.uploadDocuments([file], provider, sessionId);
        onRefreshDocs();
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            role: 'assistant',
            content: `Document **${file.filename || file.name}** has been processed and indexed into your private knowledge base. You can now ask questions about it!`,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      } catch (err: any) {
        alert(`Upload failed: ${err.message}`);
      } finally {
        setSelectedDoc(null);
        setIsLoading(false);
      }
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Detect browser-supported recording MIME type
      let mimeType = 'audio/webm;codecs=opus';
      let extension = 'webm';

      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
        extension = 'webm';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
        extension = 'webm';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
        extension = 'm4a';
      } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
        extension = 'ogg';
      } else if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav';
        extension = 'wav';
      }

      const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const actualMime = mediaRecorder.mimeType || mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: actualMime });
        stream.getTracks().forEach((track) => track.stop());

        if (audioBlob.size === 0) {
          alert('Recorded audio was empty. Please check your microphone.');
          return;
        }

        try {
          setIsLoading(true);
          const recordingFilename = `microphone_recording.${extension}`;
          const res = await ApiService.transcribeAudio(audioBlob, recordingFilename, 'groq', sessionId);
          if (res && res.text) {
            setInput((prev) => (prev ? `${prev} ${res.text}` : res.text));
          } else {
            alert('No speech could be recognized in the recording.');
          }
        } catch (err: any) {
          alert(`Speech transcription failed: ${err.message}`);
        } finally {
          setIsLoading(false);
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);
    } catch (err: any) {
      alert(`Could not access microphone: ${err.message}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleSend = async () => {
    if ((!input.trim() && !selectedImage) || isLoading) return;

    const userMessageText = input.trim() || (selectedImage ? 'Analyze this image.' : '');
    const currentImage = selectedImage;
    const currentPreview = imagePreview;

    setInput('');
    setSelectedImage(null);
    setImagePreview(null);

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: userMessageText,
      imageUrl: currentPreview || undefined,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 1. If an image is attached, run image analysis first
      if (currentImage) {
        const imgAnalysis = await ApiService.analyzeImage(currentImage, userMessageText, provider, sessionId);
        onRefreshDocs();

        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now() + 1),
            role: 'assistant',
            content: `**[Multimodal Vision Analysis]**\n\n${imgAnalysis.description}`,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      } else {
        // 2. Regular or RAG chat
        const res = await ApiService.chat(userMessageText, messages, provider, undefined, sessionId, useRag);

        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now() + 1),
            role: 'assistant',
            content: res.answer,
            citations: res.citations,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: `⚠️ **Error:** ${err.message}. If running locally, check that the backend is active at \`${ApiService.getBaseUrl()}\` and valid API keys are configured.`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-65px)] max-w-5xl mx-auto w-full p-2 sm:p-4">
      {/* Session Header / Controls */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-emerald-400" />
          <span>Knowledge Documents Indexed:</span>
          <span className="font-mono text-emerald-400 font-semibold">{uploadedDocs.length}</span>
          <span className="text-slate-600">|</span>
          <label className="flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              className="accent-emerald-500 rounded"
            />
            <span>Enable RAG Retrieval</span>
          </label>
        </div>

        <button
          onClick={() => {
            if (confirm('Clear current chat messages?')) {
              setMessages([messages[0]]);
            }
          }}
          className="flex items-center gap-1 text-slate-400 hover:text-rose-400 transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Chat
        </button>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-1">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-md leading-relaxed ${
                m.role === 'user'
                  ? 'bg-emerald-600 text-white rounded-br-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none'
              }`}
            >
              {m.imageUrl && (
                <div className="mb-2.5">
                  <img
                    src={m.imageUrl}
                    alt="User Upload"
                    className="max-h-60 rounded-xl border border-slate-700 object-cover"
                  />
                </div>
              )}

              <div className="whitespace-pre-wrap">{m.content}</div>

              {/* Citations Box */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> Grounded Source Citations
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {m.citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between text-slate-300 font-medium">
                          <span className="truncate max-w-[160px] text-emerald-300">{c.source}</span>
                          <span className="font-mono text-[10px] text-slate-400">{c.location}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 italic line-clamp-2">"{c.snippet}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Message Action Bar */}
            <div className="flex items-center gap-3 mt-1 px-1 text-[11px] text-slate-500">
              <span>{m.timestamp}</span>
              {m.role === 'assistant' && (
                <>
                  <button
                    onClick={() => handleCopy(m.id, m.content)}
                    className="hover:text-slate-300 flex items-center gap-1"
                    title="Copy message"
                  >
                    {copiedId === m.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    {copiedId === m.id ? 'Copied' : 'Copy'}
                  </button>
                  <button
                    onClick={() => handleSpeak(m.content)}
                    className="hover:text-slate-300 flex items-center gap-1"
                    title="Listen with text to speech"
                  >
                    {isSpeaking && activeSpeechText === m.content ? (
                      <VolumeX className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Volume2 className="w-3 h-3" />
                    )}
                    Listen
                  </button>
                </>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 animate-pulse bg-slate-900 border border-slate-800 px-4 py-2.5 rounded-2xl w-fit">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>OmniMind AI is reasoning and synthesizing response...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Composer */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-2.5 shadow-xl relative">
        {/* Preview Strip */}
        {imagePreview && (
          <div className="flex items-center gap-2 mb-2 p-1.5 rounded-xl bg-slate-950 border border-slate-800 w-fit">
            <img src={imagePreview} alt="Preview" className="w-12 h-12 rounded-lg object-cover" />
            <span className="text-xs text-slate-300 max-w-[200px] truncate">{selectedImage?.name}</span>
            <button
              onClick={() => {
                setSelectedImage(null);
                setImagePreview(null);
              }}
              className="p-1 hover:text-rose-400 text-slate-500"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          {/* File Upload hidden inputs */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleDocSelect}
            className="hidden"
            accept=".pdf,.docx,.pptx,.txt,.md,.csv,.xlsx"
          />
          <input
            type="file"
            ref={imageInputRef}
            onChange={handleImageSelect}
            className="hidden"
            accept="image/png,image/jpeg,image/webp"
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 rounded-xl text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition"
            title="Attach Document (PDF, Word, PPTX, Excel, CSV, TXT)"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          <button
            type="button"
            onClick={() => imageInputRef.current?.click()}
            className="p-2 rounded-xl text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition"
            title="Attach Image for Vision Understanding"
          >
            <ImageIcon className="w-5 h-5" />
          </button>

          <button
            type="button"
            onClick={isRecording ? stopRecording : startRecording}
            className={`p-2 rounded-xl transition ${
              isRecording
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
                : 'text-slate-400 hover:text-emerald-400 hover:bg-slate-800'
            }`}
            title={isRecording ? 'Stop Recording' : 'Record Audio with Microphone'}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question, analyze an image, or query uploaded documents..."
            rows={1}
            className="flex-1 bg-transparent border-0 text-white placeholder-slate-500 focus:outline-none text-sm resize-none px-2 py-1 max-h-32"
          />

          <button
            type="button"
            onClick={handleSend}
            disabled={isLoading || (!input.trim() && !selectedImage)}
            className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition shadow-lg shadow-emerald-600/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
