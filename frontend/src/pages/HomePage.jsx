import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import { useStats } from '../hooks/useStats';

/**
 * HomePage — Landing page with hero search and stats dashboard.
 */
export default function HomePage() {
  const navigate = useNavigate();
  const { stats, loading } = useStats();

  function handleSearch(query) {
    if (!query) return;
    navigate(`/search?q=${encodeURIComponent(query)}`);
  }

  return (
    <div className="flex flex-col min-h-[calc(100vh-140px)]">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center py-20 px-4 animate-fade-in relative overflow-hidden">
        {/* Subtle background decoration */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-50/50 rounded-full blur-3xl -z-10 pointer-events-none" />

        <div className="text-center max-w-3xl w-full mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white border border-gray-100 rounded-full shadow-sm mb-2 opacity-80">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-dot" />
            <span className="text-[10px] font-medium text-gray-500 tracking-wider uppercase">System Online</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 tracking-tight leading-tight">
            Discover the network <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
              semantically.
            </span>
          </h1>

          <p className="text-base text-gray-500 max-w-xl mx-auto leading-relaxed">
            Query the alumni database using natural language. Our hybrid AI engine combines Sentence-BERT with Graph Centrality to find the perfect connections.
          </p>

          <div className="max-w-2xl mx-auto mt-8 relative z-10">
            <SearchBar
              value=""
              onChange={() => {}}
              onSearch={handleSearch}
              placeholder="e.g., 'Software engineers in London who shifted to PM'"
              showQuickQueries={true}
              size="large"
            />
          </div>
        </div>
      </section>

      {/* Stats Dashboard */}
      <section className="py-12 px-4 border-t border-gray-100 bg-white z-10 relative">
        <div className="max-w-7xl mx-auto">
          <h3 className="text-sm font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <svg className="w-4 h-4 text-indigo-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <path d="M3 9h18" />
              <path d="M9 21V9" />
            </svg>
            Dataset Overview
          </h3>

          {loading || !stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-gray-50 rounded-xl p-5 border border-gray-100 h-24 skeleton" />
              ))}
            </div>
          ) : (
            <div className="space-y-8 animate-slide-up">
              {/* Counters */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Total Alumni" value={stats.total_alumni} />
                <StatCard label="Companies" value={stats.total_companies} />
                <StatCard label="Unique Skills" value={stats.total_skills} />
                <StatCard label="Global Hubs" value={stats.total_cities} />
              </div>

              {/* Bar Charts Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <DashboardList title="Top Skills" items={stats.top_skills} color="bg-indigo-500" />
                <DashboardList title="Top Companies" items={stats.top_companies} color="bg-emerald-500" />
                <DashboardList title="Locations" items={stats.top_locations} color="bg-blue-500" />
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
      <div className="text-[11px] font-medium text-gray-400 uppercase tracking-wider mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900 animate-count-up">
        {value ? value.toLocaleString() : 0}
      </div>
    </div>
  );
}

function DashboardList({ title, items, color }) {
  if (!items || items.length === 0) return null;
  const max = Math.max(...items.map(i => i.count));

  return (
    <div className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
      <h4 className="text-xs font-semibold text-gray-900 mb-4">{title}</h4>
      <div className="space-y-3">
        {items.slice(0, 5).map((item, i) => (
          <div key={i} className="flex items-center gap-3 text-xs">
            <div className="w-24 truncate text-gray-600" title={item.name}>{item.name}</div>
            <div className="flex-1 h-1.5 bg-gray-50 rounded-full overflow-hidden">
              <div
                className={`h-full ${color} rounded-full transition-all duration-1000 ease-out`}
                style={{ width: `${(item.count / max) * 100}%` }}
              />
            </div>
            <div className="w-8 text-right text-gray-400 font-mono">{item.count}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
