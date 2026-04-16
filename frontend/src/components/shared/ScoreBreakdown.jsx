import { getExportUrl } from '../../api/client';

/**
 * ScoreBreakdown — General utility panel to show explainability metrics.
 */
export default function ScoreBreakdown({ query, hasResults, latencyMs, intent, graphWeight }) {
  if (!hasResults) return null;

  return (
    <div className="flex items-center justify-between py-3 mb-6 border-b border-gray-100 bg-white">
      <div className="flex items-center gap-4 text-xs">
        {/* Latency */}
        <span className="flex items-center gap-1.5 text-gray-500">
          <svg className="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span className="font-mono text-gray-700">{latencyMs.toFixed(0)}</span> ms
        </span>

        {/* Intent Info */}
        {intent && intent.resolved_entities && Object.keys(intent.resolved_entities).length > 0 && (
          <span className="flex items-center gap-2 px-3 py-1 bg-indigo-50/50 border border-indigo-100 rounded-md">
            <span className="text-indigo-400 font-medium tracking-wide uppercase text-[10px]">Intent</span>
            <span className="text-indigo-700 font-medium">{intent.query_type}</span>
            <div className="w-px h-3 bg-indigo-200 mx-1" />
            {Object.entries(intent.resolved_entities).slice(0, 2).map(([k, v], i) => (
              <span key={i} className="text-gray-600 truncate max-w-[150px]">
                {k}: <span className="font-medium">{v}</span>
              </span>
            ))}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <a
          href={getExportUrl(query, 20, graphWeight)}
          download
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export CSV
        </a>
      </div>
    </div>
  );
}
