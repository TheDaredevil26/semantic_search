/**
 * Alumni Graph Search — Frontend Application (Enhanced)
 * Features: search, result cards, graph visualization, profile modal,
 * dashboard charts, search history, entity badges, bio snippets
 */

const API_BASE = '';

// --- State ---
let currentResults = [];
let graphNetwork = null;
let isGraphOpen = false;
let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
let statsData = null;
let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
let isBookmarksPanelOpen = false;
let isListView = false;
let currentTheme = localStorage.getItem('theme') || 'dark';

// --- DOM Elements ---
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const batchFilter = document.getElementById('batch-filter');
const deptFilter = document.getElementById('dept-filter');
const graphWeight = document.getElementById('graph-weight');
const graphWeightValue = document.getElementById('graph-weight-value');
const resultsSection = document.getElementById('results-section');
const resultsGrid = document.getElementById('results-grid');
const resultsTitle = document.getElementById('results-title');
const resultsLatency = document.getElementById('results-latency');
const resultsEntities = document.getElementById('results-entities');
const emptyState = document.getElementById('empty-state');
const graphPanel = document.getElementById('graph-panel');
const graphPanelTitle = document.getElementById('graph-panel-title');
const graphContainer = document.getElementById('graph-container');
const closeGraphBtn = document.getElementById('close-graph');
const overlay = document.getElementById('overlay');
const headerStats = document.getElementById('header-stats');
const statsDashboard = document.getElementById('stats-dashboard');
const profileModal = document.getElementById('profile-modal');
const modalBody = document.getElementById('modal-body');
const closeModalBtn = document.getElementById('close-modal');
const searchHistoryEl = document.getElementById('search-history');
const historyItems = document.getElementById('history-items');
const autocompleteDropdown = document.getElementById('autocomplete-dropdown');
const exportBtn = document.getElementById('export-btn');
const bookmarksToggle = document.getElementById('bookmarks-toggle');
const bookmarkCountEl = document.getElementById('bookmark-count');
const bookmarksPanel = document.getElementById('bookmarks-panel');
const bookmarksList = document.getElementById('bookmarks-list');
const closeBookmarksBtn = document.getElementById('close-bookmarks');
const themeToggle = document.getElementById('theme-toggle');
const toggleViewBtn = document.getElementById('toggle-view');

let autocompleteTimer = null;
let activeAcIndex = -1;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    loadFilters();
    loadStats();
    setupEventListeners();
    renderSearchHistory();
    applyTheme(currentTheme);
    updateBookmarkBadge();
    createScrollTopButton();
});

function setupEventListeners() {
    // Search
    searchButton.addEventListener('click', () => { hideAutocomplete(); performSearch(); });
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');
            if (activeAcIndex >= 0 && items[activeAcIndex]) {
                items[activeAcIndex].click();
            } else {
                hideAutocomplete();
                performSearch();
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateAutocomplete(1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateAutocomplete(-1);
        }
    });

    // Autocomplete on input
    searchInput.addEventListener('input', () => {
        clearTimeout(autocompleteTimer);
        autocompleteTimer = setTimeout(() => fetchAutocomplete(searchInput.value), 250);
    });

    // Hide autocomplete on blur (delay for click)
    searchInput.addEventListener('blur', () => {
        setTimeout(hideAutocomplete, 200);
    });

    // Quick queries
    document.querySelectorAll('.quick-query').forEach(btn => {
        btn.addEventListener('click', () => {
            searchInput.value = btn.dataset.query;
            hideAutocomplete();
            performSearch();
        });
    });

    // Graph weight slider
    graphWeight.addEventListener('input', () => {
        graphWeightValue.textContent = (graphWeight.value / 100).toFixed(2);
    });

    // Filter selection → render chips
    batchFilter.addEventListener('change', () => renderFilterChips(batchFilter, 'batch-chips'));
    deptFilter.addEventListener('change', () => renderFilterChips(deptFilter, 'dept-chips'));

    // Close graph
    closeGraphBtn.addEventListener('click', closeGraph);
    overlay.addEventListener('click', () => {
        if (isBookmarksPanelOpen) closeBookmarksPanel();
        if (isGraphOpen) closeGraph();
        if (profileModal.style.display !== 'none') closeProfileModal();
    });

    // Close modal
    closeModalBtn.addEventListener('click', closeProfileModal);

    // Export CSV
    exportBtn.addEventListener('click', exportCSV);

    // Bookmarks panel
    bookmarksToggle.addEventListener('click', toggleBookmarksPanel);
    closeBookmarksBtn.addEventListener('click', closeBookmarksPanel);

    // Theme toggle
    themeToggle.addEventListener('click', () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(currentTheme);
        localStorage.setItem('theme', currentTheme);
    });

    // View toggle (grid/list)
    if (toggleViewBtn) {
        toggleViewBtn.addEventListener('click', toggleResultsView);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!autocompleteDropdown.classList.contains('hidden')) {
                hideAutocomplete();
            } else if (isBookmarksPanelOpen) {
                closeBookmarksPanel();
            } else if (profileModal.style.display !== 'none') {
                closeProfileModal();
            } else if (isGraphOpen) {
                closeGraph();
            }
        }
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
        // Ctrl+B for bookmarks
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            toggleBookmarksPanel();
        }
    });
}

