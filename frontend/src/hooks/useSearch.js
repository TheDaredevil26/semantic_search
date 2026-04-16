import { useState, useCallback } from 'react';
import { searchAlumni } from '../api/client';

/**
 * Hook to manage search state: query, results, pagination, loading.
 */
export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Response metadata
  const [latencyMs, setLatencyMs] = useState(0);
  const [intent, setIntent] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const performSearch = useCallback(async (searchParams) => {
    const {
      query: q,
      page = 1,
      limit = 20,
      graphWeight = 0.4,
      filters = {},
    } = searchParams;

    if (!q || !q.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const body = {
        query: q.trim(),
        page,
        limit,
        top_k: 50,
        graph_weight: graphWeight,
        ...filters,
      };

      const data = await searchAlumni(body);

      setResults(data.results || []);
      setCurrentPage(data.page || page);
      setTotalPages(data.total_pages || 1);
      setTotalCount(data.total_count || data.total || 0);
      setLatencyMs(data.latency_ms || 0);
      setIntent(data.intent || null);
      setSearchQuery(data.query || q);

      return data;
    } catch (err) {
      setError(err.message);
      setResults([]);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setCurrentPage(1);
    setTotalPages(1);
    setTotalCount(0);
    setError(null);
    setIntent(null);
    setSearchQuery('');
  }, []);

  return {
    query,
    setQuery,
    results,
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
  };
}
