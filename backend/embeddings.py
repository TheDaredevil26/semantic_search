"""
Embeddings Manager — Sentence-BERT encoding, FAISS HNSW indexing, and
Cross-Encoder reranking.

PRD changes:
  §3.11 — IndexFlatIP replaced with IndexHNSWFlat (M=32) + IndexIDMap2
  §3.4  — CrossEncoderReranker class added
  §3.11 — Auto-versioned cache: faiss.version sentinel auto-rebuilds on config change
"""
import hashlib
import json
import os
import sys

import numpy as np
import faiss

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SBERT_MODEL_NAME, EMBEDDING_DIMENSION,
    EMBEDDINGS_PATH, FAISS_INDEX_PATH, FAISS_VERSION_PATH, ID_MAP_PATH, FAISS_SEARCH_K,
    CROSS_ENCODER_MODEL,
    HNSW_M, HNSW_EF_CONSTRUCTION, HNSW_EF_SEARCH,
)


# ---------------------------------------------------------------------------
# FAISS version sentinel
# ---------------------------------------------------------------------------

def _faiss_config_hash() -> str:
    """Return a hash of all FAISS/model config that would invalidate an existing index."""
    config_str = f"{SBERT_MODEL_NAME}|{EMBEDDING_DIMENSION}|{HNSW_M}|{HNSW_EF_CONSTRUCTION}|{HNSW_EF_SEARCH}"
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def _check_and_invalidate_faiss_cache():
    """
    If the cached FAISS index was built with different config, auto-delete it
    so it will be rebuilt on the next call to build_index().
    """
    current_hash = _faiss_config_hash()

    if os.path.exists(FAISS_VERSION_PATH):
        with open(FAISS_VERSION_PATH) as f:
            cached_hash = f.read().strip()
        if cached_hash != current_hash:
            print(f"[FAISS] Config changed ({cached_hash} → {current_hash}). Removing stale index…")
            for path in [FAISS_INDEX_PATH, EMBEDDINGS_PATH, ID_MAP_PATH, FAISS_VERSION_PATH]:
                if os.path.exists(path):
                    os.remove(path)
    else:
        # No version file yet — invalidate to be safe if an index already exists
        if os.path.exists(FAISS_INDEX_PATH):
            print("[FAISS] No version sentinel found. Removing stale index to force rebuild…")
            for path in [FAISS_INDEX_PATH, EMBEDDINGS_PATH, ID_MAP_PATH]:
                if os.path.exists(path):
                    os.remove(path)


def _write_faiss_version():
    """Write the current config hash to the version sentinel file."""
    with open(FAISS_VERSION_PATH, "w") as f:
        f.write(_faiss_config_hash())


# ---------------------------------------------------------------------------
# Embeddings Manager
# ---------------------------------------------------------------------------