// --- Autocomplete ---

async function fetchAutocomplete(query) {
    if (query.length < 2) {
        hideAutocomplete();
        return;
    }
    try {
        const data = await apiCall(`/api/autocomplete?q=${encodeURIComponent(query)}`);
        if (data.suggestions && data.suggestions.length > 0) {
            renderAutocomplete(data.suggestions);
        } else {
            hideAutocomplete();
        }
    } catch {
        hideAutocomplete();
    }
}

function renderAutocomplete(suggestions) {
    activeAcIndex = -1;
    autocompleteDropdown.innerHTML = suggestions.map((s, i) => `
        <button class="autocomplete-item" data-index="${i}" onmousedown="selectAutocomplete('${escapeHtml(s.text)}')">
            <span class="ac-icon">${s.icon}</span>
            <span class="ac-text">${escapeHtml(s.text)}</span>
            <span class="ac-type">${s.type}</span>
        </button>
    `).join('');
    autocompleteDropdown.classList.remove('hidden');
}

function navigateAutocomplete(dir) {
    const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');
    if (items.length === 0) return;
    items.forEach(i => i.classList.remove('active'));
    activeAcIndex = Math.max(-1, Math.min(items.length - 1, activeAcIndex + dir));
    if (activeAcIndex >= 0) {
        items[activeAcIndex].classList.add('active');
        items[activeAcIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        searchInput.value = items[activeAcIndex].querySelector('.ac-text').textContent;
    }
}

function selectAutocomplete(text) {
    searchInput.value = text;
    hideAutocomplete();
    performSearch();
}

function hideAutocomplete() {
    autocompleteDropdown.classList.add('hidden');
    activeAcIndex = -1;
}

// --- CSV Export ---

function exportCSV() {
    const query = searchInput.value.trim();
    if (!query) {
        showToast('Enter a search query first', 'error');
        return;
    }
    const gw = parseFloat(graphWeight.value) / 100;
    const url = `/api/export?query=${encodeURIComponent(query)}&top_k=20&graph_weight=${gw}`;
    window.open(url, '_blank');
    showToast('Downloading CSV...', 'success');
}

// --- API Calls ---

async function apiCall(endpoint, options = {}) {
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

// --- Search ---

async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    // Show loading state
    setSearchLoading(true);
    resultsSection.classList.remove('hidden');
    emptyState.classList.add('hidden');
    showLoadingSkeletons();

    try {
        // Build filters
        const selectedBatches = Array.from(batchFilter.selectedOptions).map(o => parseInt(o.value));
        const selectedDepts = Array.from(deptFilter.selectedOptions).map(o => o.value);
        const gw = parseFloat(graphWeight.value) / 100;

        const body = {
            query: query,
            top_k: 10,
            graph_weight: gw,
        };
        if (selectedBatches.length > 0) body.batch_filter = selectedBatches;
        if (selectedDepts.length > 0) body.dept_filter = selectedDepts;

        const data = await apiCall('/api/search', {
            method: 'POST',
            body: JSON.stringify(body),
        });

        currentResults = data.results;
        renderResults(data);
        addToHistory(query);

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    } catch (error) {
        showError('Search failed: ' + error.message);
    } finally {
        setSearchLoading(false);
    }
}

function setSearchLoading(loading) {
    const btnText = searchButton.querySelector('.btn-text');
    const btnLoader = searchButton.querySelector('.btn-loader');
    if (loading) {
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        searchButton.disabled = true;
    } else {
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        searchButton.disabled = false;
    }
}

// --- Search History ---

function addToHistory(query) {
    searchHistory = searchHistory.filter(q => q !== query);
    searchHistory.unshift(query);
    if (searchHistory.length > 8) searchHistory = searchHistory.slice(0, 8);
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    renderSearchHistory();
}

function renderSearchHistory() {
    if (searchHistory.length === 0) {
        searchHistoryEl.classList.add('hidden');
        return;
    }
    searchHistoryEl.classList.remove('hidden');
    historyItems.innerHTML = searchHistory.map(q =>
        `<button class="history-chip" onclick="replaySearch('${escapeHtml(q)}')" title="${escapeHtml(q)}">${escapeHtml(q)}</button>`
    ).join('');
}

function replaySearch(query) {
    searchInput.value = query;
    performSearch();
}

// --- Render Results ---

function renderResults(data) {
    resultsTitle.textContent = `${data.total} results for "${data.query}"`;
    resultsLatency.textContent = `${data.latency_ms}ms`;

    if (data.results.length === 0) {
        resultsGrid.innerHTML = `
            <div class="result-card" style="grid-column: 1 / -1; text-align: center; padding: 48px;">
                <p style="color: var(--text-secondary); font-size: 1rem;">No results found. Try a different query or adjust your filters.</p>
            </div>
        `;
        return;
    }

    resultsGrid.innerHTML = data.results.map((result, index) => createResultCard(result, index)).join('');

    // Animate score bars
    requestAnimationFrame(() => {
        document.querySelectorAll('.score-bar-fill').forEach(bar => {
            bar.style.width = bar.dataset.width;
        });
    });
}

function createResultCard(result, index) {
    const profile = result.profile;
    const skills = profile.skills || [];
    const delay = index * 0.05;
    const explanation = result.explanation.toLowerCase();
    const bio = profile.bio || '';
    const truncatedBio = bio.length > 100 ? bio.substring(0, 100) + '...' : bio;

    return `
        <div class="result-card" style="animation-delay: ${delay}s" data-id="${result.id}">
            <div class="card-header">
                <span class="card-rank">#${index + 1}</span>
                <div style="display:flex;align-items:center;gap:8px">
                    <button class="bookmark-btn ${isBookmarked(result.id) ? 'bookmarked' : ''}" data-id="${result.id}" onclick="toggleBookmark('${result.id}', '${escapeHtml(profile.full_name)}')" title="Bookmark">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                    </button>
                    <span class="card-score">${(result.score * 100).toFixed(1)}%</span>
                </div>
            </div>

            <h4 class="card-name" onclick="openProfile('${result.id}')">${escapeHtml(profile.full_name)}</h4>
            <p class="card-role">${escapeHtml(profile.current_role)} at ${escapeHtml(profile.current_company)}</p>
            ${truncatedBio ? `<p class="card-bio">${escapeHtml(truncatedBio)}</p>` : ''}

            <div class="card-meta">
                <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    Batch ${profile.batch_year}
                </span>
                <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 4 3 6 3s6-1 6-3v-5"/></svg>
                    ${escapeHtml(profile.department)}
                </span>
                <span class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    ${escapeHtml(profile.city)}
                </span>
            </div>

            <div class="card-skills">
                ${skills.slice(0, 6).map(skill => {
                    const isMatched = explanation.includes(skill.toLowerCase());
                    return `<span class="skill-chip ${isMatched ? 'matched' : ''}">${escapeHtml(skill)}</span>`;
                }).join('')}
                ${skills.length > 6 ? `<span class="skill-chip">+${skills.length - 6}</span>` : ''}
            </div>

            <div class="score-bars">
                <div class="score-bar">
                    <span class="score-bar-label">Vector</span>
                    <div class="score-bar-track">
                        <div class="score-bar-fill vector" data-width="${(result.vector_score * 100).toFixed(0)}%" style="width: 0%"></div>
                    </div>
                    <span class="score-bar-value">${(result.vector_score * 100).toFixed(0)}%</span>
                </div>
                <div class="score-bar">
                    <span class="score-bar-label">Graph</span>
                    <div class="score-bar-track">
                        <div class="score-bar-fill graph" data-width="${(result.graph_score * 100).toFixed(0)}%" style="width: 0%"></div>
                    </div>
                    <span class="score-bar-value">${(result.graph_score * 100).toFixed(0)}%</span>
                </div>
            </div>

            <div class="card-explanation">
                <div class="explanation-label">Why this result?</div>
                <p>${escapeHtml(result.explanation)}</p>
            </div>

            <div class="card-actions">
                <button class="action-btn primary" onclick="viewGraph('${result.id}', '${escapeHtml(profile.full_name)}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/></svg>
                    View Graph
                </button>
                <button class="action-btn secondary" onclick="findSimilar('${result.id}', '${escapeHtml(profile.full_name)}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/><path d="M3 21v-2a4 4 0 013-3.87"/></svg>
                    Find Similar
                </button>
                <button class="connect-btn"
                    data-id="${result.id}"
                    data-name="${escapeHtml(profile.full_name)}"
                    data-phone="${escapeHtml(profile.phone || '')}"
                    data-email="${escapeHtml(profile.email || '')}"
                    data-role="${escapeHtml(profile.current_role)} at ${escapeHtml(profile.current_company)}"
                    onclick="openConnectModal(this)"
                    title="Connect with ${escapeHtml(profile.full_name)}">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
                    </svg>
                    Connect
                </button>
            </div>
        </div>
    `;
}

// --- Profile Modal ---

async function openProfile(alumniId) {
    try {
        const profile = await apiCall(`/api/alumni/${alumniId}`);
        renderProfileModal(profile);
        profileModal.style.display = 'flex';
        overlay.style.display = 'block';
        requestAnimationFrame(() => {
            profileModal.classList.add('visible');
            overlay.classList.add('visible');
        });
    } catch (error) {
        showToast('Failed to load profile', 'error');
    }
}

function renderProfileModal(profile) {
    const initials = profile.full_name.split(' ').map(n => n[0]).join('').substring(0, 2);
    const skills = profile.skills || [];

    modalBody.innerHTML = `
        <div class="modal-header-section">
            <div class="modal-avatar">${initials}</div>
            <h2 class="modal-name">${escapeHtml(profile.full_name)}</h2>
            <p class="modal-role">${escapeHtml(profile.current_role)} at ${escapeHtml(profile.current_company)}</p>
            <div class="modal-meta-row">
                <span class="modal-meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    Batch ${profile.batch_year}
                </span>
                <span class="modal-meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 4 3 6 3s6-1 6-3v-5"/></svg>
                    ${escapeHtml(profile.department)}
                </span>
                <span class="modal-meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    ${escapeHtml(profile.city)}
                </span>
            </div>
        </div>

        <div class="modal-divider"></div>

        <div class="modal-section-title">About</div>
        <p class="modal-bio">${escapeHtml(profile.bio)}</p>

        <div class="modal-section-title">Skills</div>
        <div class="modal-skills">
            ${skills.map(skill => `<span class="skill-chip">${escapeHtml(skill)}</span>`).join('')}
        </div>

        <div class="modal-divider"></div>
        <div class="modal-section-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
            </svg>
            Contact
        </div>
        <div class="modal-contact-row">
            <a class="modal-contact-chip phone-chip" href="tel:${escapeHtml(profile.phone || '')}" title="Call">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
                </svg>
                ${escapeHtml(profile.phone || 'Not available')}
            </a>
            <a class="modal-contact-chip email-chip" href="mailto:${escapeHtml(profile.email || '')}" title="Email">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6c0-1.1.9-2 2-2z"/>
                    <polyline points="22,6 12,13 2,6"/>
                </svg>
                ${escapeHtml(profile.email || 'Not available')}
            </a>
        </div>

        ${profile.mentor_id ? `
            <div class="modal-section-title">Mentor</div>
            <p class="modal-bio" style="margin-bottom: var(--space-lg);">${escapeHtml(profile.mentor_id)}</p>
        ` : ''}

        <div class="modal-actions">
            <button class="action-btn primary" onclick="closeProfileModal(); viewGraph('${profile.alumnus_id}', '${escapeHtml(profile.full_name)}')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/></svg>
                View Network Graph
            </button>
            <button class="action-btn secondary" onclick="closeProfileModal(); findSimilar('${profile.alumnus_id}', '${escapeHtml(profile.full_name)}')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/><path d="M3 21v-2a4 4 0 013-3.87"/></svg>
                Find Similar Alumni
            </button>
        </div>
    `;
}

function closeProfileModal() {
    profileModal.classList.remove('visible');
    overlay.classList.remove('visible');
    setTimeout(() => {
        profileModal.style.display = 'none';
        overlay.style.display = 'none';
    }, 300);
}

// --- Graph Visualization ---

async function viewGraph(alumniId, name) {
    graphPanelTitle.textContent = `Network: ${name}`;
    openGraph();

    // Show loading in graph container
    graphContainer.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)"><p>Loading graph...</p></div>';

    try {
        const data = await apiCall(`/api/alumni/${alumniId}/graph`);
        // Wait for panel transition to complete before rendering vis.js
        setTimeout(() => {
            renderGraphVisualization(data);
        }, 500);
    } catch (error) {
        graphContainer.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color: var(--accent-rose)"><p>Failed to load graph: ${error.message}</p></div>`;
    }
}

