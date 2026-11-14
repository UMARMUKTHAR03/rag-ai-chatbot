import React, { useRef, useState } from 'react';
import { 
  Upload, 
  Trash2, 
  FileText, 
  Layers, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle,
  FileSpreadsheet,
  Presentation,
  Image,
  RefreshCw
} from 'lucide-react';
import { UploadedDoc, ModelProvider } from '../types';
import { ApiService } from '../services/api';

interface KnowledgeLibraryProps {
  provider: ModelProvider;
  sessionId: string;
  docs: UploadedDoc[];
  onRefresh: () => void;
}

export const KnowledgeLibrary: React.FC<KnowledgeLibraryProps> = ({
  provider,
  sessionId,
  docs,
  onRefresh,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    try {
      await ApiService.uploadDocuments(Array.from(files), provider, sessionId);
      onRefresh();
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (confirm('Delete this document and remove its chunks from the knowledge base?')) {
      await ApiService.deleteDocument(docId, sessionId, provider);
      onRefresh();
    }
  };

  const handleClearAll = async () => {
    if (confirm('Clear all indexed documents in this session?')) {
      await ApiService.clearSession(sessionId);
      onRefresh();
    }
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            Knowledge Library & Multimodal Ingestion
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Session-isolated document storage and semantic vector index.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
          {docs.length > 0 && (
            <button
              onClick={handleClearAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear Library
            </button>
          )}
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragEnter={() => setDragActive(true)}
        onDragLeave={() => setDragActive(false)}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-emerald-400 bg-emerald-500/10'
            : 'border-slate-800 hover:border-emerald-500/40 bg-slate-900/60'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="hidden"
          accept=".pdf,.docx,.pptx,.txt,.md,.csv,.xlsx"
        />

        <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4">
          <Upload className={`w-7 h-7 ${isUploading ? 'animate-bounce' : ''}`} />
        </div>

        <h3 className="font-semibold text-white text-base">
          {isUploading ? 'Ingesting & Indexing Documents...' : 'Upload Knowledge Documents'}
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Drag and drop PDF, Word (DOCX), PowerPoint (PPTX), Excel (XLSX), CSV, Markdown, or plain text files.
        </p>

        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {['PDF', 'DOCX', 'PPTX', 'TXT', 'MD', 'CSV', 'XLSX'].map((fmt) => (
            <span
              key={fmt}
              className="px-2.5 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-[10px] font-mono text-slate-400"
            >
              {fmt}
            </span>
          ))}
        </div>
      </div>

      {/* Uploaded Documents List */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-300">
          Indexed Documents ({docs.length})
        </h3>

        {docs.length === 0 ? (
          <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-500">
            No documents uploaded yet. Upload files above to build your session knowledge index.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {docs.map((d) => (
              <div
                key={d.document_id}
                className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs"
              >
                <div className="flex items-center gap-3 truncate">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 text-emerald-400 flex items-center justify-center shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <p className="font-medium text-white truncate">{d.filename}</p>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {d.chunk_count} semantic chunks indexed
                    </p>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(d.document_id);
                  }}
                  className="p-1.5 hover:text-rose-400 text-slate-500 rounded-lg hover:bg-slate-800 transition"
                  title="Delete Document"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
