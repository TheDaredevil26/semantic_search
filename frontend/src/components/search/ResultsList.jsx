import ResultCard from './ResultCard';

/**
 * ResultsList — Grid or list layout for search results.
 */
export default function ResultsList({
  results,
  loading,
  error,
  currentPage,
  isListView,
  onViewGraph,
  onFindSimilar,
  onOpenProfile,
  onConnect,
  onAddToCompare,
}) {
  if (loading) {
    return (
      <div className={`grid gap-6 ${isListView ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'}`}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-white border border-gray-100 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex justify-between">
              <div className="skeleton h-4 w-12" />
              <div className="skeleton h-4 w-8" />
            </div>
            <div className="skeleton h-5 w-3/4" />
            <div className="skeleton h-4 w-1/2" />
            <div className="skeleton h-12 w-full" />
            <div className="flex gap-2">
              <div className="skeleton h-6 w-16 rounded" />
              <div className="skeleton h-6 w-20 rounded" />
            </div>
            <div className="space-y-2 pt-2">
              <div className="skeleton h-1.5 w-full rounded-full" />
              <div className="skeleton h-1.5 w-full rounded-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white border border-red-100 rounded-xl">
        <svg className="w-12 h-12 text-red-400 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-1">Search Failed</h3>
        <p className="text-sm text-gray-500">{error}</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white border border-gray-100 rounded-xl text-center">
        <svg className="w-12 h-12 text-gray-300 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
          <circle cx="12" cy="12" r="3" />
          <line x1="12" y1="1" x2="12" y2="5" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="7.05" y2="7.05" />
          <line x1="16.95" y1="16.95" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="5" y2="12" />
          <line x1="19" y1="12" x2="23" y2="12" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No results found</h3>
        <p className="text-sm text-gray-500">Try adjusting your search query or removing some filters.</p>
      </div>
    );
  }

  return (
    <div className={`grid gap-6 ${isListView ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'}`}>
      {results.map((result, index) => (
        <ResultCard
          key={result.id}
          result={result}
          index={index}
          currentPage={currentPage}
          onViewGraph={onViewGraph}
          onFindSimilar={onFindSimilar}
          onOpenProfile={onOpenProfile}
          onConnect={onConnect}
          onAddToCompare={onAddToCompare}
        />
      ))}
    </div>
  );
}