function renderGraphVisualization(data) {
    // Prepare vis.js data
    const nodes = new vis.DataSet(data.nodes.map(node => ({
        ...node,
        font: node.font || {
            color: '#e8e8f0',
            size: node.group === 'alumni' ? 13 : 11,
            face: 'Inter, sans-serif',
        },
        shape: node.group === 'alumni' ? 'dot' : (node.group === 'company' ? 'diamond' : 'dot'),
        borderWidth: node.id === data.center_id ? 4 : 2,
        shadow: node.id === data.center_id ? { enabled: true, size: 20, color: 'rgba(99,102,241,0.4)' } : false,
    })));

    const edges = new vis.DataSet(data.edges.map(edge => ({
        ...edge,
        smooth: { type: 'continuous' },
        width: 1.5,
    })));

    const options = {
        nodes: {
            shape: 'dot',
            font: {
                color: '#e8e8f0',
                size: 12,
                face: 'Inter, sans-serif',
            },
        },
        edges: {
            color: { color: '#475569', opacity: 0.6 },
            font: { size: 9, color: '#94a3b8', strokeWidth: 0, face: 'Inter, sans-serif' },
            smooth: { type: 'continuous' },
        },
        physics: {
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -40,
                centralGravity: 0.005,
                springLength: 120,
                springConstant: 0.04,
                damping: 0.4,
            },
            stabilization: { iterations: 150 },
        },
        interaction: {
            hover: true,
            tooltipDelay: 150,
            hideEdgesOnDrag: true,
            hideEdgesOnZoom: true,
        },
        layout: {
            improvedLayout: true,
        },
    };

    // Destroy previous network
    if (graphNetwork) {
        graphNetwork.destroy();
    }

    graphNetwork = new vis.Network(graphContainer, { nodes, edges }, options);

    // Focus on center node after stabilization
    graphNetwork.once('stabilizationIterationsDone', () => {
        graphNetwork.focus(data.center_id, {
            scale: 0.8,
            animation: { duration: 500, easingFunction: 'easeInOutQuad' },
        });
    });

    // Click on node → search by that entity
    graphNetwork.on('doubleClick', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const nodeData = nodes.get(nodeId);
            if (nodeData && nodeData.group === 'alumni') {
                closeGraph();
                viewGraph(nodeData.label.replace('alumni_', ''), nodeData.label);
            } else if (nodeData) {
                closeGraph();
                searchInput.value = nodeData.label;
                performSearch();
            }
        }
    });
}

