import { useState, useEffect } from 'react';
import { findPath, getAlumniList } from '../../api/client';

/**
 * PathFinder — UI to find shortest paths between two alumni.
 */
export default function PathFinder({ onViewGraph }) {
  const [sourceId, setSourceId] = useState('');
  const [targetId, setTargetId] = useState('');
  const [sourceQuery, setSourceQuery] = useState('');
  const [targetQuery, setTargetQuery] = useState('');
  const [sourceList, setSourceList] = useState([]);
  const [targetList, setTargetList] = useState([]);

  const [pathResult, setPathResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Simple debounced search for dropdowns
  useEffect(() => {
    if (sourceQuery.length > 2) {
      getAlumniList(sourceQuery).then(data => setSourceList(data.alumni || [])).catch(() => {});
    } else {
      setSourceList([]);
    }
  }, [sourceQuery]);

  useEffect(() => {
    if (targetQuery.length > 2) {
      getAlumniList(targetQuery).then(data => setTargetList(data.alumni || [])).catch(() => {});
    } else {
      setTargetList([]);
    }
  }, [targetQuery]);

  async function handleFindPath() {
    if (!sourceId || !targetId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await findPath(sourceId, targetId);
      if (data.path && data.path.length > 0) {
        setPathResult(data);
      } else {
        setError('No connection path found between these alumni.');
        setPathResult(null);
      }
    } catch (err) {
      setError(err.message);
      setPathResult(null);
    } finally {
      setLoading(false);
    }
  }

  function renderDropdown(list, setQuery, setId) {
    if (list.length === 0) return null;
    return (
      <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-100 rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
        {list.map(item => (
          <div
            key={item.id}
            className="px-3 py-2 text-xs hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0"
            onClick={() => {
              setQuery(item.name);
              setId(item.id);
              setList([]); // Clear dropdown after selection
            }}
          >
            <div className="font-medium text-gray-800">{item.name}</div>
            <div className="text-gray-400 text-[10px] truncate">{item.id}</div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm mb-6 animate-fade-in">
      <div className="flex flex-col md:flex-row gap-4 items-end">
        {/* Source */}
        <div className="flex-1 relative w-full">
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Origin Alumni</label>
          <input
            type="text"
            value={sourceQuery}
            onChange={e => { setSourceQuery(e.target.value); setSourceId(''); }}
            placeholder="Search by name..."
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-100"
          />
          {sourceId === '' && renderDropdown(sourceList, setSourceQuery, setSourceId)}
        </div>

        {/* Target */}
        <div className="flex-1 relative w-full">
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Destination Alumni</label>
          <input
            type="text"
            value={targetQuery}
            onChange={e => { setTargetQuery(e.target.value); setTargetId(''); }}
            placeholder="Search by name..."
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-100"
          />
          {targetId === '' && renderDropdown(targetList, setTargetQuery, setTargetId)}
        </div>

        {/* Action */}
        <button
          onClick={handleFindPath}
          disabled={!sourceId || !targetId || loading}
          className="w-full md:w-auto px-6 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Finding...' : 'Find Connection Path'}
        </button>
      </div>

      {/* Results */}
      {error && (
        <div className="mt-4 p-3 bg-amber-50 text-amber-700 text-xs rounded-lg border border-amber-100">
          {error}
        </div>
      )}

      {pathResult && (
        <div className="mt-4 pt-4 border-t border-gray-50">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-gray-800 bg-gray-100 px-2.5 py-1 rounded-md">
              {pathResult.length} Degrees of Separation
            </span>
            {pathResult.nodes && pathResult.nodes.length > 0 && (
              <button
                onClick={() => onViewGraph?.(pathResult)}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
              >
                Visualize Path in Graph →
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {pathResult.path.map((node, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className={`px-2.5 py-1 text-xs rounded border ${
                   i === 0 ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                 : i === pathResult.path.length - 1 ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                 : 'bg-white border-gray-200 text-gray-600'
                }`}>
                  {node}
                </span>
                {i < pathResult.path.length - 1 && (
                  <svg className="w-3 h-3 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
