# Graph Report - C:\Users\kumar\Downloads\Semantic_Search-ACM\semantic_search  (2026-04-18)

## Corpus Check
- Corpus is ~46,418 words - fits in a single context window. You may not need a graph.

## Summary
- 434 nodes · 890 edges · 59 communities detected
- Extraction: 55% EXTRACTED · 45% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.57)
- Token cost: 1,500 input · 500 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Frontend State & UI Logic|Frontend State & UI Logic]]
- [[_COMMUNITY_Backend API & Service Initializers|Backend API & Service Initializers]]
- [[_COMMUNITY_Backend Core Models & Classes|Backend Core Models & Classes]]
- [[_COMMUNITY_Search Engines & Graph Algorithms|Search Engines & Graph Algorithms]]
- [[_COMMUNITY_Conversational Engine & Trie Autocomplete|Conversational Engine & Trie Autocomplete]]
- [[_COMMUNITY_Persistence & Cache Management|Persistence & Cache Management]]
- [[_COMMUNITY_Frontend API Client & Data Mapping|Frontend API Client & Data Mapping]]
- [[_COMMUNITY_React Components & Hooks|React Components & Hooks]]
- [[_COMMUNITY_Pydantic Data Models|Pydantic Data Models]]
- [[_COMMUNITY_Synthetic Data Generation|Synthetic Data Generation]]
- [[_COMMUNITY_Bookmark Management|Bookmark Management]]
- [[_COMMUNITY_Search Bar & Debouncing|Search Bar & Debouncing]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_How-It-Works Visuals|How-It-Works Visuals]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Graph Visualization Canvas|Graph Visualization Canvas]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]

## God Nodes (most connected - your core abstractions)
1. `AlumniGraph` - 45 edges
2. `EmbeddingsManager` - 39 edges
3. `EntityExtractor` - 34 edges
4. `CrossEncoderReranker` - 33 edges
5. `HybridSearchEngine` - 28 edges
6. `ConversationalSearchEngine` - 26 edges
7. `LRUCache` - 25 edges
8. `AutocompleteTrie` - 25 edges
9. `startup_logic()` - 22 edges
10. `SearchRequest` - 21 edges

## Surprising Connections (you probably didn't know these)
- `search()` --calls--> `make_search_key()`  [INFERRED]
  backend\main.py → backend\cache_manager.py
- `startup_logic()` --calls--> `ConversationalSearchEngine`  [INFERRED]
  backend\main.py → backend\conversational.py
- `startup_logic()` --calls--> `EmbeddingsManager`  [INFERRED]
  backend\main.py → backend\embeddings.py
- `startup_logic()` --calls--> `CrossEncoderReranker`  [INFERRED]
  backend\main.py → backend\embeddings.py
- `startup_logic()` --calls--> `EntityExtractor`  [INFERRED]
  backend\main.py → backend\entity_extractor.py

## Communities

### Community 0 - "Frontend State & UI Logic"
Cohesion: 0.06
Nodes (49): addConvBubble(), addToHistory(), animateCounters(), apiCall(), applyStructuredFilters(), changePage(), clearStructuredFilters(), closeBookmarksPanel() (+41 more)

### Community 1 - "Backend API & Service Initializers"
Cohesion: 0.04
Nodes (45): _CacheEntry, make_search_key(), In-Memory LRU Cache with TTL — no Redis required for single-worker deployments., Store a value under key with optional TTL., _generate_profile_text(), get_unique_values(), load_alumni_data(), Data Loader — CSV ingestion, normalization, and profile text generation. (+37 more)

### Community 2 - "Backend Core Models & Classes"
Cohesion: 0.19
Nodes (55): BaseModel, LRUCache, Thread-safe LRU cache with per-entry TTL eviction.      Parameters     ---------, ConversationalSearchEngine, Thin wrapper around resolve_turn().      Kept as a class so callers using the, Turn, CrossEncoderReranker, EmbeddingsManager (+47 more)

