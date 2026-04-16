"""
FastAPI Backend — Main application with REST endpoints for alumni semantic search.

PRD v2 additions:
  §3.1  — /api/path type mismatch fix + HTTP 400 validation
  §3.2  — Pagination on /api/search (page, limit, total_count, total_pages)
  §3.3  — Trie-based autocomplete (O(k) vs O(n))
  §3.6  — Structured filters + /api/search/filters endpoint
  §3.4  — Cross-encoder reranking wired into search pipeline
  §3.12 — LRU cache + /api/cache/stats
  §3.13 — Structured logging + /api/metrics
  §3.14 — Conversational multi-turn search (/api/search/conversational)
"""
import math
import time
import os
import sys
import subprocess
import uuid
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from collections import Counter

from config import (
    FRONTEND_DIR, ALUMNI_CSV_PATH, DATA_DIR, LLM_BACKEND,
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
)
from backend.models import (
    SearchRequest, SearchResponse, FilterOptions, StatsResponse, GraphData,
    ConversationalSearchRequest,
)
from backend.data_loader import load_alumni_data, get_unique_values
from backend.graph_builder import AlumniGraph
from backend.embeddings import EmbeddingsManager, CrossEncoderReranker
from backend.entity_extractor import EntityExtractor
from backend.search_engine import HybridSearchEngine
from backend.trie import AutocompleteTrie
from backend.cache_manager import cache, LRUCache
from backend.conversational import ConversationalSearchEngine, Turn
import backend.logger as obs_logger


