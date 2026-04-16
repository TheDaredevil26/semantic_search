import { useState, useEffect } from 'react';
import { getSimilarAlumni } from '../../api/client';

/**
 * SimilarPanel — Side panel displaying similar alumni.
 */
export default function SimilarPanel({ alumniId, onOpenProfile, onViewGraph }) {
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!alumniId) return;

    setLoading(true);
    setError(null);
    getSimilarAlumni(alumniId)
      .then(data => {
        setSimilar(data.similar || []);
      })
      .catch(err => {
        setError(err.message);
        setSimilar([]);
      })
      .finally(() => setLoading(false));
  }, [alumniId]);

  if (!alumniId) {
    return (
      <div className="bg-white border flex-shrink-0 border-gray-100 rounded-xl p-5 w-80 shadow-sm flex flex-col items-center justify-center text-center h-[calc(100vh-140px)]">
        <svg className="w-12 h-12 text-gray-200 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 16v-4" />
          <path d="M12 8h.01" />
        </svg>
        <p className="text-sm text-gray-400">Select an alumni from the graph or search to find similar profiles.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border flex-shrink-0 border-gray-100 rounded-xl flex flex-col w-80 shadow-sm h-[calc(100vh-140px)] overflow-hidden">
      <div className="p-4 border-b border-gray-50 flex items-center gap-2">
        <svg className="w-4 h-4 text-indigo-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 00-3-3.87" />
          <path d="M16 3.13a4 4 0 010 7.75" />
        </svg>
        <h3 className="font-semibold text-gray-900 text-sm">Similar Alumni</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="p-3 flex justify-center">
            <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="p-4 text-center text-xs text-red-500 bg-red-50 rounded-lg m-2">
            Failed to load similarities.
          </div>
        ) : similar.length === 0 ? (
          <div className="p-4 text-center text-xs text-gray-400">No similar alumni found.</div>
        ) : (
          <div className="space-y-1">
            {similar.map(alumni => (
              <div key={alumni.id} className="p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors group">
                <div className="flex justify-between items-start mb-1">
                  <h4
                    className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors"
                    onClick={() => onOpenProfile?.(alumni.id)}
                  >
                    {alumni.name}
                  </h4>
                  <span className="text-[10px] font-mono font-medium text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                    {(alumni.similarity * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-2 truncate">{alumni.role} at {alumni.company}</p>

                <div className="flex gap-1">
                  <button
                    onClick={(e) => { e.stopPropagation(); onViewGraph?.(alumni.id, alumni.name); }}
                    className="flex-1 py-1 px-2 text-[10px] font-medium text-gray-600 bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors text-center"
                  >
                    View Graph
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); onOpenProfile?.(alumni.id); }}
                    className="flex-1 py-1 px-2 text-[10px] font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 transition-colors text-center"
                  >
                    Profile
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
