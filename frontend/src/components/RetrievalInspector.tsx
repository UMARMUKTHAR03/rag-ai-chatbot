import React, { useState } from 'react';
import { Search, Sparkles, Filter, FileText, CheckCircle2 } from 'lucide-react';
import { ModelProvider } from '../types';
import { ApiService } from '../services/api';

interface RetrievalInspectorProps {
  provider: ModelProvider;
  sessionId: string;
}

export const RetrievalInspector: React.FC<RetrievalInspectorProps> = ({ provider, sessionId }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    try {
      const data = await ApiService.searchRetrieval(query, sessionId, provider);
      setResults(data);
    } catch (err: any) {
      alert(`Search error: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Search className="w-5 h-5 text-emerald-400" />
          Semantic Retrieval & Vector Index Inspector
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Test vector similarity, hybrid ranking, and inspect matched document passages directly.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a test query to inspect retrieved semantic passages..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold disabled:opacity-40 transition"
        >
          <Search className="w-4 h-4" />
          {isSearching ? 'Searching...' : 'Inspect Retrieval'}
        </button>
      </form>

      {/* Results */}
      <div className="space-y-3">
        {hasSearched && results.length === 0 && !isSearching && (
          <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-500">
            No matching chunks found above similarity threshold. Ensure documents are uploaded in the Knowledge Library.
          </div>
        )}

        {results.map((r, idx) => (
          <div
            key={idx}
            className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2 shadow-sm"
          >
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-md bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-mono font-bold text-[10px]">
                  #{idx + 1}
                </span>
                <span className="font-semibold text-slate-200">{r.metadata?.source || 'Document'}</span>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400 font-mono">
                  {r.metadata?.page ? `Page ${r.metadata.page}` : r.metadata?.slide ? `Slide ${r.metadata.slide}` : `Chunk ${r.metadata?.chunk_index ?? 0}`}
                </span>
              </div>

              <div className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                <span>Score:</span>
                <span className="font-bold">{(r.similarity_score * 100).toFixed(1)}%</span>
              </div>
            </div>

            <p className="text-slate-300 whitespace-pre-wrap leading-relaxed font-sans text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-850">
              {r.content}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
