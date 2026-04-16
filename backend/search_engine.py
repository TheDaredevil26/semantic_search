"""
Search Engine — Hybrid search combining vector similarity with graph scoring.
"""
import time
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_VECTOR_WEIGHT, DEFAULT_GRAPH_WEIGHT, FAISS_SEARCH_K
from backend.embeddings import EmbeddingsManager
from backend.graph_builder import AlumniGraph
from backend.entity_extractor import EntityExtractor


class HybridSearchEngine:
    """
    Hybrid search engine that fuses vector similarity with graph-based scoring.
    
    Pipeline:
    1. Embed query → FAISS ANN search → top-50 candidates
    2. Extract entities from query
    3. Compute graph scores for each candidate
    4. Fuse scores: final = α*vector + β*graph
    5. Generate explanations
    6. Return top-K reranked results
    """

    def __init__(self, df: pd.DataFrame, embeddings_mgr: EmbeddingsManager,
                 graph: AlumniGraph, entity_extractor: EntityExtractor):
        self.df = df
        self.embeddings = embeddings_mgr
        self.graph = graph
        self.extractor = entity_extractor

        # Build lookup dict for fast profile access
        self._profiles = {}
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
            }

    def search(self, query: str, top_k: int = 10,
               batch_filter: list = None, dept_filter: list = None,
               graph_weight: float = None) -> dict:
        """
        Execute a hybrid search query.
        
        Args:
            query: Natural language search query.
            top_k: Number of results to return.
            batch_filter: Optional list of batch years to filter.
            dept_filter: Optional list of departments to filter.
            graph_weight: Weight for graph score (0-1). Vector weight = 1 - graph_weight.
        
        Returns:
            dict with 'results', 'total', 'query', 'latency_ms'
        """
        start_time = time.time()

        gw = graph_weight if graph_weight is not None else DEFAULT_GRAPH_WEIGHT
        vw = 1.0 - gw

        # Step 1: FAISS vector search — get top-50 candidates
        vector_results = self.embeddings.search(query, top_k=FAISS_SEARCH_K)

        # Step 2: Extract entities from query
        entities = self.extractor.extract(query)

        # Step 3: Apply filters and collect candidates
        candidates = []
        for alumnus_id, vector_score in vector_results:
            profile = self._profiles.get(alumnus_id)
            if not profile:
                continue

            # Apply batch filter
            if batch_filter and profile["batch_year"] not in batch_filter:
                continue

            # Apply department filter
            if dept_filter and profile["department"] not in dept_filter:
                continue

            candidates.append({
                "alumnus_id": alumnus_id,
                "vector_score": vector_score,
                "profile": profile,
            })

        # Step 4: Compute graph scores
        query_entity_nids = self.graph.get_entity_node_ids(entities)
        candidate_nids = [f"alumni_{c['alumnus_id']}" for c in candidates]

        for cand in candidates:
            nid = f"alumni_{cand['alumnus_id']}"
            cand["graph_score"] = self.graph.compute_graph_score(
                nid, query_entity_nids, candidate_nids
            )

        # Step 5: Hybrid scoring
        # Normalize vector scores to [0, 1]
        if candidates:
            max_vs = max(c["vector_score"] for c in candidates)
            min_vs = min(c["vector_score"] for c in candidates)
            vs_range = max_vs - min_vs if max_vs > min_vs else 1.0

            max_gs = max(c["graph_score"] for c in candidates) or 1.0

            for cand in candidates:
                norm_vs = (cand["vector_score"] - min_vs) / vs_range if vs_range > 0 else cand["vector_score"]
                norm_gs = cand["graph_score"] / max_gs if max_gs > 0 else 0

                cand["final_score"] = round(vw * norm_vs + gw * norm_gs, 4)

        # Step 6: Sort by final score
        candidates.sort(key=lambda c: c["final_score"], reverse=True)

        # Step 7: Take top-K and generate explanations
        top_results = candidates[:top_k]

        results = []
        for cand in top_results:
            explanation = self.extractor.generate_explanation(
                query, cand["profile"], cand["vector_score"],
                cand["graph_score"], entities
            )

            results.append({
                "id": cand["alumnus_id"],
                "name": cand["profile"]["full_name"],
                "score": cand["final_score"],
                "vector_score": round(cand["vector_score"], 4),
                "graph_score": round(cand["graph_score"], 4),
                "explanation": explanation,
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
                }
            })

        latency_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "results": results,
            "total": len(results),
            "query": query,
            "latency_ms": latency_ms,
        }

    def search_similar(self, alumnus_id: str, top_k: int = 10) -> dict:
        """
        Find alumni similar to a given person (entity-based similarity).
        Uses their embedding vector directly as the query.
        """
        start_time = time.time()

        profile = self._profiles.get(alumnus_id)
        if not profile:
            return {"results": [], "total": 0, "query": f"Similar to {alumnus_id}", "latency_ms": 0}

        # Get this person's embedding
        embedding = self.embeddings.get_embedding_by_id(alumnus_id)
        if embedding is None:
            return {"results": [], "total": 0, "query": f"Similar to {profile['full_name']}", "latency_ms": 0}

        # Search by vector
        vector_results = self.embeddings.search_by_vector(embedding, top_k=FAISS_SEARCH_K)

        # Get this person's graph neighborhood for graph scoring
        nid = f"alumni_{alumnus_id}"
        neighbors = list(self.graph.graph.neighbors(nid)) if nid in self.graph.graph else []
        query_entity_nids = neighbors

        candidates = []
        for aid, vs in vector_results:
            if aid == alumnus_id:  # Skip self
                continue
            p = self._profiles.get(aid)
            if not p:
                continue
            candidates.append({
                "alumnus_id": aid,
                "vector_score": vs,
                "profile": p,
            })

        # Graph scores
        candidate_nids = [f"alumni_{c['alumnus_id']}" for c in candidates]
        for cand in candidates:
            cnid = f"alumni_{cand['alumnus_id']}"
            cand["graph_score"] = self.graph.compute_graph_score(
                cnid, query_entity_nids, candidate_nids
            )

        # Hybrid scoring
        gw = DEFAULT_GRAPH_WEIGHT
        vw = 1.0 - gw

        if candidates:
            max_vs = max(c["vector_score"] for c in candidates) or 1.0
            min_vs = min(c["vector_score"] for c in candidates)
            vs_range = max_vs - min_vs if max_vs > min_vs else 1.0
            max_gs = max(c["graph_score"] for c in candidates) or 1.0

            for cand in candidates:
                norm_vs = (cand["vector_score"] - min_vs) / vs_range
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
                "explanation": f"Similar to {profile['full_name']} — shared career profile and network connections",
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
                }
            })

        latency_ms = round((time.time() - start_time) * 1000, 1)
        return {
            "results": results,
            "total": len(results),
            "query": f"Alumni similar to {profile['full_name']}",
            "latency_ms": latency_ms,
        }