function openGraph() {
    isGraphOpen = true;
    graphPanel.style.display = 'flex';
    overlay.style.display = 'block';
    // Force layout recalc before transition
    graphPanel.offsetHeight;
    requestAnimationFrame(() => {
        graphPanel.classList.add('visible');
        overlay.classList.add('visible');
    });
}

function closeGraph() {
    isGraphOpen = false;
    graphPanel.classList.remove('visible');
    overlay.classList.remove('visible');
    setTimeout(() => {
        graphPanel.style.display = 'none';
        overlay.style.display = 'none';
        if (graphNetwork) {
            graphNetwork.destroy();
            graphNetwork = null;
        }
    }, 400);
}

// --- Find Similar ---

async function findSimilar(alumniId, name) {
    searchInput.value = `Alumni similar to ${name}`;
    setSearchLoading(true);
    resultsSection.classList.remove('hidden');
    emptyState.classList.add('hidden');
    showLoadingSkeletons();

    try {
        const data = await apiCall(`/api/similar/${alumniId}?top_k=10`);
        currentResults = data.results;
        renderResults(data);
        addToHistory(`Alumni similar to ${name}`);
    } catch (error) {
        showError('Similarity search failed: ' + error.message);
    } finally {
        setSearchLoading(false);
    }
}

// --- Filters ---

