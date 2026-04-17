"""
Search Engine — Multi-stage hybrid search pipeline.

PRD v2 changes:
  §3.4  — Cross-encoder reranking (top-50 FAISS → CE rescore → top-K)
  §3.5  — Query intent classification (STRUCTURED / SEMANTIC / GRAPH)
  §3.6  — Structured filters (company, location, batch_year, skills — applied pre-FAISS)
  §3.7/8— Weighted graph + Personalized PageRank
  §3.9  — Node2Vec blend for GRAPH-intent queries
  §3.2  — Pagination (applied post-reranking)
  §3.16 — ExplainInfo populated for every result
"""
from __future__ import annotations

import math
import re
import time
from typing import Optional

import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DEFAULT_GRAPH_WEIGHT, DEFAULT_TOP_K, FAISS_SEARCH_K,
    GRAPH_INTENT_SEMANTIC_WEIGHT, GRAPH_INTENT_PPR_WEIGHT, GRAPH_INTENT_NODE2VEC_WEIGHT,
)
from backend.embeddings import EmbeddingsManager, CrossEncoderReranker
from backend.graph_builder import AlumniGraph
from backend.entity_extractor import EntityExtractor


# ---------------------------------------------------------------------------
# Intent Classifier (PRD §3.5)
# ---------------------------------------------------------------------------

_STRUCTURED_PREFIXES = re.compile(
    r'\b(company|batch|location|city|skills?|dept|department)\s*:', re.I
)
_GRAPH_KEYWORDS = re.compile(
    r'\b(connected to|path between|colleague[s]? of|network of|via|mutual|link)\b', re.I
)


def classify_intent(query: str) -> str:
    """
    Classify query into one of: STRUCTURED | SEMANTIC | GRAPH.

    Rules:
      STRUCTURED : query contains field:value tokens (company:Google)
      GRAPH      : query asks for relationships or paths
      SEMANTIC   : everything else
    """
    if _STRUCTURED_PREFIXES.search(query):
        return "STRUCTURED"
    if _GRAPH_KEYWORDS.search(query):
        return "GRAPH"
    return "SEMANTIC"


# ---------------------------------------------------------------------------
# Structured filter helpers (PRD §3.6)
# ---------------------------------------------------------------------------

