import { useState, useEffect } from 'react';

/**
 * BookmarksPanel — Slide-in panel listing bookmarked alumni.
 * Persists to localStorage.
 */
export default function BookmarksPanel({ isOpen, onClose, onOpenProfile }) {
  const [bookmarks, setBookmarks] = useState([]);

  useEffect(() => {
    setBookmarks(JSON.parse(localStorage.getItem('bookmarks') || '[]'));
  }, [isOpen]);

  function removeBookmark(id) {
    const updated = bookmarks.filter(b => b.id !== id);
    localStorage.setItem('bookmarks', JSON.stringify(updated));
    setBookmarks(updated);
  }

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/10 z-40 animate-fade-in" onClick={onClose} />

      {/* Panel */}
      <div className="fixed top-0 right-0 h-full w-80 bg-white shadow-xl z-50 flex flex-col animate-slide-in-right border-l border-gray-100">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <svg className="w-4.5 h-4.5 text-amber-500" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            <h3 className="font-semibold text-gray-900">Bookmarks</h3>
            {bookmarks.length > 0 && (
              <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                {bookmarks.length}
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-3">
          {bookmarks.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <svg className="w-12 h-12 mb-3 opacity-30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              <p className="text-sm text-center">No bookmarks yet.<br />Star alumni from search results.</p>
            </div>
          ) : (
            <div className="space-y-1">
              {bookmarks.map(b => (
                <div
                  key={b.id}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors group"
                  onClick={() => onOpenProfile?.(b.id)}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-800 truncate">{b.name}</div>
                    <div className="text-xs text-gray-400">ID: {b.id}</div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeBookmark(b.id); }}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 text-gray-400 transition-all"
                    title="Remove"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/**
 * Utility functions for bookmark management.
 */
export function getBookmarks() {
  return JSON.parse(localStorage.getItem('bookmarks') || '[]');
}

export function isBookmarked(id) {
  return getBookmarks().some(b => b.id === id);
}

export function toggleBookmark(id, name) {
  const bookmarks = getBookmarks();
  const idx = bookmarks.findIndex(b => b.id === id);
  if (idx >= 0) {
    bookmarks.splice(idx, 1);
  } else {
    bookmarks.push({ id, name });
  }
  localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
  return idx < 0; // returns true if added, false if removed
}