### Community 3 - "Search Engines & Graph Algorithms"
Cohesion: 0.06
Nodes (23): Return cached value or None on miss/expiry., Get the embedding vector for a specific alumni by their string ID., Rerank a list of candidate profile dicts by cross-encoder score.          Para, Generate a human-readable explanation for why a result was returned., Extract entities from a natural language query.                  Args:, Add direct weighted edges between alumni nodes.          Edge weight formula (PR, Compute global (non-personalized) PageRank for baseline scoring., Compute Personalized PageRank seeded by query-matching nodes (PRD §3.8). (+15 more)

### Community 4 - "Conversational Engine & Trie Autocomplete"
Cohesion: 0.1
Nodes (17): _clean_topic_shift(), ConversationalResult, _extract_slots_from_query(), _is_follow_up(), _is_reset(), Conversational Multi-Turn Search Engine — rule-based stub.  Key design: STATEL, If query is a topic shift like 'what about managers', strip the prefix so FAISS, Heuristic: is this query a narrowing follow-up vs a fresh search?      A query (+9 more)

### Community 5 - "Persistence & Cache Management"
Cohesion: 0.08
Nodes (16): _check_and_invalidate_faiss_cache(), _faiss_config_hash(), Embeddings Manager — Sentence-BERT encoding, FAISS HNSW indexing, and Cross-Enc, Embed all profile texts and build a FAISS HNSW index.          Parameters, Save embeddings, index, ID map, and version sentinel to disk., Attempt to load pre-built embeddings and index from disk.         Auto-invalida, Embed a query and retrieve nearest neighbours from the HNSW index.          Re, Search by a pre-computed vector (for entity similarity search).          Retur (+8 more)

### Community 6 - "Frontend API Client & Data Mapping"
Cohesion: 0.22
Nodes (14): apiCall(), conversationalSearch(), findPath(), getAlumniGraph(), getAlumniList(), getAlumniProfile(), getAutocomplete(), getExportUrl() (+6 more)

### Community 7 - "React Components & Hooks"
Cohesion: 0.12
Nodes (6): AppContent(), ConversationalPanel(), HomePage(), NetworkPage(), useToast(), useStats()

### Community 8 - "Pydantic Data Models"
Cohesion: 0.13
Nodes (14): AlumniProfile, Config, ConversationTurn, ExplainInfo, GraphEdge, GraphNode, Pydantic models for API request/response schemas. Updated for PRD v2: pagination, Node for vis.js graph visualization. (+6 more)

### Community 9 - "Synthetic Data Generation"
Cohesion: 0.19
Nodes (13): generate_alumni(), generate_bio(), generate_career_path(), generate_email(), generate_phone(), Synthetic Alumni Data Generator Generates 500 realistic alumni records with div, Generate a plausible Indian mobile number (10 digits, starts with 6-9)., Derive a realistic work email from name and company. (+5 more)

### Community 10 - "Bookmark Management"
Cohesion: 0.6
Nodes (3): getBookmarks(), isBookmarked(), toggleBookmark()

### Community 11 - "Search Bar & Debouncing"
Cohesion: 0.5
Nodes (2): SearchBar(), useDebounce()

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (1): Batch year range — conversational end-to-end test against live server. Covers: s

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (1): Multi-turn conversation integration test. Simulates exactly what the frontend do

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): Central configuration for the Semantic Search on Alumni Graph system. Updated fo

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Run — Single entry point to start the Semantic Search on Alumni Graph system.

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Flush the entire cache.

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Remove a single key from the cache.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): No-op — state is now client-side.

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Load the Sentence-BERT model.

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): Entity Extractor — Extracts known entities (skills, companies, batches, etc.) f

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Return Node2Vec cosine similarity scores for candidates relative to a query node

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Return up to top_k suggestion dicts matching the given prefix.          Args:

### Community 23 - "How-It-Works Visuals"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Graph Visualization Canvas"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): Load graph from disk.

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (1): System Architecture

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): Hybrid Scoring Formula

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (1): Key Features

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): Conversational Stub

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): FAISS HNSW Upgrade

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): Node2Vec Integration

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): SQLite FTS5 Migration

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Query Intent Classifier

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Apostrophe Escape Fix

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Phone & Email Extension

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (1): Hero Image

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): React Logo

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Vite Logo

