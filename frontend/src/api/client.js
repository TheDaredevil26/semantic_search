/**
 * Centralized API client for all backend communication.
 * Wraps fetch with error handling, JSON parsing, and base URL configuration.
 */

const API_BASE = '';

/**
 * Make an API call to the backend.
 * @param {string} endpoint - API endpoint path (e.g., '/api/search')
 * @param {object} options - Fetch options (method, body, etc.)
 * @returns {Promise<object>} Parsed JSON response
 */
export async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

/**
 * POST search request.
 */
export function searchAlumni(body) {
  return apiCall('/api/search', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * POST conversational search request.
 */
export function conversationalSearch(body) {
  return apiCall('/api/search/conversational', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * GET autocomplete suggestions.
 */
export function getAutocomplete(query) {
  return apiCall(`/api/autocomplete?q=${encodeURIComponent(query)}`);
}

/**
 * GET filter options for the search UI.
 */
export function getSearchFilters() {
  return apiCall('/api/search/filters');
}

/**
 * GET dashboard statistics.
 */
export function getStats() {
  return apiCall('/api/stats');
}

/**
 * GET single alumni profile.
 */
export function getAlumniProfile(id) {
  return apiCall(`/api/alumni/${id}`);
}

/**
 * GET alumni graph neighborhood.
 */
export function getAlumniGraph(id) {
  return apiCall(`/api/alumni/${id}/graph`);
}

/**
 * GET similar alumni.
 */
export function getSimilarAlumni(id, topK = 10) {
  return apiCall(`/api/similar/${id}?top_k=${topK}`);
}

/**
 * GET shortest path between two alumni.
 */
export function findPath(id1, id2) {
  return apiCall(`/api/path/${id1}/${id2}`);
}

/**
 * GET alumni list for dropdowns.
 */
export function getAlumniList(query = '') {
  return apiCall(`/api/alumni-list?q=${encodeURIComponent(query)}`);
}

/**
 * GET system metrics.
 */
export function getMetrics() {
  return apiCall('/api/metrics');
}

/**
 * Build export CSV URL.
 */
export function getExportUrl(query, topK = 20, graphWeight = 0.4) {
  return `/api/export?query=${encodeURIComponent(query)}&top_k=${topK}&graph_weight=${graphWeight}`;
}