# ---------------------------------------------------------------------------
# Global State
# ---------------------------------------------------------------------------
search_engine: HybridSearchEngine = None
alumni_graph: AlumniGraph = None
df = None
unique_values = None
autocomplete_trie: AutocompleteTrie = None
conv_engine: ConversationalSearchEngine = None


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def startup_logic():
    """Initialize all components on server startup."""
    global search_engine, alumni_graph, df, unique_values, autocomplete_trie, conv_engine

    print("\n" + "=" * 60)
    print("  SEMANTIC SEARCH ON ALUMNI GRAPH — Starting Up (PRD v2)")
    print("=" * 60)

    start = time.time()

    # 1. Generate data if needed
    if not os.path.exists(ALUMNI_CSV_PATH):
        print("\n[1/7] Generating alumni data…")
        subprocess.run(
            [sys.executable, os.path.join(DATA_DIR, "generate_alumni.py")],
            check=True
        )
    else:
        print("\n[1/7] Alumni data found.")

    # 2. Load and normalize data
    print("\n[2/7] Loading & normalizing alumni data…")
    df = load_alumni_data()
    unique_values = get_unique_values(df)

    # 3. Build Trie index (PRD §3.3)
    print("\n[3/7] Building Trie autocomplete index…")
    autocomplete_trie = AutocompleteTrie()
    autocomplete_trie.build_from_data(df)
    print(f"  Trie built from {len(df)} records.")

    # 4. Build/load graph
    loaded_graph = None
    try:
        loaded_graph = AlumniGraph.load()
    except Exception:
        pass

    if loaded_graph is not None:
        alumni_graph = loaded_graph
        print("\n[4/7] Graph loaded from cache.")
    else:
        print("\n[4/7] Building weighted alumni graph…")
        alumni_graph = AlumniGraph()
        alumni_graph.build_from_dataframe(df)
        alumni_graph.save()

    # 5. Build/load SBERT embeddings + HNSW FAISS index (PRD §3.11)
    print("\n[5/7] Building SBERT embeddings & FAISS HNSW index…")
    embeddings_mgr = EmbeddingsManager()

    if not embeddings_mgr.load_from_cache():
        embeddings_mgr.load_model()
        embeddings_mgr.build_index(
            profile_texts=df["profile_text"].tolist(),
            alumni_ids=df["alumnus_id"].astype(str).tolist()
        )
    else:
        embeddings_mgr.load_model()  # Still need model for query embedding

    obs_logger.set_embeddings_ready(True)

    # 6. Cross-encoder reranker (PRD §3.4)
    print("\n[6/7] Loading cross-encoder reranker…")
    cross_encoder = CrossEncoderReranker()
    try:
        cross_encoder.load_model()
    except Exception as e:
        print(f"  [WARN] Cross-encoder failed to load: {e}. Search will run without reranking.")
        cross_encoder = None

    # 7. Entity extractor + Search engine
    print("\n[7/7] Initializing entity extractor & search engine…")
    extractor = EntityExtractor()
    extractor.load_entities(alumni_graph.get_all_entity_names())

    search_engine = HybridSearchEngine(
        df, embeddings_mgr, alumni_graph, extractor, cross_encoder
    )

    # 8. Conversational engine (PRD §3.14)
    conv_engine = ConversationalSearchEngine(llm_backend=LLM_BACKEND)

    elapsed = round(time.time() - start, 1)
    print(f"\n{'=' * 60}")
    print(f"  READY — {len(df)} alumni indexed in {elapsed}s")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"  Frontend: http://localhost:8000")
    print(f"{'=' * 60}\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_logic()
    yield


# ---------------------------------------------------------------------------
# Application Setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Semantic Search on Alumni Graph",
    description="AI-powered semantic search over alumni networks using SBERT + FAISS HNSW + Graph scoring (PRD v2)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
@app.get("/")
async def serve_frontend():
    """Serve the main HTML page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. API is running at /docs"}


if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ---------------------------------------------------------------------------
# Search Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute a paginated hybrid semantic search query with graph-boosted reranking.

    Returns results for the requested page along with total_count and total_pages
    for pagination controls.
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    request_id = str(uuid.uuid4())

    # Build cache key
    filters = {
        "company": request.company_filter or "",
        "location": request.location_filter or "",
        "batch_year": request.batch_year_filter or "",
        "skills": str(sorted(request.skills_filter)),
        "batch": str(sorted(request.batch_filter or [])),
        "dept": str(sorted(request.dept_filter or [])),
    }
    cache_key = LRUCache.make_search_key(request.query, filters, request.page, request.limit)
    cached = cache.get(cache_key)

    if cached is not None:
        obs_logger.log_request(
            endpoint="/api/search", query=request.query, intent=cached.get("intent"),
            latency_ms=0.5, result_count=len(cached.get("results", [])),
            cache_hit=True, request_id=request_id,
        )
        return cached

    t0 = time.time()
    result = search_engine.search(
        query=request.query,
        page=request.page,
        limit=request.limit,
        top_k=request.top_k,
        company_filter=request.company_filter,
        location_filter=request.location_filter,
        batch_year_filter=request.batch_year_filter,
        skills_filter=request.skills_filter,
        batch_filter=request.batch_filter,
        dept_filter=request.dept_filter,
        graph_weight=request.graph_weight,
    )
    latency = round((time.time() - t0) * 1000, 1)

    # Cache and log
    cache.set(cache_key, result)
    obs_logger.log_request(
        endpoint="/api/search", query=request.query, intent=result.get("intent"),
        latency_ms=latency, result_count=len(result.get("results", [])),
        cache_hit=False, request_id=request_id,
    )
    return result


@app.post("/api/search/conversational")
async def conversational_search(request: ConversationalSearchRequest):
    """
    Multi-turn conversational search (PRD §3.14).

    Stateless: the client sends the full conversation_history on every request.
    The engine replays history to reconstruct accumulated filter state, then
    runs the hybrid search with those filters applied.
    """
    if not search_engine or not conv_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    # Convert Pydantic ConversationTurn → Turn dataclass
    history = [Turn(role=t.role, content=t.content) for t in request.conversation_history]

    # Resolve current query against history (stateless)
    resolved = conv_engine.handle_turn(request.query, history)

    # Run search with resolved query + accumulated filters
    result = search_engine.search(
        query=resolved.resolved_query,
        page=request.page,
        limit=request.limit,
        top_k=50,
        company_filter=resolved.company_filter,
        location_filter=resolved.location_filter,
        batch_year_filter=resolved.batch_year_filter,
        skills_filter=resolved.skills_filter,
    )

    # Ensure pagination fields are present (for frontend renderResults + renderPagination)
    result.setdefault("page", request.page)
    result.setdefault("limit", request.limit)
    result.setdefault("total_count", result.get("total", 0))
    result.setdefault("total_pages", max(1, math.ceil(result.get("total_count", 0) / request.limit)))
    result.setdefault("intent", resolved.intent)

    # Add conversational metadata
    result["resolved_query"] = resolved.resolved_query
    result["applied_filters"] = {
        "company": resolved.company_filter,
        "location": resolved.location_filter,
        "batch_year": resolved.batch_year_filter,
        "skills": resolved.skills_filter,
    }
    return result


# ---------------------------------------------------------------------------
# Filter Options (PRD §3.6)
# ---------------------------------------------------------------------------

@app.get("/api/search/filters")
async def get_search_filters():
    """
    Return distinct filterable values for the UI filter panel.

    Response:
      { companies: [...], locations: [...], batch_years: [...], skills: [...] }
    """
    if unique_values is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    all_skills = sorted(set(s for skills in df["skills_list"] for s in skills))
    return {
        "companies": unique_values.get("companies", []),
        "locations": unique_values.get("locations", []),
        "batch_years": unique_values.get("batch_years", []),
        "departments": unique_values.get("departments", []),
        "skills": all_skills,
    }


# ---------------------------------------------------------------------------
# Alumni Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/alumni/{alumnus_id}")
async def get_alumni(alumnus_id: str):
    """Get a single alumni profile by ID."""
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    row = df[df["alumnus_id"] == alumnus_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Alumni {alumnus_id} not found")
    r = row.iloc[0]
    return {
        "alumnus_id": r["alumnus_id"],
        "full_name": r["full_name"],
        "batch_year": int(r["batch_year"]),
        "department": r["department"],
        "current_company": r["current_company"],
        "current_role": r["current_role"],
        "city": r["city"],
        "skills": r["skills_list"],
        "bio": r["bio"],
        "mentor_id": r.get("mentor_id", ""),
        "phone": r.get("phone", "N/A"),
        "email": r.get("email", "N/A"),
    }


@app.get("/api/alumni/{alumnus_id}/graph")
async def get_alumni_graph(alumnus_id: str):
    """Get the graph neighborhood of an alumni for vis.js visualization (2-hop)."""
    if not alumni_graph:
        raise HTTPException(status_code=503, detail="Graph not built")
    nid = f"alumni_{alumnus_id}"
    if nid not in alumni_graph.graph:
        raise HTTPException(status_code=404, detail=f"Alumni {alumnus_id} not found in graph")
    return alumni_graph.get_neighborhood(nid, max_hops=2)


@app.get("/api/similar/{alumnus_id}")
async def find_similar(alumnus_id: str, top_k: int = 10):
    """Find alumni similar to a given person using embedding + graph similarity."""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    return search_engine.search_similar(alumnus_id, top_k=top_k)


# ---------------------------------------------------------------------------
# Path Finding (PRD §3.1 — type mismatch fix)
# ---------------------------------------------------------------------------

@app.get("/api/path/{id1}/{id2}")
async def find_path(id1: str, id2: str):
    """
    Find the shortest path between two alumni in the graph.

    Accepts integer node IDs as strings; coerces to int with HTTP 400 on invalid input.
    """
    if alumni_graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    try:
        node_id_1 = int(id1)
        node_id_2 = int(id2)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid node id", "detail": f"Both id1 and id2 must be integers, got '{id1}' and '{id2}'"}
        )
    return alumni_graph.find_path(node_id_1, node_id_2)


# ---------------------------------------------------------------------------
# Autocomplete (PRD §3.3 — Trie-based O(k))
# ---------------------------------------------------------------------------

@app.get("/api/autocomplete")
async def autocomplete(q: str = ""):
    """
    Return autocomplete suggestions using prefix Trie lookup (O(k)).

    Each suggestion: { text: str, category: str, icon: str }
    """
    if not autocomplete_trie or len(q) < 2:
        return {"suggestions": []}
    suggestions = autocomplete_trie.search(q, top_k=10)
    return {"suggestions": suggestions}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics about the alumni dataset."""
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    company_counts = Counter(df["current_company"].tolist())
    top_companies = [{"name": k, "count": v} for k, v in company_counts.most_common(10)]

    all_skills = [s for skills in df["skills_list"] for s in skills]
    skill_counts = Counter(all_skills)
    top_skills = [{"name": k, "count": v} for k, v in skill_counts.most_common(15)]

    dept_counts = Counter(df["department"].tolist())
    dept_distribution = [{"name": k, "count": v} for k, v in sorted(dept_counts.items(), key=lambda x: -x[1])]

    batch_counts = Counter(df["batch_year"].tolist())
    batch_distribution = [{"year": int(k), "count": v} for k, v in sorted(batch_counts.items())]

    location_counts = Counter(df["city"].tolist())
    top_locations = [{"name": k, "count": v} for k, v in location_counts.most_common(10)]

    role_counts = Counter(df["current_role"].tolist())
    top_roles = [{"name": k, "count": v} for k, v in role_counts.most_common(10)]

    return {
        "total_alumni": len(df),
        "total_companies": df["current_company"].nunique(),
        "total_skills": len(set(all_skills)),
        "total_locations": df["city"].nunique(),
        "departments": sorted(df["department"].unique().tolist()),
        "batch_years": sorted(df["batch_year"].unique().tolist()),
        "top_companies": top_companies,
        "top_skills": top_skills,
        "dept_distribution": dept_distribution,
        "batch_distribution": batch_distribution,
        "top_locations": top_locations,
        "top_roles": top_roles,
    }


@app.get("/api/filters")
async def get_filters():
    """Get available filter options for the search UI (legacy endpoint)."""
    if unique_values is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    return unique_values


# ---------------------------------------------------------------------------
# Cache & Metrics (PRD §3.12, §3.13)
# ---------------------------------------------------------------------------

@app.get("/api/cache/stats")
async def cache_stats():
    """Return LRU cache statistics: hits, misses, evictions, hit_rate."""
    return cache.stats


@app.get("/api/metrics")
async def get_metrics():
    """
    Return aggregate observability metrics.

    Includes latency percentiles, cache hit rate, and background task status
    (node2vec_ready, embeddings_ready).
    """
    return obs_logger.get_metrics(cache_stats=cache.stats)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@app.get("/api/export")
async def export_results(
    query: str,
    top_k: int = 20,
    graph_weight: float = 0.4,
    company_filter: str = None,
    location_filter: str = None,
):
    """Export search results as CSV."""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    data = search_engine.search(
        query, limit=top_k, graph_weight=graph_weight,
        company_filter=company_filter, location_filter=location_filter,
    )
    import io
    import csv
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Name", "Score", "CE Score", "Role", "Company",
        "Batch", "Department", "City", "Skills", "Explanation"
    ])
    for i, result in enumerate(data["results"]):
        p = result["profile"]
        writer.writerow([
            i + 1, p["full_name"], f"{result['score']:.3f}",
            f"{result.get('cross_encoder_score', ''):.3f}" if result.get("cross_encoder_score") else "",
            p["current_role"], p["current_company"],
            p["batch_year"], p["department"], p["city"],
            " | ".join(p.get("skills", [])),
            result.get("explanation", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=alumni_search_{query[:30].replace(' ', '_')}.csv"}
    )


# ---------------------------------------------------------------------------
# Alumni List (for dropdowns)
# ---------------------------------------------------------------------------

@app.get("/api/alumni-list")
async def alumni_list(q: str = ""):
    """Return a list of alumni names and IDs for path-finder dropdowns."""
    if df is None:
        return {"alumni": []}
    results = []
    q_lower = q.lower()
    for _, row in df.iterrows():
        if q_lower and q_lower not in row["full_name"].lower():
            continue
        results.append({
            "id": int(row["alumnus_id"]),
            "name": row["full_name"],
            "role": row["current_role"],
            "company": row["current_company"],
            "batch": int(row["batch_year"]),
            "department": row["department"],
        })
        if len(results) >= 20:
            break
    return {"alumni": results}


# ---------------------------------------------------------------------------
# Favicon
# ---------------------------------------------------------------------------

@app.get("/favicon.ico")
async def favicon():
    """Serve an SVG favicon."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#6366f1"/><stop offset="100%" style="stop-color:#a855f7"/>
        </linearGradient></defs>
        <rect width="100" height="100" rx="20" fill="url(#g)"/>
        <circle cx="50" cy="50" r="12" fill="none" stroke="#fff" stroke-width="4"/>
        <circle cx="50" cy="22" r="5" fill="#fff"/><circle cx="50" cy="78" r="5" fill="#fff"/>
        <circle cx="22" cy="50" r="5" fill="#fff"/><circle cx="78" cy="50" r="5" fill="#fff"/>
        <line x1="50" y1="34" x2="50" y2="22" stroke="#fff" stroke-width="3"/>
        <line x1="50" y1="66" x2="50" y2="78" stroke="#fff" stroke-width="3"/>
        <line x1="34" y1="50" x2="22" y2="50" stroke="#fff" stroke-width="3"/>
        <line x1="66" y1="50" x2="78" y2="50" stroke="#fff" stroke-width="3"/>
    </svg>'''
    return Response(content=svg, media_type="image/svg+xml")
