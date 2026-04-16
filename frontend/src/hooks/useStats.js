import { useState, useEffect } from 'react';
import { getStats } from '../api/client';

/**
 * Hook to fetch and cache dashboard statistics.
 */
export function useStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  async function fetchStats() {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.warn('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  }

  return { stats, loading };
}
