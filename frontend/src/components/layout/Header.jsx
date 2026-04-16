import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getMetrics } from '../../api/client';

/**
 * Header — App navigation bar with logo, nav links, stats, and bookmarks toggle.
 */
export default function Header({ stats, onOpenBookmarks }) {
  const location = useLocation();
  const [metricsReady, setMetricsReady] = useState(false);

  // Poll metrics for Graph AI status
  useEffect(() => {
    let mounted = true;
    async function poll() {
      try {
        const data = await getMetrics();
        if (mounted) setMetricsReady(data.node2vec_ready || false);
      } catch { /* ignore */ }
      if (mounted) setTimeout(poll, 15000);
    }
    poll();
    return () => { mounted = false; };
  }, []);

  const navItems = [
    { path: '/', label: 'Home' },
    { path: '/search', label: 'Search' },
    { path: '/network', label: 'Network' },
  ];

  const bookmarkCount = JSON.parse(localStorage.getItem('bookmarks') || '[]').length;

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-semibold text-gray-900 leading-tight">Alumni Graph Search</h1>
              <p className="text-[10px] text-gray-400 leading-tight">Semantic AI × Graph Intelligence</p>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden sm:flex items-center gap-1">
            {navItems.map(item => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* Quick stats */}
            {stats && (
              <div className="hidden md:flex items-center gap-4 text-xs text-gray-400 mr-2">
                <span><strong className="text-gray-600 font-semibold">{stats.total_alumni?.toLocaleString()}</strong> Alumni</span>
                <span><strong className="text-gray-600 font-semibold">{stats.total_companies?.toLocaleString()}</strong> Companies</span>
              </div>
            )}

            {/* Graph AI status */}
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-gray-400" title="Graph AI Status">
              <span className={`w-1.5 h-1.5 rounded-full ${metricsReady ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
              <span>{metricsReady ? 'Ready' : 'Loading…'}</span>
            </div>

            {/* Bookmarks */}
            <button
              onClick={onOpenBookmarks}
              className="relative p-2 rounded-lg hover:bg-gray-50 text-gray-400 hover:text-gray-600 transition-colors"
              title="Bookmarks (Ctrl+B)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {bookmarkCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] flex items-center justify-center font-medium">
                  {bookmarkCount}
                </span>
              )}
            </button>

            {/* Mobile nav */}
            <div className="sm:hidden flex items-center gap-1">
              {navItems.map(item => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                      isActive ? 'bg-indigo-50 text-indigo-700' : 'text-gray-400'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
