# Alumni Search — Final Implementation Plan

> **Version:** 2.2 (Complete)
> **Base PRD:** Alumni Network Search System v2.0
> **Status:** Ready for Execution

---

## Pre-Flight Q&A (Answered)

### Q1 — Conversational LLM Search (§3.14, P1)
> *Do you have an OpenAI API key, or should I implement a rule-based version?*

**Recommendation: Implement a rule-based / stub version first.**

- Build `ConversationalSearchEngine` with a clean interface: `handle_turn(query, history) → SearchRequest`
- Use rule-based multi-turn logic to handle follow-ups like "show me more from Google" or "filter to 2020 batch" by diffing the previous `SearchRequest`
- Add an `LLM_BACKEND` config flag (`none` | `openai` | `local`) that defaults to `none`
- When `LLM_BACKEND=openai`, swap in a thin GPT-4o-mini adapter; when `local`, point to llama.cpp via `llama-cpp-python`
- This gives you a working demo without an API key, and a single-line config change to enable the full LLM version

**No API key needed to proceed. The stub will be portfolio-ready on its own.**

---

### Q2 — SQLite Migration (§3.10, P2)
> *Should I do it now, or finish P0/P1 first?*

**Recommendation: Keep pandas for P0/P1, migrate SQLite as a separate P2 step.**

Rationale:
- The SQLite migration touches the data layer that every other feature depends on — doing it mid-sprint risks blocking P0 fixes
- All P1 features (cross-encoder, HNSW, weighted graph) are independent of the storage layer and can be built and tested against pandas today
- Once P0/P1 are green, SQLite becomes a clean isolated swap: `DataLoader → SQLiteDataLayer`, nothing else changes
- Design the `DataLoader` abstraction now (interface only) so SQLite slots in without refactoring callers

**Proceed with pandas. SQLite is step 12 in the execution table (see below).**

---

### Q3 — FAISS HNSW Rebuild
> *The HNSW upgrade requires deleting `cache/faiss.index` on first run.*

**Confirmed — this is expected and safe.**

- Add a version sentinel file: `cache/faiss.version` containing a hash of the index config
- On startup, if `faiss.version` doesn't match current config → auto-delete stale index and rebuild
- This means you never have to manually delete the cache file again after any future config change
- First-run re-encoding time: ~30–90s depending on dataset size; log a clear `[FAISS] Building HNSW index (first run)…` message so it doesn't look like a hang

---

## Improvements Over Original Plan

The following gaps were identified in the original implementation plan and are addressed here:

| # | Gap | Fix Added |
|---|-----|-----------|
| 1 | `ConversationalSearch` had no fallback path | Rule-based stub + LLM_BACKEND config flag |
| 2 | FAISS rebuild required manual file deletion | Auto-versioned cache with sentinel file |
| 3 | No `DataLoader` abstraction before SQLite | Interface-first design specified |
| 4 | `Node2Vec` listed without startup-cost warning | Added lazy/background build note |
| 5 | `/api/cache/stats` not wired to frontend | Added to metrics dashboard spec |
| 6 | Cross-encoder score not exposed in API response | `explain` field explicitly required in `SearchResult` |
| 7 | No test stubs listed for P0 fixes | Acceptance tests added inline per section |
| 8 | No note on cold-start latency from model loading | Startup sequence and lazy-load strategy added |
| 9 | §3.15 Smart Search Suggestions treated as part of autocomplete with no dedicated spec | Promoted to its own section with full implementation spec |
| 10 | `/api/search/filters` had no response schema or acceptance test | Schema and test added to §3.6 |
| 11 | MRR@10 benchmark mentioned but not in verification checklist | Added to automated tests checklist |
| 12 | `models.py` Pydantic changes not spelled out — risk of contract drift | Full model diff added to §3.2 / §3.6 |
| 13 | No degraded-mode flag when Node2Vec is still building | `embeddings_ready` status field added to `/api/metrics` |
| 14 | In-process LRU won't be shared across multiple workers | Caveat + Redis upgrade path noted in §3.12 |

---

## Full Implementation Plan

### Phase 1 — Bug Fixes & Critical Foundations *(Week 1)*

**Goal:** Zero crashes. The system must demo cleanly before any new features land.

---

#### 3.1 Fix `/api/path` Type Mismatch · P0 · 0.5h

**File:** `backend/main.py`