## Knowledge Gaps
- **105 isolated node(s):** `Central configuration for the Semantic Search on Alumni Graph system. Updated fo`, `Run — Single entry point to start the Semantic Search on Alumni Graph system.`, `In-Memory LRU Cache with TTL — no Redis required for single-worker deployments.`, `Thread-safe LRU cache with per-entry TTL eviction.      Parameters     ---------`, `Return cached value or None on miss/expiry.` (+100 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (2 nodes): `config.py`, `Central configuration for the Semantic Search on Alumni Graph system. Updated fo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (2 nodes): `run.py`, `Run — Single entry point to start the Semantic Search on Alumni Graph system.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (2 nodes): `.clear()`, `Flush the entire cache.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `.invalidate()`, `Remove a single key from the cache.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (2 nodes): `.reset()`, `No-op — state is now client-side.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `.load_model()`, `Load the Sentence-BERT model.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `entity_extractor.py`, `Entity Extractor — Extracts known entities (skills, companies, batches, etc.) f`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `.get_node2vec_similarity()`, `Return Node2Vec cosine similarity scores for candidates relative to a query node`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `.search()`, `Return up to top_k suggestion dicts matching the given prefix.          Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `How-It-Works Visuals`** (2 nodes): `HowItWorks.jsx`, `HowItWorks()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `Footer()`, `Footer.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `Header.jsx`, `Header()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Graph Visualization Canvas`** (2 nodes): `GraphCanvas.jsx`, `GraphCanvas()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `PathFinder.jsx`, `PathFinder()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `SimilarPanel.jsx`, `SimilarPanel()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `ActiveFilterChips()`, `ActiveFilterChips.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `FilterSidebar()`, `FilterSidebar.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `Pagination.jsx`, `Pagination()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `ResultsList.jsx`, `ResultsList()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `CommandPalette()`, `CommandPalette.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `CompareModal()`, `CompareModal.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (2 nodes): `CompareTray()`, `CompareTray.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `ConnectModal()`, `ConnectModal.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `ProfileModal.jsx`, `ProfileModal()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `check()`, `conv_unit_test.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `check()`, `multiturn_bug_test.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `check()`, `smoke_test.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `Load graph from disk.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `eslint.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `main.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `System Architecture`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `Hybrid Scoring Formula`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `Key Features`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Conversational Stub`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `FAISS HNSW Upgrade`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `Node2Vec Integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `SQLite FTS5 Migration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Query Intent Classifier`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Apostrophe Escape Fix`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Phone & Email Extension`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `Hero Image`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `React Logo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Vite Logo`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AlumniGraph` connect `Backend Core Models & Classes` to `Backend API & Service Initializers`, `Community 21`, `Search Engines & Graph Algorithms`, `Persistence & Cache Management`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `LRUCache` connect `Backend Core Models & Classes` to `Community 16`, `Backend API & Service Initializers`, `Search Engines & Graph Algorithms`, `Community 17`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `startup_logic()` connect `Backend API & Service Initializers` to `Backend Core Models & Classes`, `Search Engines & Graph Algorithms`, `Persistence & Cache Management`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `AlumniGraph` (e.g. with `FastAPI Backend — Main application with REST endpoints for alumni semantic searc` and `Initialize all components on server startup.`) actually correct?**
  _`AlumniGraph` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `EmbeddingsManager` (e.g. with `FastAPI Backend — Main application with REST endpoints for alumni semantic searc` and `Initialize all components on server startup.`) actually correct?**
  _`EmbeddingsManager` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `EntityExtractor` (e.g. with `FastAPI Backend — Main application with REST endpoints for alumni semantic searc` and `Initialize all components on server startup.`) actually correct?**
  _`EntityExtractor` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `CrossEncoderReranker` (e.g. with `FastAPI Backend — Main application with REST endpoints for alumni semantic searc` and `Initialize all components on server startup.`) actually correct?**
  _`CrossEncoderReranker` has 28 INFERRED edges - model-reasoned connections that need verification._