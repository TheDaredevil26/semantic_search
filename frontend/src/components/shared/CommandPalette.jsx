import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAutocomplete } from '../../api/client';

export default function CommandPalette({ onOpenProfile }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    } else {
      setQuery('');
    }
  }, [isOpen]);

  useEffect(() => {
    if (query.trim().length > 1) {
      setLoading(true);
      const timer = setTimeout(() => {
        getAutocomplete(query)
          .then(data => setResults(data.suggestions || []))
          .catch(() => setResults([]))
          .finally(() => setLoading(false));
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setResults([]);
    }
  }, [query]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-24 sm:pt-32 px-4 animate-fade-in">
      <div 
        className="absolute inset-0 bg-gray-900/20 backdrop-blur-sm transition-opacity" 
        onClick={() => setIsOpen(false)} 
      />
      
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden ring-1 ring-gray-200">
        <div className="flex items-center px-4 border-b border-gray-100">
          <svg className="w-5 h-5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            className="w-full px-3 py-4 text-sm bg-transparent border-none focus:outline-none focus:ring-0 text-gray-900 placeholder:text-gray-400"
            placeholder="Search alumni, skills, or companies... (Esc to close)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {loading && (
            <div className="w-4 h-4 border-2 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
          )}
          <div className="text-[10px] ml-2 px-1.5 py-0.5 rounded border border-gray-200 text-gray-400 font-mono">
            ESC
          </div>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {results.length === 0 && query.trim().length > 1 && !loading ? (
            <div className="p-6 text-center text-sm text-gray-500">
              No results found for "{query}"
            </div>
          ) : results.length > 0 ? (
            <ul className="p-2 space-y-1">
              {results.map((item, idx) => (
                <li key={idx}>
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      if (item.category === 'alumni') {
                        onOpenProfile(item.text); // assumes text is ID or we might want to do a search
                        // Actually, our autocomplete returns {text, category, icon}. 
                        // It represents general search strings. We should route to the Search page directly.
                        navigate(`/search?q=${encodeURIComponent(item.text)}`);
                      } else {
                        navigate(`/search?q=${encodeURIComponent(item.text)}`);
                      }
                    }}
                    className="w-full flex items-center justify-between px-4 py-3 text-sm text-gray-700 bg-white rounded-xl hover:bg-indigo-50 hover:text-indigo-700 group transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl opacity-60 group-hover:opacity-100">{item.icon}</span>
                      <span className="font-medium">{item.text}</span>
                    </div>
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 group-hover:text-indigo-400">
                      {item.category}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-6">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Quick Navigation</h3>
              <div className="grid grid-cols-2 gap-2">
                {['Home', 'Search Directory', 'Network Graph'].map(path => (
                  <button 
                     key={path}
                     onClick={() => {
                       setIsOpen(false);
                       navigate(path === 'Home' ? '/' : path === 'Search Directory' ? '/search' : '/network');
                     }}
                     className="px-3 py-2 text-sm text-left text-gray-600 bg-gray-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-colors border border-gray-100 font-medium"
                   >
                     {path}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
