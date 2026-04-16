import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAutocomplete } from '../../api/client';
import { useDebounce } from '../../hooks/useDebounce';

/**
 * SearchBar — Prominent search input with autocomplete dropdown and quick query pills.
 */
export default function SearchBar({ value, onChange, onSearch, placeholder, showQuickQueries = false, size = 'normal' }) {
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const debouncedValue = useDebounce(value, 250);

  const quickQueries = [
    { label: 'ML engineers 2020', query: 'Find ML engineers from the 2020 batch' },
    { label: 'SDE → PM transitions', query: 'Who transitioned from software engineering to product management?' },
    { label: 'AI research mentors', query: 'Find mentors with experience in AI research' },
    { label: 'CS alumni in startups', query: 'Alumni from Computer Science who now work at startups in Bangalore' },
    { label: 'Data scientists', query: 'Find data scientists working in healthcare or fintech' },
  ];

  // Fetch autocomplete suggestions
  useEffect(() => {
    if (debouncedValue.length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }
    getAutocomplete(debouncedValue)
      .then(data => {
        if (data.suggestions?.length > 0) {
          setSuggestions(data.suggestions);
          setShowDropdown(true);
        } else {
          setSuggestions([]);
          setShowDropdown(false);
        }
      })
      .catch(() => setShowDropdown(false));
  }, [debouncedValue]);

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      if (activeIndex >= 0 && suggestions[activeIndex]) {
        selectSuggestion(suggestions[activeIndex].text);
      } else {
        setShowDropdown(false);
        handleSearch();
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => Math.max(prev - 1, -1));
    } else if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  }

  function selectSuggestion(text) {
    onChange(text);
    setShowDropdown(false);
    setActiveIndex(-1);
    // Navigate to search page and trigger search
    navigate('/search');
    setTimeout(() => onSearch?.(text), 100);
  }

  function handleSearch() {
    if (!value.trim()) return;
    navigate('/search');
    onSearch?.(value);
  }

  function handleQuickQuery(query) {
    onChange(query);
    navigate('/search');
    setTimeout(() => onSearch?.(query), 100);
  }

  const isLarge = size === 'large';

  return (
    <div className="w-full">
      {/* Search input container */}
      <div className="relative">
        <div className={`flex items-center bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md hover:border-gray-300 transition-all ${isLarge ? 'px-5 py-3.5' : 'px-4 py-2.5'}`}>
          {/* Search icon */}
          <svg className={`text-gray-300 flex-shrink-0 ${isLarge ? 'w-5 h-5' : 'w-4.5 h-4.5'}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => { onChange(e.target.value); setActiveIndex(-1); }}
            onKeyDown={handleKeyDown}
            onFocus={() => { if (suggestions.length > 0) setShowDropdown(true); }}
            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
            placeholder={placeholder || "Search alumni — try natural language queries..."}
            className={`flex-1 bg-transparent outline-none text-gray-800 placeholder:text-gray-300 ${isLarge ? 'ml-4 text-base' : 'ml-3 text-sm'}`}
            autoComplete="off"
          />

          {/* Search button */}
          <button
            onClick={handleSearch}
            className={`flex-shrink-0 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 active:bg-indigo-800 transition-colors ${isLarge ? 'px-6 py-2 text-sm' : 'px-4 py-1.5 text-xs'}`}
          >
            Search
          </button>
        </div>

        {/* Autocomplete dropdown */}
        {showDropdown && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-100 rounded-xl shadow-lg overflow-hidden z-20 max-h-64 overflow-y-auto">
            {suggestions.map((s, i) => (
              <button
                key={i}
                className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors ${
                  i === activeIndex ? 'bg-indigo-50' : 'hover:bg-gray-50'
                }`}
                onMouseDown={() => selectSuggestion(s.text)}
              >
                <span className="text-base flex-shrink-0">{s.icon}</span>
                <span className="text-gray-700 flex-1 truncate">{s.text}</span>
                <span className="text-[10px] text-gray-300 uppercase tracking-wider">{s.type}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Quick query pills */}
      {showQuickQueries && (
        <div className="flex items-center gap-2 mt-4 flex-wrap justify-center">
          <span className="text-xs text-gray-300 font-medium">Try:</span>
          {quickQueries.map((q, i) => (
            <button
              key={i}
              onClick={() => handleQuickQuery(q.query)}
              className="px-3 py-1.5 text-xs text-gray-500 bg-white border border-gray-150 rounded-full hover:border-indigo-200 hover:text-indigo-600 hover:bg-indigo-50/50 transition-all"
            >
              {q.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
