"""
Pydantic models for API request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SearchRequest(BaseModel):
    """Request body for the /api/search endpoint."""
    query: str = Field(..., max_length=500, description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    batch_filter: Optional[List[int]] = Field(default=None, description="Filter by graduation year(s)")
    dept_filter: Optional[List[str]] = Field(default=None, description="Filter by department(s)")
    graph_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight for graph score (0.0-1.0)")


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


class SearchResultItem(BaseModel):
    """Individual search result with scores and explanation."""
    id: str
    name: str
    score: float = Field(description="Final hybrid score")
    vector_score: float = Field(description="Cosine similarity score from FAISS")
    graph_score: float = Field(description="Graph-based relevance score")
    explanation: str = Field(description="Human-readable explanation of why this result matched")
    profile: AlumniProfile


class SearchResponse(BaseModel):
    """Complete search response."""
    results: List[SearchResultItem]
    total: int
    query: str
    latency_ms: float


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

    class Config:
        populate_by_name = True


class GraphData(BaseModel):
    """Graph neighborhood data for vis.js rendering."""
    nodes: List[dict]
    edges: List[dict]
    center_id: str


class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_alumni: int
    total_companies: int
    total_skills: int
    departments: List[str]
    batch_years: List[int]
    top_companies: List[dict]
    top_skills: List[dict]


class FilterOptions(BaseModel):
    """Available filter options."""
    departments: List[str]
    batch_years: List[int]
    companies: List[str]
    locations: List[str] 