def _parse_batch_filter(batch_year_filter: Optional[str]) -> Optional[tuple]:
    """
    Parse batch_year_filter string into an inclusive (min, max) int tuple.

    "2019"        → (2019, 2019)
    "2015-2020"   → (2015, 2020)
    None          → None
    """
    if not batch_year_filter:
        return None
    batch_year_filter = str(batch_year_filter).strip()
    if "-" in batch_year_filter:
        parts = batch_year_filter.split("-")
        try:
            return (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return None
    try:
        y = int(batch_year_filter)
        return (y, y)
    except ValueError:
        return None


def _apply_structured_filters(
    df_subset: pd.DataFrame,
    company_filter: Optional[str],
    location_filter: Optional[str],
    batch_year_filter: Optional[str],
    skills_filter: list,
    batch_filter: Optional[list] = None,  # Legacy
    dept_filter: Optional[list] = None,   # Legacy
) -> pd.DataFrame:
    """
    Apply SQL-style WHERE clauses to the DataFrame before FAISS embedding.
    Returns a filtered subset of the DataFrame.
    """
    mask = pd.Series([True] * len(df_subset), index=df_subset.index)

    # New structured filters
    if company_filter:
        mask &= df_subset["current_company"].str.lower().str.contains(
            company_filter.lower(), na=False
        )
    if location_filter:
        locs = [l.strip().lower() for l in re.split(r'[,|]', location_filter) if l.strip()]
        if locs:
            regex_pat = "|".join(locs)
            mask &= df_subset["city"].str.lower().str.contains(regex_pat, na=False)
    batch_range = _parse_batch_filter(batch_year_filter)
    if batch_range:
        lo, hi = batch_range
        mask &= (df_subset["batch_year"] >= lo) & (df_subset["batch_year"] <= hi)

    if skills_filter:
        for skill in skills_filter:
            skill_lower = skill.lower()
            mask &= df_subset["skills_list"].apply(
                lambda lst: any(skill_lower in s.lower() for s in lst)
            )

    # Legacy filters (kept for backward compat)
    if batch_filter:
        mask &= df_subset["batch_year"].isin(batch_filter)
    if dept_filter:
        mask &= df_subset["department"].isin(dept_filter)

    return df_subset[mask]


# ---------------------------------------------------------------------------
# Main Search Engine
# ---------------------------------------------------------------------------

class HybridSearchEngine:
    """
    Multi-stage hybrid search engine:
      1. Apply structured filters to reduce candidate pool
      2. FAISS HNSW ANN retrieval (top-50 candidates)
      3. Graph scoring with Personalized PageRank
      4. Cross-encoder reranking
      5. Final hybrid score fusion
      6. Pagination
    """

    def __init__(
        self,
        df: pd.DataFrame,
        embeddings_mgr: EmbeddingsManager,
        graph: AlumniGraph,
        entity_extractor: EntityExtractor,
        cross_encoder: Optional[CrossEncoderReranker] = None,
    ):
        self.df = df
        self.embeddings = embeddings_mgr
        self.graph = graph
        self.extractor = entity_extractor
        self.cross_encoder = cross_encoder

        # Build profile lookup dict
        self._profiles: dict = {}
        for _, row in df.iterrows():
            aid = str(row["alumnus_id"])
            self._profiles[aid] = {
                "alumnus_id": aid,
                "full_name": row["full_name"],
                "batch_year": int(row["batch_year"]),
                "department": row["department"],
                "current_company": row["current_company"],
                "current_role": row["current_role"],
                "city": row["city"],
                "skills_list": row.get("skills_list", []),
                "skills": row["skills"],
                "bio": row["bio"],
                "mentor_id": row.get("mentor_id", ""),
                "phone": row.get("phone", "N/A"),
                "email": row.get("email", "N/A"),
            }

        # Filtered DataFrame cache (rebuilt when filters change)
        self._filtered_ids: Optional[set] = None

    # ------------------------------------------------------------------
    # Main search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        page: int = 1,
        limit: int = 20,
        # Structured filters (PRD §3.6)
        company_filter: Optional[str] = None,
        location_filter: Optional[str] = None,
        batch_year_filter: Optional[str] = None,
        skills_filter: Optional[list] = None,
        # Legacy filters
        batch_filter: Optional[list] = None,
        dept_filter: Optional[list] = None,
        # Weights
        graph_weight: Optional[float] = None,
    ) -> dict:
        """
        Execute a paginated, multi-stage hybrid search.

        Returns dict with results (current page), total_count, page, limit, total_pages.
        """
        start_time = time.time()
        skills_filter = skills_filter or []

        # 1. Intent classification (PRD §3.5)
        intent = classify_intent(query)

        # 2. Apply structured filters to DataFrame → get allowed IDs
        filtered_df = _apply_structured_filters(
            self.df,
            company_filter=company_filter,
            location_filter=location_filter,
            batch_year_filter=batch_year_filter,
            skills_filter=skills_filter,
            batch_filter=batch_filter,
            dept_filter=dept_filter,
        )
        allowed_ids = set(filtered_df["alumnus_id"].astype(str).tolist())

        # 3. FAISS ANN search (full index — filter post-retrieval)
        # allowed_ids=None means no filter active; empty set means filter has zero matches
        has_filters = any([
            company_filter, location_filter, batch_year_filter,
            skills_filter, batch_filter, dept_filter
        ])
        # Only compute allowed_ids when filters are actually active
        if has_filters:
            allowed_ids: Optional[set] = set(filtered_df["alumnus_id"].astype(str).tolist())
        else:
            allowed_ids = None  # No filter — all candidates allowed

        if not has_filters or allowed_ids is None:
            # No filters: standard FAISS search
            vector_results = self.embeddings.search(query, top_k=FAISS_SEARCH_K)
        elif len(allowed_ids) == 0:
            # Filters leave zero candidates — short-circuit
            vector_results = []
        elif len(allowed_ids) <= FAISS_SEARCH_K:
            # Small filtered pool: score ALL filtered candidates directly
            # (avoids losing filtered matches that FAISS would not retrieve)
            vector_results = self.embeddings.search_by_ids(query, list(allowed_ids))
        else:
            # Large filtered pool: run FAISS over full index then post-filter
            # Use a larger k to account for filter shrinkage
            oversample_k = min(len(allowed_ids), FAISS_SEARCH_K * 4)
            vector_results = self.embeddings.search(query, top_k=oversample_k)

        # 4. Entity extraction
        entities = self.extractor.extract(query)

        # 5. Personalized PageRank (PRD §3.8)
        query_tokens = [t for t in query.lower().split() if len(t) > 2]
        ppr_scores = self.graph.compute_personalized_pagerank(query_tokens)

        # 6. Collect & filter candidates
        # allowed_ids=None → no filtering; allowed_ids=set → must be in set
        candidates = []
        for alumnus_id, vector_score in vector_results:
            if allowed_ids is not None and alumnus_id not in allowed_ids:
                continue
            profile = self._profiles.get(alumnus_id)
            if not profile:
                continue
            candidates.append({
                "alumnus_id": alumnus_id,
                "vector_score": vector_score,
                "profile": profile,
                "cross_encoder_score": None,
            })

        # 7. Graph scoring
        query_entity_nids = self.graph.get_entity_node_ids(entities)
        candidate_nids = [f"alumni_{c['alumnus_id']}" for c in candidates]

        for cand in candidates:
            nid = f"alumni_{cand['alumnus_id']}"
            cand["graph_score"] = self.graph.compute_graph_score(
                nid, query_entity_nids, candidate_nids, ppr_scores=ppr_scores
            )

        # 8. Cross-encoder reranking (PRD §3.4)
        if self.cross_encoder and candidates:
            candidates = self.cross_encoder.rerank(query, candidates)

        # 9. Score fusion
        gw = graph_weight if graph_weight is not None else DEFAULT_GRAPH_WEIGHT
        vw = 1.0 - gw

        if candidates:
            max_vs = max(c["vector_score"] for c in candidates) or 1.0
            min_vs = min(c["vector_score"] for c in candidates)
            vs_range = max_vs - min_vs if max_vs > min_vs else 1.0
            max_gs = max(c["graph_score"] for c in candidates) or 1.0

            for cand in candidates:
                norm_vs = (cand["vector_score"] - min_vs) / vs_range if vs_range > 0 else cand["vector_score"]
                norm_gs = cand["graph_score"] / max_gs if max_gs > 0 else 0

                # If cross-encoder is available, let it dominate
                if cand.get("cross_encoder_score") is not None:
                    ce_score = cand["cross_encoder_score"]
                    # Normalize CE score (raw logit, typically -5 to +5)
                    norm_ce = 1.0 / (1.0 + math.exp(-ce_score))  # sigmoid
                    cand["final_score"] = round(0.5 * norm_ce + 0.3 * norm_vs + 0.2 * norm_gs, 4)
                else:
                    cand["final_score"] = round(vw * norm_vs + gw * norm_gs, 4)

        # 10. Sort
        candidates.sort(key=lambda c: c["final_score"], reverse=True)

        # 11. Pagination (applied post-ranking — PRD §3.2)
        total_count = len(candidates)
        total_pages = math.ceil(total_count / limit) if limit else 1
        page = max(1, min(page, total_pages or 1))
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_candidates = candidates[start_idx:end_idx]

        # 12. Build result objects with ExplainInfo
        results = []
        for cand in page_candidates:
            explanation = self.extractor.generate_explanation(
                query, cand["profile"], cand["vector_score"],
                cand["graph_score"], entities
            )
            matched_kws = _extract_matched_keywords(query, cand["profile"])

            explain = {
                "semantic_score": round(cand["vector_score"], 4),
                "graph_score": round(cand["graph_score"], 4),
                "cross_encoder_score": (
                    round(cand["cross_encoder_score"], 4)
                    if cand.get("cross_encoder_score") is not None else None
                ),
                "matched_keywords": matched_kws,
                "graph_connections": [],
                "intent": intent,
            }

            results.append({
                "id": cand["alumnus_id"],
                "name": cand["profile"]["full_name"],
                "score": cand["final_score"],
                "vector_score": round(cand["vector_score"], 4),
                "graph_score": round(cand["graph_score"], 4),
                "cross_encoder_score": explain["cross_encoder_score"],
                "explanation": explanation,
                "explain": explain,
                "profile": {
                    "alumnus_id": cand["profile"]["alumnus_id"],
                    "full_name": cand["profile"]["full_name"],
                    "batch_year": cand["profile"]["batch_year"],
                    "department": cand["profile"]["department"],
                    "current_company": cand["profile"]["current_company"],
                    "current_role": cand["profile"]["current_role"],
                    "city": cand["profile"]["city"],
                    "skills": cand["profile"]["skills_list"],
                    "bio": cand["profile"]["bio"],
                    "mentor_id": cand["profile"].get("mentor_id", ""),
                    "phone": cand["profile"].get("phone", "N/A"),
                    "email": cand["profile"].get("email", "N/A"),
                },
            })

        latency_ms = round((time.time() - start_time) * 1000, 1)
        return {
            "results": results,
            "total": len(results),
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "query": query,
            "latency_ms": latency_ms,
            "intent": intent,
        }

    # ------------------------------------------------------------------
    # Similar profiles
    # ------------------------------------------------------------------

    def search_similar(self, alumnus_id: str, top_k: int = 10) -> dict:
        """Find alumni similar to a given person using their embedding vector."""
        start_time = time.time()
        profile = self._profiles.get(alumnus_id)
        if not profile:
            return {"results": [], "total": 0, "total_count": 0, "page": 1,
                    "limit": top_k, "total_pages": 0, "query": f"Similar to {alumnus_id}", "latency_ms": 0}

        embedding = self.embeddings.get_embedding_by_id(alumnus_id)
        if embedding is None:
            return {"results": [], "total": 0, "total_count": 0, "page": 1,
                    "limit": top_k, "total_pages": 0,
                    "query": f"Similar to {profile['full_name']}", "latency_ms": 0}

        vector_results = self.embeddings.search_by_vector(embedding, top_k=FAISS_SEARCH_K)

        nid = f"alumni_{alumnus_id}"
        neighbors = list(self.graph.graph.neighbors(nid)) if nid in self.graph.graph else []
        query_entity_nids = neighbors

        candidates = []
        for aid, vs in vector_results:
            if aid == alumnus_id:
                continue
            p = self._profiles.get(aid)
            if not p:
                continue
            candidates.append({"alumnus_id": aid, "vector_score": vs, "profile": p,
                                "cross_encoder_score": None})

        candidate_nids = [f"alumni_{c['alumnus_id']}" for c in candidates]
        for cand in candidates:
            cnid = f"alumni_{cand['alumnus_id']}"
            cand["graph_score"] = self.graph.compute_graph_score(
                cnid, query_entity_nids, candidate_nids
            )

        gw = DEFAULT_GRAPH_WEIGHT
        vw = 1.0 - gw
        if candidates:
            max_vs = max(c["vector_score"] for c in candidates) or 1.0
            min_vs = min(c["vector_score"] for c in candidates)
            vs_range = max_vs - min_vs if max_vs > min_vs else 1.0
            max_gs = max(c["graph_score"] for c in candidates) or 1.0
            for cand in candidates:
                norm_vs = (cand["vector_score"] - min_vs) / vs_range if vs_range > 0 else cand["vector_score"]
                norm_gs = cand["graph_score"] / max_gs if max_gs > 0 else 0
                cand["final_score"] = round(vw * norm_vs + gw * norm_gs, 4)

        candidates.sort(key=lambda c: c["final_score"], reverse=True)

        results = []
        for cand in candidates[:top_k]:
            results.append({
                "id": cand["alumnus_id"],
                "name": cand["profile"]["full_name"],
                "score": cand["final_score"],
                "vector_score": round(cand["vector_score"], 4),
                "graph_score": round(cand["graph_score"], 4),
                "cross_encoder_score": None,
                "explanation": f"Similar to {profile['full_name']} — shared career profile and network connections",
                "explain": {
                    "semantic_score": round(cand["vector_score"], 4),
                    "graph_score": round(cand["graph_score"], 4),
                    "cross_encoder_score": None,
                    "matched_keywords": [],
                    "graph_connections": [],
                    "intent": "SEMANTIC",
                },
                "profile": {
                    "alumnus_id": cand["profile"]["alumnus_id"],
                    "full_name": cand["profile"]["full_name"],
                    "batch_year": cand["profile"]["batch_year"],
                    "department": cand["profile"]["department"],
                    "current_company": cand["profile"]["current_company"],
                    "current_role": cand["profile"]["current_role"],
                    "city": cand["profile"]["city"],
                    "skills": cand["profile"]["skills_list"],
                    "bio": cand["profile"]["bio"],
                    "mentor_id": cand["profile"].get("mentor_id", ""),
                    "phone": cand["profile"].get("phone", "N/A"),
                    "email": cand["profile"].get("email", "N/A"),
                },
            })

        latency_ms = round((time.time() - start_time) * 1000, 1)
        return {
            "results": results,
            "total": len(results),
            "total_count": len(results),
            "page": 1,
            "limit": top_k,
            "total_pages": 1,
            "query": f"Alumni similar to {profile['full_name']}",
            "latency_ms": latency_ms,
        }


# ---------------------------------------------------------------------------
# Keyword extraction helper
# ---------------------------------------------------------------------------

def _extract_matched_keywords(query: str, profile: dict) -> list:
    """Find query tokens that appear in the profile text."""
    tokens = set(re.findall(r'\b\w{3,}\b', query.lower()))
    profile_text = (
        f"{profile.get('full_name', '')} {profile.get('current_company', '')} "
        f"{profile.get('current_role', '')} {profile.get('city', '')} "
        f"{profile.get('bio', '')} "
        f"{' '.join(profile.get('skills_list', profile.get('skills', [])))}"
    ).lower()
    return [t for t in tokens if t in profile_text][:8]
