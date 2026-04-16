export default function CompareTray({ selected, onRemove, onClear, onCompare }) {
  if (!selected || selected.length === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
      <div className="bg-gray-900 border border-gray-700 shadow-2xl rounded-2xl p-3 flex items-center justify-between gap-6 min-w-[400px]">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-2 border-r border-gray-700">
            Compare Profiles
          </span>
          <div className="flex gap-2 relative">
            {selected.map((item, i) => (
              <div key={item.id} className="relative group/pill">
                <div className="flex items-center gap-2 bg-gray-800 border border-gray-600 rounded-full px-3 py-1.5 text-sm text-gray-200">
                  <span className="font-medium">{item.name}</span>
                </div>
                <button
                  onClick={() => onRemove(item.id)}
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 rounded-full text-white flex items-center justify-center opacity-0 group-hover/pill:opacity-100 transition-opacity"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))}
            {selected.length < 3 && (
              <div className="flex items-center gap-2 bg-gray-800/50 border border-gray-700 border-dashed rounded-full px-3 py-1.5 text-sm text-gray-500 italic">
                Add up to {3 - selected.length} more
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={onClear}
            className="text-xs text-gray-400 hover:text-white transition-colors"
          >
            Clear
          </button>
          <button
            onClick={onCompare}
            disabled={selected.length < 2}
            className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-semibold rounded-xl transition-colors"
          >
            Compare Now →
          </button>
        </div>
      </div>
    </div>
  );
}
