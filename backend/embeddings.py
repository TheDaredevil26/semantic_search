"""
Embeddings Manager — Sentence-BERT encoding and FAISS indexing.
"""
import numpy as np
import faiss
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SBERT_MODEL_NAME, EMBEDDING_DIMENSION,
    EMBEDDINGS_PATH, FAISS_INDEX_PATH, ID_MAP_PATH, FAISS_SEARCH_K
)


class EmbeddingsManager:
    """
    Manages Sentence-BERT embeddings and FAISS index for alumni profiles.
    """

    def __init__(self):
        self.model = None
        self.index = None
        self.id_map = []  # Maps FAISS integer index → alumnus_id
        self.embeddings = None

    def load_model(self):
        """Load the Sentence-BERT model."""
        from sentence_transformers import SentenceTransformer
        print(f"Loading SBERT model: {SBERT_MODEL_NAME}...")
        self.model = SentenceTransformer(SBERT_MODEL_NAME)
        print("SBERT model loaded.")

    def build_index(self, profile_texts: list, alumni_ids: list):
        """
        Embed all profile texts and build a FAISS index.
        
        Args:
            profile_texts: List of profile text blobs.
            alumni_ids: List of corresponding alumnus_id strings.
        """
        if self.model is None:
            self.load_model()

        print(f"Encoding {len(profile_texts)} profiles...")
        self.embeddings = self.model.encode(
            profile_texts,
            normalize_embeddings=True,  # Normalize for cosine similarity
            show_progress_bar=True,
            batch_size=64
        ).astype(np.float32)

        self.id_map = list(alumni_ids)

        # Build FAISS index (IndexFlatIP = cosine similarity with normalized vectors)
        self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
        self.index.add(self.embeddings)

        print(f"FAISS index built with {self.index.ntotal} vectors ({EMBEDDING_DIMENSION}-dim)")

        # Save to disk
        self._save()

    def _save(self):
        """Save embeddings, index, and ID map to disk."""
        os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)

        np.save(EMBEDDINGS_PATH, self.embeddings)
        faiss.write_index(self.index, FAISS_INDEX_PATH)

        with open(ID_MAP_PATH, "w") as f:
            json.dump(self.id_map, f)

        print(f"Saved embeddings, FAISS index, and ID map to cache/")

    def load_from_cache(self) -> bool:
        """
        Attempt to load pre-built embeddings and index from disk.
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        if not all(os.path.exists(p) for p in [EMBEDDINGS_PATH, FAISS_INDEX_PATH, ID_MAP_PATH]):
            return False

        try:
            self.embeddings = np.load(EMBEDDINGS_PATH)
            self.index = faiss.read_index(FAISS_INDEX_PATH)

            with open(ID_MAP_PATH, "r") as f:
                self.id_map = json.load(f)

            print(f"Loaded cached FAISS index with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            print(f"Failed to load cache: {e}")
            return False

    def search(self, query_text: str, top_k: int = None) -> list:
        """
        Embed a query and search for nearest neighbors.
        
        Args:
            query_text: Natural language search query.
            top_k: Number of candidates to retrieve.
        
        Returns:
            List of (alumnus_id, cosine_similarity_score) tuples.
        """
        if self.model is None:
            self.load_model()

        k = top_k or FAISS_SEARCH_K

        # Embed and normalize the query
        query_vec = self.model.encode(
            [query_text],
            normalize_embeddings=True
        ).astype(np.float32)

        # Search FAISS
        scores, indices = self.index.search(query_vec, k)

        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx < 0 or idx >= len(self.id_map):
                continue
            score = float(scores[0][i])
            results.append((self.id_map[idx], score))

        return results

    def get_embedding_by_id(self, alumnus_id: str) -> np.ndarray:
        """Get the embedding vector for a specific alumni."""
        if alumnus_id in self.id_map:
            idx = self.id_map.index(alumnus_id)
            return self.embeddings[idx]
        return None

    def search_by_vector(self, vector: np.ndarray, top_k: int = None) -> list:
        """
        Search by a pre-computed vector (for entity similarity search).
        
        Args:
            vector: 384-dim numpy array.
            top_k: Number of results.
        
        Returns:
            List of (alumnus_id, score) tuples.
        """
        k = top_k or FAISS_SEARCH_K

        # Ensure correct shape and type
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)
        vector = vector.astype(np.float32)

        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        scores, indices = self.index.search(vector, k)

        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx < 0 or idx >= len(self.id_map):
                continue
            score = float(scores[0][i])
            results.append((self.id_map[idx], score))

        return results