async function loadFilters() {
    try {
        const data = await apiCall('/api/filters');

        // Batch years
        batchFilter.innerHTML = data.batch_years.map(y =>
            `<option value="${y}">${y}</option>`
        ).join('');

        // Departments
        deptFilter.innerHTML = data.departments.map(d =>
            `<option value="${d}">${d}</option>`
        ).join('');
    } catch (error) {
        console.warn('Failed to load filters:', error);
    }
}

// --- Stats & Dashboard ---

async function loadStats() {
    try {
        const data = await apiCall('/api/stats');
        statsData = data;

        // Header stats
        headerStats.innerHTML = `
            <div class="stat-item">
                <div class="stat-value" data-counter="${data.total_alumni}">0</div>
                <div class="stat-label">Alumni</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" data-counter="${data.total_companies}">0</div>
                <div class="stat-label">Companies</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" data-counter="${data.total_skills}">0</div>
                <div class="stat-label">Skills</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" data-counter="${data.total_locations || 0}">0</div>
                <div class="stat-label">Cities</div>
            </div>
        `;

        // Dashboard stat cards
        statsDashboard.innerHTML = `
            <div class="stat-card">
                <div class="stat-number" data-counter="${data.total_alumni}">0</div>
                <div class="stat-title">Alumni Indexed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" data-counter="${data.total_companies}">0</div>
                <div class="stat-title">Companies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" data-counter="${data.total_skills}">0</div>
                <div class="stat-title">Unique Skills</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" data-counter="${data.departments.length}">0</div>
                <div class="stat-title">Departments</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" data-counter="${data.batch_years.length}">0</div>
                <div class="stat-title">Batch Years</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" data-counter="${data.total_locations || 0}">0</div>
                <div class="stat-title">Cities</div>
            </div>
        `;

        // Animate counters
        animateCounters();

        // Render dashboard charts
        renderDashboardCharts(data);

    } catch (error) {
        console.warn('Failed to load stats:', error);
        statsDashboard.innerHTML = '<p style="color: var(--text-muted); grid-column: 1/-1;">Loading stats...</p>';
    }
}

function animateCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseInt(el.dataset.counter);
        const duration = 1500;
        const start = performance.now();

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(target * eased).toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    });
}

