"""
FastAPI Backend — Main application with REST endpoints for semantic search.
"""
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from collections import Counter

from config import FRONTEND_DIR, ALUMNI_CSV_PATH
from backend.models import SearchRequest, SearchResponse, FilterOptions, StatsResponse, GraphData
from backend.data_loader import load_alumni_data, get_unique_values
from backend.graph_builder import AlumniGraph
from backend.embeddings import EmbeddingsManager
from backend.entity_extractor import EntityExtractor
from backend.search_engine import HybridSearchEngine


# --- Application Setup ---
app = FastAPI(
    title="Semantic Search on Alumni Graph",
    description="AI-powered semantic search over alumni networks using SBERT + FAISS + Graph scoring",
    version="1.0.0",
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
search_engine: HybridSearchEngine = None
alumni_graph: AlumniGraph = None
df = None
unique_values = None


@app.on_event("startup")
async def startup():
    """Initialize all components on server startup."""
    global search_engine, alumni_graph, df, unique_values

    print("\n" + "=" * 60)
    print("  SEMANTIC SEARCH ON ALUMNI GRAPH — Starting Up")
    print("=" * 60)

    start = time.time()

    # 1. Generate data if needed
    if not os.path.exists(ALUMNI_CSV_PATH):
        print("\n[1/4] Generating alumni data...")
        from data.generate_alumni import generate_alumni, write_csv
        records = generate_alumni(500)
        write_csv(records, ALUMNI_CSV_PATH)
    else:
        print("\n[1/4] Alumni data found.")

    # 2. Load and normalize data
    print("\n[2/4] Loading & normalizing alumni data...")
    df = load_alumni_data()
    unique_values = get_unique_values(df)

    # 3. Build graph
    print("\n[3/4] Building alumni graph...")
    alumni_graph = AlumniGraph()
    alumni_graph.build_from_dataframe(df)

    # 4. Build/load embeddings and FAISS index
    print("\n[4/4] Building embeddings & FAISS index...")
    embeddings_mgr = EmbeddingsManager()

    if not embeddings_mgr.load_from_cache():
        embeddings_mgr.load_model()
        embeddings_mgr.build_index(
            profile_texts=df["profile_text"].tolist(),
            alumni_ids=df["alumnus_id"].astype(str).tolist()
        )
    else:
        embeddings_mgr.load_model()  # Still need model for query embedding

    # 5. Initialize entity extractor
    extractor = EntityExtractor()
    extractor.load_entities(alumni_graph.get_all_entity_names())

    # 6. Initialize search engine
    search_engine = HybridSearchEngine(df, embeddings_mgr, alumni_graph, extractor)

    elapsed = round(time.time() - start, 1)
    print(f"\n{'=' * 60}")
    print(f"  READY — {len(df)} alumni indexed in {elapsed}s")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"  Frontend: http://localhost:8000")
    print(f"{'=' * 60}\n")


# --- Serve Frontend ---
@app.get("/")
async def serve_frontend():
    """Serve the main HTML page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. API is running at /docs"}


# Mount static files for CSS/JS
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# --- API Endpoints ---

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute a semantic search query with graph-boosted reranking.
    
    Accepts natural language queries and returns ranked alumni results
    with scores, explanations, and metadata.
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    result = search_engine.search(
        query=request.query,
        top_k=request.top_k,
        batch_filter=request.batch_filter,
        dept_filter=request.dept_filter,
        graph_weight=request.graph_weight,
    )

    return result


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
    }


@app.get("/api/alumni/{alumnus_id}/graph")
async def get_alumni_graph(alumnus_id: str):
    """
    Get the graph neighborhood of an alumni for vis.js visualization.
    Returns nodes and edges within 2 hops.
    """
    if not alumni_graph:
        raise HTTPException(status_code=503, detail="Graph not built")

    nid = f"alumni_{alumnus_id}"
    if nid not in alumni_graph.graph:
        raise HTTPException(status_code=404, detail=f"Alumni {alumnus_id} not found in graph")

    return alumni_graph.get_neighborhood(nid, max_hops=2)


@app.get("/api/similar/{alumnus_id}")
async def find_similar(alumnus_id: str, top_k: int = 10):
    """
    Find alumni similar to a given person.
    Uses their embedding vector and graph neighborhood as the query.
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    return search_engine.search_similar(alumnus_id, top_k=top_k)


