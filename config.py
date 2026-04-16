"""
Central configuration for the Semantic Search on Alumni Graph system.
Updated for PRD v2: HNSW FAISS, cross-encoder, conversational LLM backend, SQLite path.
"""
import os
from typing import Literal

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

ALUMNI_CSV_PATH = os.path.join(DATA_DIR, "alumni.csv")
EMBEDDINGS_PATH = os.path.join(CACHE_DIR, "embeddings.npy")
FAISS_INDEX_PATH = os.path.join(CACHE_DIR, "faiss.index")
FAISS_VERSION_PATH = os.path.join(CACHE_DIR, "faiss.version")   # auto-versioned sentinel
GRAPH_PATH = os.path.join(CACHE_DIR, "graph.pickle")
ID_MAP_PATH = os.path.join(CACHE_DIR, "id_map.json")
SQLITE_PATH = os.path.join(DATA_DIR, "alumni.db")               # P2 SQLite migration

# --- Model ---
SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Cross-encoder reranking (PRD §3.4)
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- FAISS HNSW (PRD §3.11) ---
HNSW_M = 32               # Number of bi-directional links per node
HNSW_EF_CONSTRUCTION = 200  # Build-time beam width (quality vs. speed)
HNSW_EF_SEARCH = 100       # Query-time beam width

# --- Node2Vec (PRD §3.9) ---
NODE2VEC_DIMENSIONS = 128
NODE2VEC_WALK_LENGTH = 30
NODE2VEC_NUM_WALKS = 200
NODE2VEC_WORKERS = 4
NODE2VEC_ENABLED = True     # Set False to skip on slow machines

# --- Search ---
DEFAULT_TOP_K = 20
FAISS_SEARCH_K = 50         # Candidates retrieved from FAISS before reranking
DEFAULT_VECTOR_WEIGHT = 0.60
DEFAULT_GRAPH_WEIGHT = 0.40

# --- Graph Scoring Weights ---
CENTRALITY_WEIGHT = 0.4
ENTITY_OVERLAP_WEIGHT = 0.3
RELATIONSHIP_DENSITY_WEIGHT = 0.3

# --- Score Blend for GRAPH-intent queries (PRD §3.9) ---
GRAPH_INTENT_SEMANTIC_WEIGHT = 0.40
GRAPH_INTENT_PPR_WEIGHT = 0.35
GRAPH_INTENT_NODE2VEC_WEIGHT = 0.25

# --- Pagination ---
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# --- Conversational LLM Backend (PRD §3.14) ---
# "none"   → rule-based only (no API key required)
# "openai" → GPT-4o-mini (set OPENAI_API_KEY env var)
# "local"  → llama-cpp-python (set LOCAL_LLM_PATH below)
LLM_BACKEND: Literal["none", "openai", "local"] = "none"
LOCAL_LLM_PATH: str = ""   # Path to GGUF model file when LLM_BACKEND="local"

# --- Cache ---
CACHE_MAX_SIZE = 1000        # Max LRU entries
CACHE_SEARCH_TTL = 300       # 5 minutes for search results
CACHE_EMBEDDING_TTL = 3600   # 1 hour for embeddings
CACHE_GRAPH_TTL = 300        # 5 minutes for graph scores

# --- Server ---
API_HOST = "0.0.0.0"
API_PORT = 8000

# --- Profile Text Template ---
PROFILE_TEMPLATE = (
    "{name}, {batch} batch, {department} department, "
    "currently {role} at {company} in {location}. "
    "Skills: {skills}. {bio}"
)

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(os.path.join(DOCS_DIR, "benchmarks"), exist_ok=True)
