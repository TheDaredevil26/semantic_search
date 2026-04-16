/**
 * Pagination — Robust pagination controls for large datasets.
 */
export default function Pagination({ currentPage, totalPages, totalCount, onPageChange }) {
  if (totalPages <= 1) return null;

  // Generate page numbers with ellipsis
  function getPageNumbers() {
    const delta = 2; // how many pages to show beside current
    const range = [];
    const rangeWithDots = [];
    let l;

    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= currentPage - delta && i <= currentPage + delta)) {
        range.push(i);
      }
    }

    range.forEach(i => {
      if (l) {
        if (i - l === 2) {
          rangeWithDots.push(l + 1);
        } else if (i - l !== 1) {
          rangeWithDots.push('...');
        }
      }
      rangeWithDots.push(i);
      l = i;
    });

    return rangeWithDots;
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4 px-2 mt-6 border-t border-gray-100">
      <div className="text-xs text-gray-500">
        Showing <span className="font-medium text-gray-900">{(currentPage - 1) * 20 + 1}</span> to{' '}
        <span className="font-medium text-gray-900">{Math.min(currentPage * 20, totalCount)}</span> of{' '}
        <span className="font-medium text-gray-900">{totalCount}</span> results
      </div>

      <nav className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Previous
        </button>

        <div className="hidden sm:flex items-center gap-1 mx-2">
          {getPageNumbers().map((page, idx) => {
            if (page === '...') {
              return <span key={`dots-${idx}`} className="px-2 text-gray-400 text-xs">...</span>;
            }
            return (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-medium transition-colors ${
                  currentPage === page
                    ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                    : 'text-gray-600 hover:bg-gray-50 border border-transparent'
                }`}
              >
                {page}
              </button>
            );
          })}
        </div>
        <div className="sm:hidden text-xs text-gray-600 font-medium px-4">
          Page {currentPage} of {totalPages}
        </div>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Next
          <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </nav>
    </div>
  );
}