function renderDashboardCharts(data) {
    // Skills chart
    const skillsChart = document.getElementById('skills-chart');
    if (skillsChart && data.top_skills) {
        const maxSkill = Math.max(...data.top_skills.map(s => s.count));
        skillsChart.innerHTML = data.top_skills.slice(0, 8).map(skill => {
            const width = (skill.count / maxSkill * 100).toFixed(0);
            return `
                <div class="bar-row">
                    <span class="bar-label" title="${skill.name}">${skill.name}</span>
                    <div class="bar-track">
                        <div class="bar-fill skills" style="width: 0%" data-width="${width}%">
                            <span>${skill.count}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        // Animate bars
        setTimeout(() => {
            skillsChart.querySelectorAll('.bar-fill').forEach(bar => {
                bar.style.width = bar.dataset.width;
            });
        }, 300);
    }

    // Companies chart
    const companiesChart = document.getElementById('companies-chart');
    if (companiesChart && data.top_companies) {
        const maxComp = Math.max(...data.top_companies.map(c => c.count));
        companiesChart.innerHTML = data.top_companies.slice(0, 8).map(company => {
            const width = (company.count / maxComp * 100).toFixed(0);
            return `
                <div class="bar-row">
                    <span class="bar-label" title="${company.name}">${company.name}</span>
                    <div class="bar-track">
                        <div class="bar-fill companies" style="width: 0%" data-width="${width}%">
                            <span>${company.count}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        setTimeout(() => {
            companiesChart.querySelectorAll('.bar-fill').forEach(bar => {
                bar.style.width = bar.dataset.width;
            });
        }, 500);
    }

    // Department chart
    const deptChart = document.getElementById('dept-chart');
    if (deptChart && data.dept_distribution) {
        const maxDept = Math.max(...data.dept_distribution.map(d => d.count));
        deptChart.innerHTML = data.dept_distribution.map(dept => {
            const width = (dept.count / maxDept * 100).toFixed(0);
            return `
                <div class="bar-row">
                    <span class="bar-label" title="${dept.name}">${dept.name}</span>
                    <div class="bar-track">
                        <div class="bar-fill departments" style="width: 0%" data-width="${width}%">
                            <span>${dept.count}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        setTimeout(() => {
            deptChart.querySelectorAll('.bar-fill').forEach(bar => {
                bar.style.width = bar.dataset.width;
            });
        }, 700);
    }

    // Locations chart
    const locationsChart = document.getElementById('locations-chart');
    if (locationsChart && data.top_locations) {
        const maxLoc = Math.max(...data.top_locations.map(l => l.count));
        locationsChart.innerHTML = data.top_locations.slice(0, 8).map(loc => {
            const width = (loc.count / maxLoc * 100).toFixed(0);
            return `
                <div class="bar-row">
                    <span class="bar-label" title="${loc.name}">${loc.name}</span>
                    <div class="bar-track">
                        <div class="bar-fill locations" style="width: 0%" data-width="${width}%">
                            <span>${loc.count}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        setTimeout(() => {
            locationsChart.querySelectorAll('.bar-fill').forEach(bar => {
                bar.style.width = bar.dataset.width;
            });
        }, 900);
    }
}

// --- Loading Skeletons ---

function showLoadingSkeletons() {
    resultsGrid.innerHTML = Array.from({ length: 4 }, () => `
        <div class="skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line medium"></div>
        </div>
    `).join('');
}

// --- Toast Notifications ---

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        ${type === 'success' ? '✓' : '⚠'} ${escapeHtml(message)}
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- Error Handling ---

function showError(message) {
    resultsGrid.innerHTML = `
        <div class="result-card" style="grid-column: 1 / -1; text-align: center; padding: 48px; border-color: rgba(244, 63, 94, 0.3);">
            <p style="color: var(--accent-rose); font-size: 1rem; margin-bottom: 8px;">⚠ Error</p>
            <p style="color: var(--text-secondary);">${escapeHtml(message)}</p>
        </div>
    `;
}

// --- Utilities ---

function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function renderFilterChips(selectEl, chipsContainerId) {
    const container = document.getElementById(chipsContainerId);
    const selected = Array.from(selectEl.selectedOptions);

    // Toggle has-selection class on the select
    selectEl.classList.toggle('has-selection', selected.length > 0);

    if (selected.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = selected.map(opt => `
        <span class="filter-chip" data-value="${escapeHtml(opt.value)}">
            ${escapeHtml(opt.textContent)}
            <span class="chip-remove" onclick="removeFilterOption('${selectEl.id}', '${escapeHtml(opt.value)}', '${chipsContainerId}')">&times;</span>
        </span>
    `).join('');
}

function removeFilterOption(selectId, value, chipsContainerId) {
    const selectEl = document.getElementById(selectId);
    const option = Array.from(selectEl.options).find(o => o.value === value);
    if (option) option.selected = false;
    renderFilterChips(selectEl, chipsContainerId);
}

// --- Path Finder ---

(function initPathFinder() {
    const pathFrom = document.getElementById('path-from');
    const pathTo = document.getElementById('path-to');
    const pathFromId = document.getElementById('path-from-id');
    const pathToId = document.getElementById('path-to-id');
    const pathFromDropdown = document.getElementById('path-from-dropdown');
    const pathToDropdown = document.getElementById('path-to-dropdown');
    const findPathBtn = document.getElementById('find-path-btn');
    const pathResult = document.getElementById('path-result');

    if (!pathFrom || !pathTo) return;

    let pathTimer = null;

    function setupPathInput(input, hiddenInput, dropdown) {
        input.addEventListener('input', () => {
            clearTimeout(pathTimer);
            pathTimer = setTimeout(async () => {
                const q = input.value.trim();
                if (q.length < 2) { dropdown.classList.add('hidden'); return; }
                try {
                    const data = await apiCall(`/api/alumni-list?q=${encodeURIComponent(q)}`);
                    if (data.alumni.length > 0) {
                        dropdown.innerHTML = data.alumni.map(a => `
                            <button class="path-dropdown-item" onmousedown="selectPathAlumni(this, '${a.id}', '${escapeHtml(a.name)}', '${input.id}')">
                                <span class="pd-name">${escapeHtml(a.name)}</span>
                                <span class="pd-meta">${escapeHtml(a.role)} at ${escapeHtml(a.company)} · Batch ${a.batch}</span>
                            </button>
                        `).join('');
                        dropdown.classList.remove('hidden');
                    } else {
                        dropdown.classList.add('hidden');
                    }
                } catch { dropdown.classList.add('hidden'); }
            }, 250);
        });
        input.addEventListener('blur', () => setTimeout(() => dropdown.classList.add('hidden'), 200));
    }

    setupPathInput(pathFrom, pathFromId, pathFromDropdown);
    setupPathInput(pathTo, pathToId, pathToDropdown);

    findPathBtn.addEventListener('click', async () => {
        const id1 = pathFromId.value;
        const id2 = pathToId.value;
        if (!id1 || !id2) {
            showToast('Select two alumni first', 'error');
            return;
        }
        if (id1 === id2) {
            showToast('Select two different alumni', 'error');
            return;
        }
        findPathBtn.disabled = true;
        findPathBtn.textContent = 'Finding...';
        try {
            const data = await apiCall(`/api/path/${id1}/${id2}`);
            renderPathResult(data);
        } catch (error) {
            pathResult.classList.remove('hidden');
            pathResult.innerHTML = `<p class="path-info" style="color: var(--accent-rose)">Failed to find path: ${error.message}</p>`;
        } finally {
            findPathBtn.disabled = false;
            findPathBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="12" r="3"/><circle cx="19" cy="12" r="3"/><line x1="8" y1="12" x2="16" y2="12"/></svg> Find Path`;
        }
    });

    function renderPathResult(data) {
        pathResult.classList.remove('hidden');
        if (data.length === -1 || !data.path || data.path.length === 0) {
            pathResult.innerHTML = '<p class="path-info">No connection path found between these alumni.</p>';
            return;
        }

        const stepsHtml = data.path.map((name, i) => {
            const isEndpoint = i === 0 || i === data.path.length - 1;
            const cls = isEndpoint ? 'endpoint' : (name.includes('_') ? 'entity' : 'alumni');
            const connector = i < data.path.length - 1 ? '<span class="path-connector">→</span>' : '';
            return `<span class="path-step"><span class="path-node ${cls}">${escapeHtml(name)}</span>${connector}</span>`;
        }).join('');

        pathResult.innerHTML = `
            <p class="path-info"><strong>${data.length}</strong> degree${data.length > 1 ? 's' : ''} of separation</p>
            <div class="path-steps">${stepsHtml}</div>
            <button class="action-btn primary path-view-graph-btn" onclick="viewPathGraph(${JSON.stringify(data).replace(/"/g, '&quot;')})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4"/></svg>
                View Path in Graph
            </button>
        `;
    }
})();

function selectPathAlumni(btn, id, name, inputId) {
    const input = document.getElementById(inputId);
    const hiddenInput = document.getElementById(inputId + '-id');
    input.value = name;
    hiddenInput.value = id;
}

function viewPathGraph(data) {
    const graphPanelTitle = document.getElementById('graph-panel-title');
    graphPanelTitle.textContent = 'Connection Path';
    openGraph();
    setTimeout(() => {
        renderGraphVisualization(data);
    }, 500);
}

// --- Bookmarks ---

function toggleBookmark(alumniId, name) {
    const idx = bookmarks.findIndex(b => b.id === alumniId);
    if (idx >= 0) {
        bookmarks.splice(idx, 1);
        showToast(`Removed ${name} from bookmarks`, 'success');
    } else {
        bookmarks.push({ id: alumniId, name: name });
        showToast(`Bookmarked ${name}`, 'success');
    }
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
    updateBookmarkBadge();
    // Update all bookmark buttons
    document.querySelectorAll(`.bookmark-btn[data-id="${alumniId}"]`).forEach(btn => {
        btn.classList.toggle('bookmarked', isBookmarked(alumniId));
    });
}

function isBookmarked(alumniId) {
    return bookmarks.some(b => b.id === alumniId);
}

// --- Bookmarks Panel ---

function toggleBookmarksPanel() {
    if (isBookmarksPanelOpen) {
        closeBookmarksPanel();
    } else {
        openBookmarksPanel();
    }
}

function openBookmarksPanel() {
    isBookmarksPanelOpen = true;
    renderBookmarksList();
    bookmarksPanel.style.display = 'flex';
    overlay.style.display = 'block';
    bookmarksPanel.offsetHeight; // force reflow
    requestAnimationFrame(() => {
        bookmarksPanel.classList.add('visible');
        overlay.classList.add('visible');
    });
}

function closeBookmarksPanel() {
    isBookmarksPanelOpen = false;
    bookmarksPanel.classList.remove('visible');
    overlay.classList.remove('visible');
    setTimeout(() => {
        bookmarksPanel.style.display = 'none';
        overlay.style.display = 'none';
    }, 400);
}

function renderBookmarksList() {
    if (bookmarks.length === 0) {
        bookmarksList.innerHTML = `
            <div class="bookmarks-empty">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <p>No bookmarks yet.<br>Star alumni from search results to save them here.</p>
            </div>
        `;
        return;
    }

    bookmarksList.innerHTML = bookmarks.map(b => `
        <div class="bookmark-item" onclick="openProfile('${b.id}')">
            <div class="bookmark-item-info">
                <div class="bookmark-item-name">${escapeHtml(b.name)}</div>
                <div class="bookmark-item-meta">ID: ${b.id}</div>
            </div>
            <button class="bookmark-remove-btn" onclick="event.stopPropagation(); removeBookmarkFromPanel('${b.id}')" title="Remove">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
    `).join('');
}

function removeBookmarkFromPanel(alumniId) {
    bookmarks = bookmarks.filter(b => b.id !== alumniId);
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
    updateBookmarkBadge();
    renderBookmarksList();
    // Update any visible bookmark buttons in results
    document.querySelectorAll(`.bookmark-btn[data-id="${alumniId}"]`).forEach(btn => {
        btn.classList.remove('bookmarked');
    });
    showToast('Bookmark removed', 'success');
}

function updateBookmarkBadge() {
    if (bookmarks.length > 0) {
        bookmarkCountEl.textContent = bookmarks.length;
        bookmarkCountEl.classList.remove('hidden');
    } else {
        bookmarkCountEl.classList.add('hidden');
    }
}

// --- Theme Toggle ---

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const darkIcon = document.getElementById('theme-icon-dark');
    const lightIcon = document.getElementById('theme-icon-light');
    if (theme === 'light') {
        darkIcon.classList.add('hidden');
        lightIcon.classList.remove('hidden');
    } else {
        darkIcon.classList.remove('hidden');
        lightIcon.classList.add('hidden');
    }
}

// --- Results View Toggle ---

function toggleResultsView() {
    isListView = !isListView;
    resultsGrid.classList.toggle('list-view', isListView);
    if (toggleViewBtn) {
        toggleViewBtn.classList.toggle('active', isListView);
        toggleViewBtn.title = isListView ? 'Switch to grid view' : 'Switch to list view';
        toggleViewBtn.innerHTML = isListView
            ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>'
            : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    }
}

// --- Scroll to Top ---

function createScrollTopButton() {
    const btn = document.createElement('button');
    btn.className = 'scroll-top-btn';
    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"/></svg>';
    btn.title = 'Scroll to top';
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.body.appendChild(btn);

    window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });
}

// --- Connect Modal ---

const connectModal = document.getElementById('connect-modal');
const closeConnectBtn = document.getElementById('close-connect-modal');

if (closeConnectBtn) {
    closeConnectBtn.addEventListener('click', () => {
        connectModal.style.display = 'none';
        overlay.style.display = 'none';
        overlay.classList.remove('visible');
    });
}

function openConnectModal(btn) {
    const name  = btn.dataset.name;
    const phone = btn.dataset.phone || 'Not available';
    const email = btn.dataset.email || 'Not available';
    const role  = btn.dataset.role || '';

    // Avatar initials
    const initials = name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();
    document.getElementById('connect-avatar').textContent       = initials;
    document.getElementById('connect-name').textContent         = name;
    document.getElementById('connect-role').textContent         = role;
    document.getElementById('connect-phone-display').textContent = phone;
    document.getElementById('connect-email-display').textContent = email;

    const phoneLink = document.getElementById('connect-phone-link');
    const emailLink = document.getElementById('connect-email-link');
    phoneLink.href  = phone !== 'Not available' ? `tel:${phone}` : '#';
    emailLink.href  = email !== 'Not available' ? `mailto:${email}` : '#';

    connectModal.style.display = 'flex';
    overlay.style.display      = 'block';
    requestAnimationFrame(() => {
        overlay.classList.add('visible');
    });
}

// --- How It Works Toggle ---

function toggleHowItWorks() {
    const body    = document.getElementById('hiw-body');
    const toggle  = document.getElementById('hiw-toggle');
    const chevron = toggle.querySelector('.hiw-chevron');
    const isOpen  = body.style.display !== 'none';

    if (isOpen) {
        body.style.display = 'none';
        toggle.setAttribute('aria-expanded', 'false');
        chevron.style.transform = 'rotate(0deg)';
    } else {
        body.style.display = 'block';
        toggle.setAttribute('aria-expanded', 'true');
        chevron.style.transform = 'rotate(180deg)';
        body.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
