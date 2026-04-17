import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import SearchBar from '../components/search/SearchBar';
import FilterSidebar from '../components/search/FilterSidebar';
import ActiveFilterChips from '../components/search/ActiveFilterChips';
import ConversationalPanel from '../components/search/ConversationalPanel';
import ResultsList from '../components/search/ResultsList';
import Pagination from '../components/search/Pagination';
import ScoreBreakdown from '../components/shared/ScoreBreakdown';
import { useSearch } from '../hooks/useSearch';
import { useFilters } from '../hooks/useFilters';

export default function SearchPage({ onOpenProfile, onViewGraph, onFindSimilar, onConnect, onAddToCompare }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialQuery = searchParams.get('q') || '';

  const {
    filterOptions,
    activeFilters,
    hasActiveFilters,
    updateFilter,
    setAllFilters,
    clearFilters,
    removeFilter,
    getFilterPayload
  } = useFilters();

  const {
    query,
    setQuery,
    results,
    setResults,
    loading,
    error,
    currentPage,
    totalPages,
    totalCount,
    latencyMs,
    intent,
    searchQuery,
    performSearch,
    clearResults,
    injectSearchData,
  } = useSearch();

  const [isListView, setIsListView] = useState(false);
  const skipAutoSearchRef = useRef(false);

  // Sync URL query to local state
  useEffect(() => {
    if (initialQuery !== query) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  // Trigger search when query or filters change
  useEffect(() => {
    if (initialQuery) {
      if (skipAutoSearchRef.current) {
        skipAutoSearchRef.current = false;
        return;
      }
      performSearch({
        query: initialQuery,
        page: 1,
        graphWeight: activeFilters.graphWeight,
        filters: getFilterPayload()
      });
    }
  }, [initialQuery, activeFilters.graphWeight]); // Don't trigger auto-search on other filters until 'Apply' is clicked

  function handleSearch(newQuery) {
    navigate(`/search?q=${encodeURIComponent(newQuery)}`);
  }

  function handleApplyFilters() {
    performSearch({
      query: initialQuery,
      page: 1,
      graphWeight: activeFilters.graphWeight,
      filters: getFilterPayload()
    });
  }

  function handleClearFilters() {
    clearFilters();
    performSearch({
      query: initialQuery,
      page: 1,
      graphWeight: 0.4,
      filters: {}
    });
  }

  function handlePageChange(newPage) {
    performSearch({
      query: initialQuery,
      page: newPage,
      graphWeight: activeFilters.graphWeight,
      filters: getFilterPayload()
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleConversationalResponse(data) {
    // Atomically replace all active filter state from the resolved backend response
    // so old filters don't bleed into the new conversational context.
    const resolvedFilters = data.applied_filters || {};
    setAllFilters({
      batchFilter: [],
      deptFilter: [],
      company: resolvedFilters.company || '',
      location: resolvedFilters.location || '',
      batchYear: resolvedFilters.batch_year || '',
      skills: resolvedFilters.skills || [],
      graphWeight: activeFilters.graphWeight,
    });

    const resolvedQuery = data.resolved_query || initialQuery;
    
    // Changing the URL will trigger the useEffect, but we already have the
    // perfect conversational results. Flag the ref to skip the redundant fetch.
    if (resolvedQuery !== initialQuery) {
      skipAutoSearchRef.current = true;
    }
    navigate(`/search?q=${encodeURIComponent(resolvedQuery)}`, { replace: true });

    // Inject the total state
    if (data) {
      injectSearchData(data);
    }
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 pb-20 animate-fade-in">
      {/* Top Search Area */}
      <div className="mb-6 flex gap-4 items-center">
        <div className="flex-1">
          <SearchBar value={query} onChange={setQuery} onSearch={handleSearch} />
        </div>
        <button
          onClick={() => setIsListView(!isListView)}
          className="p-2.5 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 text-gray-500 transition-colors hidden md:block"
          title={isListView ? "Switch to Grid View" : "Switch to List View"}
        >
          {isListView ? (
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          )}
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Sidebar */}
        <div className="w-full lg:w-auto lg:sticky lg:top-20 z-10">
          <FilterSidebar
            filterOptions={filterOptions}
            activeFilters={activeFilters}
            onUpdateFilter={updateFilter}
            onClear={handleClearFilters}
            onApply={handleApplyFilters}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <ConversationalPanel
            initialQuery={initialQuery}
            onSearchResponse={handleConversationalResponse}
            onReset={() => { clearFilters(); clearResults(); }}
          />

          {hasActiveFilters && (
            <ActiveFilterChips filters={activeFilters} onRemove={removeFilter} />
          )}

          {results.length > 0 && !loading && (
            <ScoreBreakdown
              query={searchQuery}
              hasResults={true}
              latencyMs={latencyMs}
              intent={intent}
              graphWeight={activeFilters.graphWeight}
            />
          )}

          <ResultsList
            results={results}
            loading={loading}
            error={error}
            currentPage={currentPage}
            isListView={isListView}
            onViewGraph={onViewGraph}
            onFindSimilar={onFindSimilar}
            onOpenProfile={onOpenProfile}
            onConnect={onConnect}
            onAddToCompare={onAddToCompare}
          />

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalCount={totalCount}
            onPageChange={handlePageChange}
          />
        </div>
      </div>
    </div>
  );
}