- Graph stores nodes as `alumni_{id}` strings; endpoint receives raw integers
- Add explicit coercion: `node_key = f"alumni_{int(node_id)}"`
- Return HTTP 400 with `{"error": "invalid node id", "detail": "..."}` on bad input
- **Tests:**
  - `GET /api/path?id1=5&id2=10` → 200
  - `GET /api/path?id1=abc&id2=10` → 400

---

#### 3.2 Implement Pagination · P0 · 2h

**Files:** `backend/main.py`, `backend/models.py`, `frontend/app.js`, `frontend/index.html`

- `GET /api/search?q=...&page=1&limit=20` (max limit: 100)
- Response envelope:
  ```json
  { "results": [...], "total_count": 143, "page": 1, "limit": 20, "total_pages": 8 }
  ```
- Apply pagination **after** all ranking/reranking is complete
- Frontend: Previous / Next buttons, "Showing 1–20 of 143 results" label
- Preserve query + filter state across page navigation
- **Pydantic changes in `backend/models.py`:**
  ```python
  class SearchRequest(BaseModel):
      q: str
      page: int = 1
      limit: int = Field(default=20, le=100)
      company_filter: str | None = None
      location_filter: str | None = None
      batch_year_filter: str | None = None   # "2019" or "2015-2020"
      skills_filter: list[str] = []

  class ExplainInfo(BaseModel):
      semantic_score: float
      graph_score: float
      cross_encoder_score: float | None
      matched_keywords: list[str]

  class SearchResult(BaseModel):
      id: int
      name: str
      company: str
      college: str
      batch_year: int
      location: str
      skills: list[str]
      explain: ExplainInfo

  class SearchResponse(BaseModel):
      results: list[SearchResult]
      total_count: int
      page: int
      limit: int
      total_pages: int
  ```
- **Tests:** page=1 of 100-result query → 20 items; page=5 → items 81–100

---

#### 3.3 Fix Autocomplete Performance · P0 · 1.5h

**Files:** `backend/trie.py` *(new)*, `backend/main.py`

- Replace O(n) row-by-row loop with a prefix Trie built once at startup
- Index: name tokens, company tokens, skill tokens, location tokens
- Endpoint: `GET /api/autocomplete?q=<prefix>` → O(k) lookup where k = prefix length
- Return suggestions with category label: `{ "text": "Google", "category": "company" }`
- **Acceptance:** p99 latency < 20ms on 100k-row dataset

---

#### 3.6 Structured Filters · P1 · 3h *(partially in Phase 1)*

**Files:** `backend/main.py`, `backend/models.py`, `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`

- New `/api/search` filter params: `company`, `batch_year` (int or `2015-2020` range), `location`, `skills` (list, AND logic)
- New endpoint: `GET /api/search/filters` → distinct values for all filterable fields
  ```json
  {
    "companies": ["Google", "Microsoft", "Amazon", ...],
    "locations": ["Bangalore", "Mumbai", ...],
    "batch_years": [2015, 2016, ..., 2024],
    "skills": ["Python", "ML", "React", ...]
  }
  ```
- Apply filters **before** SBERT embedding to shrink the candidate pool
- Frontend: collapsible filter panel, dropdowns populated from `/api/search/filters`
- Active filter chips above results; each chip has ✕ to remove
- **Acceptance:** `?company=Google` returns only Google employees
- **Acceptance:** `GET /api/search/filters` returns non-empty lists for all four fields

---

### Phase 2 — Search Quality Upgrade *(Week 2)*

**Goal:** Multi-stage retrieval pipeline replacing basic cosine similarity.

---

#### 3.4 Cross-Encoder Reranking · P1 · 2h

**Files:** `backend/embeddings.py`, `backend/search_engine.py`

- Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~100MB, downloaded once from HuggingFace)
- Load at startup via `CrossEncoderReranker` class; expose `rerank(query: str, candidates: list[Profile]) → list[ScoredProfile]`
- Pipeline: FAISS retrieves top-50 → cross-encoder rescores all 50 → return top-K
- Input format: `(query_text, name + company + skills + bio)`
- Expose score in `SearchResult.explain.cross_encoder_score`
- Benchmark and document MRR@10 before/after — **save results to `docs/benchmarks/mrr_crossencoder.md`** as a portfolio artefact
- **Acceptance:** Relevant results appear in top-3 more often than baseline
- **Acceptance:** MRR@10 improvement is documented with a before/after table

---

#### 3.5 Query Intent Classification · P2 · 2h