@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics about the alumni dataset."""
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Top companies
    company_counts = Counter(df["current_company"].tolist())
    top_companies = [{"name": k, "count": v} for k, v in company_counts.most_common(10)]

    # Top skills
    all_skills = [s for skills in df["skills_list"] for s in skills]
    skill_counts = Counter(all_skills)
    top_skills = [{"name": k, "count": v} for k, v in skill_counts.most_common(15)]

    # Department distribution
    dept_counts = Counter(df["department"].tolist())
    dept_distribution = [{"name": k, "count": v} for k, v in sorted(dept_counts.items(), key=lambda x: -x[1])]

    # Batch year distribution
    batch_counts = Counter(df["batch_year"].tolist())
    batch_distribution = [{"year": int(k), "count": v} for k, v in sorted(batch_counts.items())]

    # Top locations
    location_counts = Counter(df["city"].tolist())
    top_locations = [{"name": k, "count": v} for k, v in location_counts.most_common(10)]

    # Top roles
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
    """Get available filter options for the search UI."""
    if unique_values is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    return unique_values


@app.get("/api/autocomplete")
async def autocomplete(q: str = ""):
    """Return autocomplete suggestions for search."""
    if df is None or len(q) < 2:
        return {"suggestions": []}

    q_lower = q.lower()
    suggestions = []

    # Match alumni names
    name_matches = df[df["full_name"].str.lower().str.contains(q_lower, na=False)]["full_name"].head(5).tolist()
    for name in name_matches:
        suggestions.append({"text": f"Alumni similar to {name}", "type": "alumni", "icon": "👤"})

    # Match skills
    all_skills = sorted(set(s for skills in df["skills_list"] for s in skills))
    skill_matches = [s for s in all_skills if q_lower in s.lower()][:4]
    for skill in skill_matches:
        suggestions.append({"text": f"Alumni with {skill} skills", "type": "skill", "icon": "⚡"})

    # Match companies
    companies = sorted(df["current_company"].unique().tolist())
    company_matches = [c for c in companies if q_lower in c.lower()][:3]
    for company in company_matches:
        suggestions.append({"text": f"Alumni working at {company}", "type": "company", "icon": "🏢"})

    # Match cities
    cities = sorted(df["city"].unique().tolist())
    city_matches = [c for c in cities if q_lower in c.lower()][:3]
    for city in city_matches:
        suggestions.append({"text": f"Alumni in {city}", "type": "location", "icon": "📍"})

    return {"suggestions": suggestions[:10]}


@app.get("/api/export")
async def export_results(query: str, top_k: int = 20, graph_weight: float = 0.4):
    """Export search results as CSV."""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    data = search_engine.search(query, top_k=top_k, graph_weight=graph_weight)
    import io
    import csv
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Name", "Score", "Role", "Company", "Batch", "Department", "City", "Skills", "Explanation"])

    for i, result in enumerate(data["results"]):
        p = result["profile"]
        writer.writerow([
            i + 1, p["full_name"], f"{result['score']:.3f}",
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
    from fastapi.responses import Response
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/api/path/{id1}/{id2}")
async def find_path(id1: int, id2: int):
    """Find the shortest path between two alumni in the graph."""
    if alumni_graph is None:
        raise HTTPException(status_code=503, detail="Graph not initialized")
    return alumni_graph.find_path(id1, id2)


@app.get("/api/alumni-list")
async def alumni_list(q: str = ""):
    """Return a list of alumni names and IDs for dropdowns."""
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
        })
        if len(results) >= 20:
            break

    return {"alumni": results}
