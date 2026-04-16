"""
Pydantic models for API request/response schemas.
Updated for PRD v2: pagination, structured filters, explainability, conversational search.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# ---------------------------------------------------------------------------
# Search Request
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    """Request body for the /api/search endpoint."""
    query: str = Field(..., max_length=500, description="Natural language search query")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=20, ge=1, le=100, description="Results per page")

    # Legacy convenience fields (kept for backward compat)
    top_k: int = Field(default=50, ge=1, le=200, description="Candidate pool size before reranking")
    batch_filter: Optional[List[int]] = Field(default=None, description="Filter by graduation year(s)")
    dept_filter: Optional[List[str]] = Field(default=None, description="Filter by department(s)")
    graph_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight for graph score (0–1)")

    # New structured filters (PRD §3.6)
    company_filter: Optional[str] = Field(default=None, description="Filter by company (partial match)")
    location_filter: Optional[str] = Field(default=None, description="Filter by city/location (partial match)")
    batch_year_filter: Optional[str] = Field(default=None, description="Filter by batch year or range e.g. '2019' or '2015-2020'")
    skills_filter: List[str] = Field(default_factory=list, description="Filter by skills (AND logic)")


# ---------------------------------------------------------------------------
# Conversational Search
# ---------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    """A single turn in a multi-turn conversation."""
    role: Literal["user", "assistant"]
    content: str


class ConversationalSearchRequest(BaseModel):
    """Request body for the /api/search/conversational endpoint."""
    query: str = Field(..., max_length=500)
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Profile & Explainability
# ---------------------------------------------------------------------------

class AlumniProfile(BaseModel):
    """Complete alumni profile data."""
    alumnus_id: str
    full_name: str
    batch_year: int
    department: str
    current_company: str
    current_role: str
    city: str
    skills: List[str]
    bio: str
    mentor_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class ExplainInfo(BaseModel):
    """Explainability breakdown for a single search result (PRD §3.16)."""
    semantic_score: float = Field(description="Raw cosine similarity from SBERT/FAISS (0–1)")
    graph_score: float = Field(description="Graph-based relevance score (0–1)")
    cross_encoder_score: Optional[float] = Field(default=None, description="Cross-encoder reranking score")
    matched_keywords: List[str] = Field(default_factory=list, description="Query tokens found in this profile")
    graph_connections: List[str] = Field(default_factory=list, description="Notable shared connections")
    intent: Optional[str] = Field(default=None, description="Classified query intent")


# ---------------------------------------------------------------------------
# Search Result & Response
# ---------------------------------------------------------------------------

class SearchResultItem(BaseModel):
    """Individual search result with scores, explanation, and full profile."""
    id: str
    name: str
    score: float = Field(description="Final hybrid score")
    vector_score: float = Field(description="Cosine similarity score from FAISS")
    graph_score: float = Field(description="Graph-based relevance score")
    cross_encoder_score: Optional[float] = Field(default=None, description="Cross-encoder reranking score")
    explanation: str = Field(description="Human-readable explanation of why this result matched")
    explain: Optional[ExplainInfo] = Field(default=None, description="Detailed explainability breakdown")
    profile: AlumniProfile


class SearchResponse(BaseModel):
    """Complete search response with pagination metadata."""
    results: List[SearchResultItem]
    total: int           # Number of results on this page
    total_count: int     # Total matching results across all pages
    page: int
    limit: int
    total_pages: int
    query: str
    latency_ms: float
    intent: Optional[str] = None


# ---------------------------------------------------------------------------
# Graph Data
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    """Node for vis.js graph visualization."""
    id: str
    label: str
    group: str  # node type: alumni, company, skill, batch, etc.
    title: Optional[str] = None  # tooltip
    size: Optional[int] = None
    color: Optional[dict] = None


class GraphEdge(BaseModel):
    """Edge for vis.js graph visualization."""
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    label: Optional[str] = None
    color: Optional[dict] = None
    dashes: Optional[bool] = None
    width: Optional[float] = None

    class Config:
        populate_by_name = True


class GraphData(BaseModel):
    """Graph neighborhood data for vis.js rendering."""
    nodes: List[dict]
    edges: List[dict]
    center_id: str


# ---------------------------------------------------------------------------
# Stats & Filters
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_alumni: int
    total_companies: int
    total_skills: int
    total_locations: int
    departments: List[str]
    batch_years: List[int]
    top_companies: List[dict]
    top_skills: List[dict]
    dept_distribution: List[dict]
    batch_distribution: List[dict]
    top_locations: List[dict]
    top_roles: List[dict]


class FilterOptions(BaseModel):
    """Available filter options for the search UI (PRD §3.6)."""
    departments: List[str]
    batch_years: List[int]
    companies: List[str]
    locations: List[str]
    skills: List[str]