**File:** `backend/search_engine.py`

- Three intent classes: `STRUCTURED` | `SEMANTIC` | `GRAPH`
- Detection rules (fast path, no model needed):
  - `STRUCTURED`: query contains `company:`, `batch:`, `location:`, `skills:` tokens
  - `GRAPH`: query contains relationship keywords ("connected to", "path between", "colleagues of")
  - `SEMANTIC`: everything else
- Optional upgrade: zero-shot classifier via HuggingFace `facebook/bart-large-mnli`
- Routing:
  - `STRUCTURED` → skip SBERT, apply DB filters only
  - `SEMANTIC` → full SBERT + cross-encoder pipeline
  - `GRAPH` → emphasize graph score, minimize semantic weight
- Log intent class per query
- **Acceptance:** Rule-based classifier > 85% accuracy on a 50-query test set

---

### Phase 3 — Graph Intelligence Upgrade *(Week 3)*

**Goal:** Turn the graph from a visual ornament into a real ranking engine.

---

#### 3.7 Weighted Graph Edges · P1 · 2h

**File:** `backend/graph_builder.py`

- Edge weight formula during `build_from_dataframe`:
  - `same_company → weight += 3.0`
  - `same_college → weight += 2.0`
  - `shared_skill (per skill) → weight += 1.0`
- Pass `weight=edge_weight` on all `G.add_edge(...)` calls
- Switch to weighted degree centrality for base graph score
- **Acceptance:** Two nodes sharing company + college + 3 skills → edge weight = 8.0

---

#### 3.8 Personalized PageRank · P1 · 1.5h

**File:** `backend/graph_builder.py`

- Replace `nx.pagerank(G)` with `nx.pagerank(G, personalization=seed_dict)`
- Seed logic: nodes whose name/company/skills contain query tokens → `seed=0.8`, others → `seed=0.2`
- Normalize seed dict so values sum to 1.0 before passing
- Re-run per query (PPR is fast on graphs < 50k nodes)
- **Acceptance:** Query "machine learning" boosts ML-connected nodes measurably

---

#### 3.9 Node2Vec Graph Embeddings · P2 · 2h

**File:** `backend/graph_builder.py`

- `pip install node2vec`
- Run Node2Vec at startup: 128-dim embeddings, `walk_length=30`, `num_walks=200`, `workers=4`
- **Important:** Run in a background thread; don't block server startup. Fall back to PPR-only until embeddings are ready
- Set `app.state.node2vec_ready = False` on startup; flip to `True` when background thread completes
- Expose `node2vec_ready` in `GET /api/metrics` so the frontend can show a "Graph intelligence: building…" indicator
- Store node embeddings in a secondary FAISS `IndexHNSWFlat`
- For `GRAPH`-intent queries: retrieve nearest nodes in graph embedding space
- Final score blend: `0.40 × semantic + 0.35 × ppr + 0.25 × node2vec`
- **Acceptance:** Graph-based similar profiles are meaningfully different from text-based results

---

### Phase 4 — Backend Infrastructure *(Week 4)*

**Goal:** Scalable storage, optimized FAISS, caching, observability.

---

#### 3.11 Upgrade FAISS to HNSW · P1 · 1h

**File:** `backend/embeddings.py`

- Replace `IndexFlatIP` with `IndexHNSWFlat(dim, M=32)` wrapped in `IndexIDMap2`
- Config: `efConstruction=200` at build time, `efSearch=100` at query time
- **Auto-versioned cache:** write `cache/faiss.version` = hash of `(M, efConstruction, efSearch, model_name)` on index save; on startup, if hash mismatch → delete stale index and rebuild automatically
- Persist with `faiss.write_index`; reload with `faiss.read_index`
- Log `[FAISS] Building HNSW index…` clearly during first run
- **Acceptance:** ANN query < 10ms for 100k vectors; recall@10 > 0.95 vs. brute force

---

#### 3.10 SQLite + FTS5 Storage · P2 · 3h *(after all P1 items are green)*

**Files:** `backend/db.py` *(new)*, `backend/main.py`

- **Design the `DataLoader` interface now** (abstract base class with `get_all()`, `filter(...)`, `get_by_id(...)`) so SQLite is a drop-in replacement
- Schema:
  ```sql
  CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    name TEXT, company TEXT, college TEXT,
    batch_year INTEGER, location TEXT,
    skills TEXT,           -- JSON array as text
    bio TEXT, influence_score REAL,
    embedding BLOB         -- serialized numpy array
  );
  CREATE VIRTUAL TABLE profiles_fts USING fts5(name, company, bio, skills);
  ```
