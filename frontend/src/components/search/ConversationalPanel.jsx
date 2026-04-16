import { useState, useRef, useEffect } from 'react';
import { conversationalSearch } from '../../api/client';
import { useToast } from '../shared/Toast';

/**
 * ConversationalPanel — Collapsible UI for multi-turn conversational search.
 */
export default function ConversationalPanel({ initialQuery, onSearchResponse }) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const historyEndRef = useRef(null);
  const { addToast } = useToast();

  useEffect(() => {
    if (historyEndRef.current) {
      historyEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [history]);

  async function handleSend() {
    const q = input.trim();
    if (!q) return;

    const newTurn = { role: 'user', content: q };
    setHistory(prev => [...prev, newTurn]);
    setInput('');
    setIsLoading(true);

    try {
      const data = await conversationalSearch({
        query: q,
        conversation_history: history, // send history *before* this query
        page: 1,
        limit: 20,
      });

      const filters = data.applied_filters || {};
      const filterParts = Object.entries(filters)
        .filter(([, v]) => v && (!Array.isArray(v) || v.length > 0))
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`);

      const assistantMsg = filterParts.length > 0
        ? `Found ${data.total_count} results. Active filters: ${filterParts.join(' | ')}`
        : `Found ${data.total_count} results for "${data.resolved_query || q}"`;

      setHistory(prev => [...prev, { role: 'assistant', content: assistantMsg }]);

      // Pass the fully resolved backend state back to the search page
      onSearchResponse?.({
        ...data,
        query: data.resolved_query || q,
      });

    } catch (err) {
      setHistory(prev => [...prev, { role: 'assistant', content: `Sorry: ${err.message}` }]);
      addToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  }

  function handleReset() {
    setHistory([]);
    addToast('Conversation reset', 'info');
  }

  return (
    <div className="mb-6 bg-white border border-gray-100 rounded-xl overflow-hidden shadow-sm">
      {/* Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gray-50/50 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <span className="text-sm font-medium text-gray-800">Multi-Turn Conversational Search</span>
          <span className="text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded ml-2">Beta</span>
        </div>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Body */}
      {isOpen && (
        <div className="px-4 pb-4 animate-slide-up">
          <div className="h-48 overflow-y-auto mb-3 pr-2 space-y-3 pt-2">
            {history.length === 0 ? (
              <div className="h-full flex items-center justify-center text-sm text-gray-400 text-center">
                Refine your search naturally.<br />Try: "Find ML engineers" → "filter to Bangalore" → "from 2019"
              </div>
            ) : (
              history.map((turn, i) => (
                <div key={i} className={`flex ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                    turn.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}>
                    {turn.content}
                  </div>
                </div>
              ))
            )}
            <div ref={historyEndRef} />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="e.g. 'Only show those in Bangalore'..."
              className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-100"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-indigo-600 text-white disabled:opacity-50 hover:bg-indigo-700 transition-colors"
            >
              {isLoading ? (
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="31.4" strokeDashoffset="10" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
            <button
              onClick={handleReset}
              className="px-3 py-2 text-xs text-gray-500 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
            >
              Reset
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
