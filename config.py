"""
Central configuration for the Semantic Search on Alumni Graph system.
"""
import os

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

ALUMNI_CSV_PATH = os.path.join(DATA_DIR, "alumni.csv")
EMBEDDINGS_PATH = os.path.join(CACHE_DIR, "embeddings.npy")
FAISS_INDEX_PATH = os.path.join(CACHE_DIR, "faiss.index")
GRAPH_PATH = os.path.join(CACHE_DIR, "graph.pickle")
ID_MAP_PATH = os.path.join(CACHE_DIR, "id_map.json")

# --- Model ---
SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# --- Search ---
DEFAULT_TOP_K = 10
FAISS_SEARCH_K = 50  # Candidates retrieved from FAISS before reranking
DEFAULT_VECTOR_WEIGHT = 0.60
DEFAULT_GRAPH_WEIGHT = 0.40

# --- Graph Scoring Weights ---
CENTRALITY_WEIGHT = 0.4
ENTITY_OVERLAP_WEIGHT = 0.3
RELATIONSHIP_DENSITY_WEIGHT = 0.3

# --- Server ---
API_HOST = "0.0.0.0"
API_PORT = 8000

# --- Profile Text Template ---
PROFILE_TEMPLATE = (
    "{name}, {batch} batch, {department} department, "
    "currently {role} at {company} in {location}. "
    "Skills: {skills}. {bio}"
)

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