- Indexes: `(company)`, `(batch_year)`, `(location)`
- FTS5 virtual table for full-text search fallback
- **Acceptance:** System loads and queries 200k-row dataset without memory errors

---

#### 3.12 In-Memory LRU Cache · P2 · 1.5h *(no Redis required)*

**File:** `backend/cache_manager.py` *(new)*

> Redis is a great P3 upgrade but adds operational complexity. An in-process LRU cache handles the common case (warm queries) with zero infrastructure.
> **Multi-worker note:** If you run Uvicorn with `--workers N > 1`, each worker has its own LRU and they won't share state. For single-worker dev/demo this is fine. Upgrade to Redis (P3) before any multi-process deployment.

- Use `functools.lru_cache` or a custom TTL-aware LRU (`maxsize=1000`)
- Cache keys:
  - `search:{sha256(query + filters + page)}` → result list, TTL=300s
  - `embedding:{sha256(text)}` → numpy array, TTL=3600s
  - `graph_score:{sha256(query)}` → score dict, TTL=300s
- Track: `hits`, `misses`, `evictions`
- Expose via `GET /api/cache/stats` and surface on metrics dashboard
- **Acceptance:** Second identical query completes in < 5ms

---

#### 3.13 Structured Logging & Observability · P2 · 1h

**File:** `backend/logger.py` *(new)*

- Use `loguru` (simpler) or `structlog` (more powerful) for JSON-structured logs
- Log fields per request:
  ```json
  { "ts": "...", "endpoint": "/api/search", "query": "...", "intent": "SEMANTIC",
    "latency_ms": 42, "result_count": 20, "cache_hit": false }
  ```
- Expose `GET /api/metrics` returning aggregate stats: avg latency, p95 latency, cache hit rate, total queries, `node2vec_ready: bool`, `embeddings_ready: bool`

---

#### 3.14 Conversational Multi-Turn Search · P1 · 3h

**File:** `backend/conversational.py` *(new)*

- `ConversationalSearchEngine.handle_turn(query: str, history: list[Turn]) → SearchRequest`
- Rule-based multi-turn resolution (no API key needed):
  - "more like him" → copy previous result's profile fields into new query
  - "filter to Google" → add `company_filter=Google` to previous `SearchRequest`
  - "from 2020 batch" → add `batch_year=2020` to previous request
  - Bare follow-up (no entity change) → append to previous query text
- Config flag in `config.py`: `LLM_BACKEND: Literal["none", "openai", "local"] = "none"`
  - `openai`: thin adapter calling GPT-4o-mini to parse intent and extract slots
  - `local`: `llama-cpp-python` pointing to a quantized model path
- Frontend: chat-style search box with turn history panel

---

### Phase 5 — Frontend UX Overhaul *(Week 5)*

**Goal:** Transform the UI from type-search-click to a rich interactive experience.

---

#### Frontend Changes Summary

| File | Changes |
|------|---------|
| `frontend/index.html` | Filter panel, explainability panel, pagination controls, chat search box |
| `frontend/app.js` | Filter state management, pagination logic, filter chip removal, graph click handlers, explainability toggle, multi-turn history |
| `frontend/styles.css` | Filter panel, chips, explainability panel, pagination, chat UI |

---

#### 3.15 Smart Search Suggestions · P1 · 1h

**Files:** `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`

- Dropdown renders suggestions returned by `GET /api/autocomplete?q=<prefix>`
- Each suggestion shows a category badge: `Google  [company]`, `Batch 2019  [batch]`
- Keyboard navigation: `↑` / `↓` to move, `Enter` to select, `Esc` to dismiss
- Debounce: fire request 100ms after last keystroke (cancel previous in-flight request)
- Highlight the matched prefix characters in bold within each suggestion
- Selecting a suggestion populates the search box **and immediately submits the search**
- **Acceptance:** Suggestions appear within 150ms of typing; keyboard nav works end-to-end

#### 3.16 Explainability Panel · P2

- Expandable "Why This Result?" section on each result card
- Shows: Semantic score, Graph score, Cross-encoder score, Matched keywords
- Data sourced from `SearchResult.explain` field (already populated by backend)

#### 3.17 Interactive Graph Visualization · P2

