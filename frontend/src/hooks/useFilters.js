import { useState, useEffect } from 'react';
import { getSearchFilters } from '../api/client';

/**
 * Hook to fetch and manage filter options and active filter state.
 */
export function useFilters() {
  const [filterOptions, setFilterOptions] = useState({
    companies: [],
    locations: [],
    batch_years: [],
    departments: [],
    skills: [],
  });
  const [loading, setLoading] = useState(true);

  // Active filter selections
  const [activeFilters, setActiveFilters] = useState({
    batchFilter: [],
    deptFilter: [],
    company: '',
    location: '',
    batchYear: '',
    skills: [],
    graphWeight: 0.4,
  });

  useEffect(() => {
    fetchFilters();
  }, []);

  async function fetchFilters() {
    try {
      const data = await getSearchFilters();
      setFilterOptions({
        companies: data.companies || [],
        locations: data.locations || [],
        batch_years: data.batch_years || [],
        departments: data.departments || [],
        skills: data.skills || [],
      });
    } catch (err) {
      console.warn('Failed to load filters:', err);
    } finally {
      setLoading(false);
    }
  }

  function updateFilter(key, value) {
    setActiveFilters(prev => ({ ...prev, [key]: value }));
  }

  function clearFilters() {
    setActiveFilters({
      batchFilter: [],
      deptFilter: [],
      company: '',
      location: '',
      batchYear: '',
      skills: [],
      graphWeight: activeFilters.graphWeight,
    });
  }

  function removeFilter(key, value) {
    if (key === 'skills') {
      setActiveFilters(prev => ({
        ...prev,
        skills: prev.skills.filter(s => s !== value),
      }));
    } else if (key === 'batchFilter' || key === 'deptFilter') {
      setActiveFilters(prev => ({
        ...prev,
        [key]: prev[key].filter(v => v !== value),
      }));
    } else {
      setActiveFilters(prev => ({ ...prev, [key]: '' }));
    }
  }

  // Build the filter payload for the search API
  function getFilterPayload() {
    const payload = {};
    if (activeFilters.batchFilter.length > 0) payload.batch_filter = activeFilters.batchFilter;
    if (activeFilters.deptFilter.length > 0) payload.dept_filter = activeFilters.deptFilter;
    if (activeFilters.company) payload.company_filter = activeFilters.company;
    if (activeFilters.location) payload.location_filter = activeFilters.location;
    if (activeFilters.batchYear) payload.batch_year_filter = activeFilters.batchYear;
    if (activeFilters.skills.length > 0) payload.skills_filter = activeFilters.skills;
    return payload;
  }

  // Check if any filters are active
  const hasActiveFilters = activeFilters.batchFilter.length > 0 ||
    activeFilters.deptFilter.length > 0 ||
    activeFilters.company !== '' ||
    activeFilters.location !== '' ||
    activeFilters.batchYear !== '' ||
    activeFilters.skills.length > 0;

  return {
    filterOptions,
    activeFilters,
    loading,
    hasActiveFilters,
    updateFilter,
    clearFilters,
    removeFilter,
    getFilterPayload,
  };
}