class EmbeddingsManager:
    """
    Manages Sentence-BERT embeddings and FAISS HNSW index for alumni profiles.

    Index type: IndexHNSWFlat wrapped in IndexIDMap2 for ID-preserving retrieval.
    """

    def __init__(self):
        self.model = None
        self.index = None          # FAISS IndexIDMap2 wrapping HNSW
        self.id_map: list = []     # Maps integer position → alumnus_id string
        self.embeddings = None     # (N, D) float32 numpy array

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def load_model(self):
        """Load the Sentence-BERT model."""
        from sentence_transformers import SentenceTransformer
        print(f"Loading SBERT model: {SBERT_MODEL_NAME}…")
        self.model = SentenceTransformer(SBERT_MODEL_NAME)
        print("SBERT model loaded.")

    # ------------------------------------------------------------------
    # Index construction
    # ------------------------------------------------------------------

    def build_index(self, profile_texts: list, alumni_ids: list):
        """
        Embed all profile texts and build a FAISS HNSW index.

        Parameters
        ----------
        profile_texts : List[str] — one text blob per alumni profile.
        alumni_ids    : List[str] — corresponding alumnus_id values.
        """
        if self.model is None:
            self.load_model()

        print(f"[FAISS] Building HNSW index (first run)… encoding {len(profile_texts)} profiles.")
        self.embeddings = self.model.encode(
            profile_texts,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=64,
        ).astype(np.float32)

        self.id_map = list(alumni_ids)

        # Build HNSW inner index
        inner = faiss.IndexHNSWFlat(EMBEDDING_DIMENSION, HNSW_M)
        inner.hnsw.efConstruction = HNSW_EF_CONSTRUCTION

        # Wrap with IDMap2 so we can use integer IDs (we use sequential 0…N-1)
        self.index = faiss.IndexIDMap2(inner)

        # Add vectors with integer IDs (0-indexed, maps to id_map)
        ids = np.arange(len(alumni_ids), dtype=np.int64)
        self.index.add_with_ids(self.embeddings, ids)

        # Set efSearch for queries
        faiss.downcast_index(self.index.index).hnsw.efSearch = HNSW_EF_SEARCH

        print(f"[FAISS] HNSW index built: {self.index.ntotal} vectors ({EMBEDDING_DIMENSION}-dim). "
              f"M={HNSW_M}, efConstruction={HNSW_EF_CONSTRUCTION}, efSearch={HNSW_EF_SEARCH}")

        self._save()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self):
        """Save embeddings, index, ID map, and version sentinel to disk."""
        os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
        np.save(EMBEDDINGS_PATH, self.embeddings)
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(ID_MAP_PATH, "w") as f:
            json.dump(self.id_map, f)
        _write_faiss_version()
        print(f"[FAISS] Saved HNSW index, embeddings, and ID map to {os.path.dirname(EMBEDDINGS_PATH)}/")

    def load_from_cache(self) -> bool:
        """
        Attempt to load pre-built embeddings and index from disk.
        Auto-invalidates if config has changed.

        Returns True if loaded successfully, False otherwise.
        """
        _check_and_invalidate_faiss_cache()

        if not all(os.path.exists(p) for p in [EMBEDDINGS_PATH, FAISS_INDEX_PATH, ID_MAP_PATH]):
            return False

        try:
            self.embeddings = np.load(EMBEDDINGS_PATH)
            self.index = faiss.read_index(FAISS_INDEX_PATH)

            # Restore efSearch after loading
            try:
                faiss.downcast_index(self.index.index).hnsw.efSearch = HNSW_EF_SEARCH
            except Exception:
                pass  # Index may not be HNSW if loaded from old cache

            with open(ID_MAP_PATH) as f:
                self.id_map = json.load(f)

            print(f"[FAISS] Loaded cached index with {self.index.ntotal} vectors.")
            return True
        except Exception as e:
            print(f"[FAISS] Failed to load cache: {e}")
            return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query_text: str, top_k: int = None) -> list:
        """
        Embed a query and retrieve nearest neighbours from the HNSW index.

        Returns list of (alumnus_id, cosine_similarity_score) tuples.
        """
        if self.model is None:
            self.load_model()

        k = min(top_k or FAISS_SEARCH_K, self.index.ntotal)

        query_vec = self.model.encode(
            [query_text],
            normalize_embeddings=True,
        ).astype(np.float32)

        scores, indices = self.index.search(query_vec, k)

        results = []
        for i in range(len(indices[0])):
            idx = int(indices[0][i])
            if idx < 0 or idx >= len(self.id_map):
                continue
            # Convert FAISS L2 squared distance to Cosine Similarity
            # L2^2 = 2 - 2*cos_sim  =>  cos_sim = 1 - (L2^2 / 2)
            l2_sq = float(scores[0][i])
            cosine_sim = 1.0 - (l2_sq / 2.0)
            
            # Floor to 0.0 to avoid negative score visual bugs in UI
            cosine_sim = max(0.0, cosine_sim)
            results.append((self.id_map[idx], cosine_sim))
        
        # Sort descending by cosine similarity (highest is best)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def search_by_vector(self, vector: np.ndarray, top_k: int = None) -> list:
        """
        Search by a pre-computed vector (for entity similarity search).

        Returns list of (alumnus_id, score) tuples.
        """
        k = min(top_k or FAISS_SEARCH_K, self.index.ntotal)

        if vector.ndim == 1:
            vector = vector.reshape(1, -1)
        vector = vector.astype(np.float32)

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        scores, indices = self.index.search(vector, k)

        results = []
        for i in range(len(indices[0])):
            idx = int(indices[0][i])
            if idx < 0 or idx >= len(self.id_map):
                continue
            # Convert FAISS L2 squared distance to Cosine Similarity
            l2_sq = float(scores[0][i])
            cosine_sim = 1.0 - (l2_sq / 2.0)
            cosine_sim = max(0.0, cosine_sim)
            results.append((self.id_map[idx], cosine_sim))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_embedding_by_id(self, alumnus_id: str) -> np.ndarray:
        """Get the embedding vector for a specific alumni by their string ID."""
        if alumnus_id in self.id_map:
            idx = self.id_map.index(alumnus_id)
            return self.embeddings[idx]
        return None

    def search_by_ids(self, query_text: str, allowed_ids: list) -> list:
        """
        Compute similarity scores directly against a specific list of candidate IDs.
        Useful when the candidate pool has been heavily filtered and we want to 
        bypass FAISS ANN to guarantee 100% recall of the filtered subset.
        """
        if self.model is None:
            self.load_model()

        query_vec = self.model.encode(
            [query_text],
            normalize_embeddings=True,
        ).astype(np.float32)[0]

        results = []
        for aid in allowed_ids:
            if aid in self.id_map:
                idx = self.id_map.index(aid)
                vec = self.embeddings[idx]
                score = float(np.dot(query_vec, vec))
                results.append((aid, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results


# ---------------------------------------------------------------------------
# Cross-Encoder Reranker  (PRD §3.4)
# ---------------------------------------------------------------------------

class CrossEncoderReranker:
    """
    Reranks FAISS candidates using a cross-encoder for higher precision.

    Pipeline:
      FAISS top-50 candidates → cross-encoder rescores all 50 → return top-K

    Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (~100MB, downloaded once).
    """

    def __init__(self):
        self.model = None
        self._model_name = CROSS_ENCODER_MODEL

    def load_model(self):
        """Load the cross-encoder model at startup."""
        from sentence_transformers import CrossEncoder
        print(f"Loading cross-encoder model: {self._model_name}…")
        self.model = CrossEncoder(self._model_name)
        print("Cross-encoder model loaded.")

    def rerank(self, query: str, candidates: list) -> list:
        """
        Rerank a list of candidate profile dicts by cross-encoder score.

        Parameters
        ----------
        query      : Original search query string.
        candidates : List of dicts, each containing at least 'profile' with
                     'full_name', 'current_company', 'skills_list', 'bio'.

        Returns
        -------
        Candidates sorted by cross-encoder score (descending).
        Each candidate gets a 'cross_encoder_score' key added.
        """
        if self.model is None or not candidates:
            # No-op: return candidates unchanged with None scores
            for c in candidates:
                c["cross_encoder_score"] = None
            return candidates

        pairs = []
        for cand in candidates:
            profile = cand.get("profile", {})
            profile_text = (
                f"{profile.get('full_name', '')} "
                f"{profile.get('current_role', '')} at {profile.get('current_company', '')}. "
                f"Skills: {', '.join(profile.get('skills_list', profile.get('skills', [])))}. "
                f"{profile.get('bio', '')}"
            )
            pairs.append((query, profile_text))

        scores = self.model.predict(pairs)

        for cand, score in zip(candidates, scores):
            cand["cross_encoder_score"] = float(score)

        candidates.sort(key=lambda c: c["cross_encoder_score"], reverse=True)
        return candidates