- Click a graph node → trigger new search for that profile
- Hover → tooltip with name, company, connection count
- Cluster nodes by company or college (colour-coded)
- Edge thickness proportional to edge weight

---

## Priority Execution Order

| # | Feature | Priority | Est. Effort | Depends On |
|---|---------|----------|-------------|------------|
| 1 | Fix `/api/path` type mismatch | P0 | 0.5h | — |
| 2 | Pagination + Pydantic model updates | P0 | 2h | — |
| 3 | Trie-based autocomplete (backend) | P0 | 1.5h | — |
| 4 | Structured filters + `/api/search/filters` endpoint | P1 | 3h | #2 |
| 5 | Cross-encoder reranking + MRR@10 benchmark | P1 | 2.5h | — |
| 6 | Weighted graph edges | P1 | 2h | — |
| 7 | Personalized PageRank | P1 | 1.5h | #6 |
| 8 | FAISS HNSW upgrade + auto-versioned cache | P1 | 1h | — |
| 9 | Conversational search (rule-based stub) | P1 | 3h | #4 |
| 10 | Smart Search Suggestions UI (§3.15) | P1 | 1h | #3 |
| 11 | Explainability panel | P2 | 2h | #5 |
| 12 | In-memory LRU cache + `/api/metrics` | P2 | 1.5h | — |
| 13 | Structured logging | P2 | 1h | — |
| 14 | SQLite migration | P2 | 3h | All P1 done |
| 15 | Interactive graph visualization | P2 | 2h | #6 |
| 16 | Query intent classification | P2 | 2h | #5 |
| 17 | Node2Vec embeddings (background thread) | P2 | 2h | #6, #8 |

**Total P0+P1 estimate:** ~17h
**Total P2 estimate:** ~13.5h

---

## Startup Sequence (After All Changes)

```
1. Load config (config.py)
2. Initialize logger (logger.py)
3. Load data: pandas → DataLoader interface
4. Build Trie index (trie.py) — fast, in-memory
5. Load SBERT model (embeddings.py)
6. Load Cross-Encoder model (embeddings.py)
7. Build/load FAISS HNSW index (auto-versioned)
8. Build weighted graph + run global PageRank (graph_builder.py)
9. [Background thread] Node2Vec embeddings (if enabled)
10. Start FastAPI server
```

Cold start time estimate: ~15–30s (dominated by model loading + FAISS if rebuilding).

---

## Verification Checklist

### Automated Tests

- [ ] `GET /api/path?id1=5&id2=10` → 200
- [ ] `GET /api/path?id1=abc&id2=10` → 400
- [ ] Pagination: `total_pages = ceil(total_count / limit)`
- [ ] `?company=Google` returns only Google employees
- [ ] `GET /api/search/filters` returns non-empty lists for companies, locations, batch_years, skills
- [ ] MRR@10 before/after cross-encoder documented in `docs/benchmarks/mrr_crossencoder.md`
- [ ] FAISS HNSW loads correctly from `cache/faiss.index`
- [ ] Auto-versioned cache rebuilds when config changes
- [ ] Cache hit on second identical query
- [ ] `GET /api/metrics` includes `node2vec_ready` and `embeddings_ready` fields

### Manual Checks

- [ ] Filter panel renders and dropdowns populate
- [ ] Filter chips appear and are removable
- [ ] Autocomplete suggestions appear with category badges and prefix highlighting
- [ ] Keyboard navigation (↑↓ Enter Esc) works in autocomplete dropdown
- [ ] Click a graph node → triggers new search
- [ ] Expand "Why This Result?" panel on a result card
- [ ] Multi-turn: follow-up "more from Google" refines previous results
- [ ] `/api/metrics` shows latency, cache stats, and `node2vec_ready` status
- [ ] Frontend shows "Graph intelligence: building…" indicator while Node2Vec is warming up

---

## P3 Stretch Goals (Not in Scope)

| Feature | PRD Section | Est. Effort |
|---------|-------------|-------------|
| 3D force-graph with temporal playback | §3.18 | 3 days |
| Recommendation engine (similar profiles) | §3.19 | 3 days |
| Career path insights & analytics | §3.20 | 4 days |
| PDF export + graph snapshots | §3.21 | 2 days |
| User accounts + persistent bookmarks | §3.23 | 3 days |
| Community detection / graph analytics | §3.24 | 3 days |
| Redis caching (upgrade from LRU) | §3.12 | 1.5 days |
| Responsive mobile UI | §3.22 | 1.5 days |
