"""
Graph Builder — Constructs a NetworkX weighted property graph from alumni data
with weighted edges, Personalized PageRank, and Node2Vec support.

PRD changes:
  §3.7 — Weighted graph edges (same_company=3.0, same_college=2.0, shared_skill=1.0/skill)
  §3.8 — Personalized PageRank (query-aware seed weights)
  §3.9 — Node2Vec graph embeddings (background thread, optional)
"""
import networkx as nx
import pandas as pd
import pickle
import os
import sys
import threading
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GRAPH_PATH, NODE2VEC_ENABLED, NODE2VEC_DIMENSIONS, NODE2VEC_WALK_LENGTH, NODE2VEC_NUM_WALKS, NODE2VEC_WORKERS


class AlumniGraph:
    """
    NetworkX-based weighted property graph for alumni relationships.

    Node types : alumni, company, skill, department, batch, location, mentor
    Edge types : WORKS_AT, HAS_SKILL, IN_DEPARTMENT, SAME_BATCH, LIVES_IN, MENTORED_BY
    Weighted   : alumni↔alumni edges carry computed weights (§3.7)
    """

    def __init__(self):
        self.graph = nx.Graph()
        self.alumni_ids = set()
        self.centrality_scores = {}
        self._entity_index = {
            "companies": {},    # company_name→node_id
            "skills": {},
            "departments": {},
            "batches": {},
            "locations": {},
            "mentors": {},
        }
        # Node2Vec (§3.9)
        self.node2vec_model = None
        self.node2vec_faiss = None
        self.node2vec_id_map = []
        self.node2vec_ready = False

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_from_dataframe(self, df: pd.DataFrame):
        """Build the full weighted graph from a normalized alumni DataFrame."""
        print("Building weighted alumni graph…")

        # Build per-row lookup structures for O(1) weight computation
        _by_company: dict = {}   # company_name → set of alumni node IDs
        _by_college: dict = {}   # department (used as proxy for college) → set
        _by_skill: dict = {}     # skill → set of alumni node IDs

        for _, row in df.iterrows():
            aid = f"alumni_{row['alumnus_id']}"
            self.alumni_ids.add(aid)

            # --- Alumni node ---
            self.graph.add_node(aid,
                node_type="alumni",
                name=row["full_name"],
                alumnus_id=row["alumnus_id"],
                batch_year=row["batch_year"],
                department=row["department"],
                company=row["current_company"],
                role=row["current_role"],
                city=row["city"],
                skills=row.get("skills_list", []),
                bio=row["bio"],
                mentor_id=row.get("mentor_id", ""),
            )

            # --- Company ---
            company = row["current_company"]
            cid = f"company_{company.lower().replace(' ', '_')}"
            if not self.graph.has_node(cid):
                self.graph.add_node(cid, node_type="company", name=company)
                self._entity_index["companies"][company.lower()] = cid
            self.graph.add_edge(aid, cid, relation="WORKS_AT", weight=1.0)
            _by_company.setdefault(company, set()).add(aid)

            # --- Skills ---
            for skill in row.get("skills_list", []):
                sid = f"skill_{skill.lower().replace(' ', '_')}"
                if not self.graph.has_node(sid):
                    self.graph.add_node(sid, node_type="skill", name=skill)
                    self._entity_index["skills"][skill.lower()] = sid
                self.graph.add_edge(aid, sid, relation="HAS_SKILL", weight=1.0)
                _by_skill.setdefault(skill.lower(), set()).add(aid)

            # --- Department (used as college proxy) ---
            dept = row["department"]
            did = f"dept_{dept.lower().replace(' ', '_').replace('&', 'and')}"
            if not self.graph.has_node(did):
                self.graph.add_node(did, node_type="department", name=dept)
                self._entity_index["departments"][dept.lower()] = did
            self.graph.add_edge(aid, did, relation="IN_DEPARTMENT", weight=1.0)
            _by_college.setdefault(dept, set()).add(aid)

            # --- Batch ---
            batch = row["batch_year"]
            bid = f"batch_{batch}"
            if not self.graph.has_node(bid):
                self.graph.add_node(bid, node_type="batch", name=str(batch), year=batch)
                self._entity_index["batches"][str(batch)] = bid
            self.graph.add_edge(aid, bid, relation="SAME_BATCH", weight=1.0)

            # --- Location ---
            city = row["city"]
            lid = f"loc_{city.lower().replace(' ', '_')}"
            if not self.graph.has_node(lid):
                self.graph.add_node(lid, node_type="location", name=city)
                self._entity_index["locations"][city.lower()] = lid
            self.graph.add_edge(aid, lid, relation="LIVES_IN", weight=1.0)

            # --- Mentor ---
            mentor = row.get("mentor_id", "")
            if mentor and mentor.strip():
                mid = f"mentor_{mentor.lower().replace(' ', '_').replace('.', '')}"
                if not self.graph.has_node(mid):
                    self.graph.add_node(mid, node_type="mentor", name=mentor)
                    self._entity_index["mentors"][mentor.lower()] = mid
                self.graph.add_edge(aid, mid, relation="MENTORED_BY", weight=1.0)

        # --- Add weighted alumni↔alumni edges (PRD §3.7) ---
        print("Adding weighted alumni↔alumni edges…")
        self._add_weighted_alumni_edges(_by_company, _by_college, _by_skill)

        # --- Compute global centrality (PPR computed per-query) ---
        self._compute_centrality()

        node_counts = {}
        for _, data in self.graph.nodes(data=True):
            nt = data.get("node_type", "unknown")
            node_counts[nt] = node_counts.get(nt, 0) + 1

        print(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        for nt, count in sorted(node_counts.items()):
            print(f"  {nt}: {count}")

        # --- Node2Vec in background (PRD §3.9) ---
        if NODE2VEC_ENABLED:
            t = threading.Thread(target=self._build_node2vec, daemon=True)
            t.start()

    def _add_weighted_alumni_edges(
        self,
        by_company: dict,
        by_college: dict,
        by_skill: dict,
    ):
        """
        Add direct weighted edges between alumni nodes.

        Edge weight formula (PRD §3.7):
          same_company  → += 3.0
          same_college  → += 2.0
          shared_skill  → += 1.0 per skill
        """
        # Collect all pairs and their weights
        edge_weights: dict = {}  # (aid1, aid2) → weight

        def _add(aid1, aid2, w):
            key = (min(aid1, aid2), max(aid1, aid2))
            edge_weights[key] = edge_weights.get(key, 0.0) + w

        for group in by_company.values():
            lst = list(group)
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    _add(lst[i], lst[j], 3.0)

        for group in by_college.values():
            lst = list(group)
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    _add(lst[i], lst[j], 2.0)

        for group in by_skill.values():
            lst = list(group)
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    _add(lst[i], lst[j], 1.0)

        for (aid1, aid2), weight in edge_weights.items():
            if self.graph.has_edge(aid1, aid2):
                self.graph[aid1][aid2]["weight"] = max(self.graph[aid1][aid2].get("weight", 0), weight)
            else:
                self.graph.add_edge(aid1, aid2, relation="CONNECTED", weight=weight)

        print(f"  Added {len(edge_weights)} weighted alumni↔alumni edges.")

    # ------------------------------------------------------------------
    # Centrality
    # ------------------------------------------------------------------

    def _compute_centrality(self):
        """Compute global (non-personalized) PageRank for baseline scoring."""
        print("Computing global PageRank centrality…")
        pr = nx.pagerank(self.graph, alpha=0.85, weight="weight")
        self.centrality_scores = pr

        max_pr = max(pr.values()) if pr else 1.0
        for node_id, score in pr.items():
            self.graph.nodes[node_id]["centrality"] = score / max_pr

    def compute_personalized_pagerank(self, query_tokens: list) -> dict:
        """
        Compute Personalized PageRank seeded by query-matching nodes (PRD §3.8).

        Seed logic:
          - Node whose name/company/skills contain any query token → seed=0.8
          - All other nodes → seed=0.2
        Seed dict is normalized to sum=1.0 before passing to nx.pagerank.

        Parameters
        ----------
        query_tokens : List of lowercase query tokens.

        Returns
        -------
        Dict mapping node_id → normalized PPR score (0–1).
        """
        if not query_tokens:
            return self.centrality_scores  # Fall back to global PR

        seed: dict = {}
        for nid in self.graph.nodes:
            data = self.graph.nodes[nid]
            node_type = data.get("node_type", "")
            name = data.get("name", "").lower()
            company = data.get("company", "").lower()
            skills = [s.lower() for s in data.get("skills", [])]

            fields = [name, company] + skills
            matched = any(token in field for token in query_tokens for field in fields if field)
            seed[nid] = 0.8 if matched else 0.2

        # Normalize
        total = sum(seed.values())
        if total > 0:
            seed = {k: v / total for k, v in seed.items()}

        try:
            ppr = nx.pagerank(self.graph, alpha=0.85, personalization=seed, weight="weight")
        except Exception:
            ppr = self.centrality_scores  # Safe fallback

        # Normalize to [0, 1]
        max_ppr = max(ppr.values()) if ppr else 1.0
        return {k: v / max_ppr for k, v in ppr.items()}

    def get_centrality(self, alumni_node_id: str) -> float:
        """Get normalized global centrality score for an alumni node."""
        return self.graph.nodes.get(alumni_node_id, {}).get("centrality", 0.0)

    # ------------------------------------------------------------------
    # Entity look-up
    # ------------------------------------------------------------------

    def get_entity_node_ids(self, entities: dict) -> list:
        """Given extracted entities from a query, find matching graph node IDs."""
        node_ids = []
        for company in entities.get("companies", []):
            nid = self._entity_index["companies"].get(company.lower())
            if nid:
                node_ids.append(nid)
        for skill in entities.get("skills", []):
            nid = self._entity_index["skills"].get(skill.lower())
            if nid:
                node_ids.append(nid)
        for batch in entities.get("batches", []):
            nid = self._entity_index["batches"].get(str(batch))
            if nid:
                node_ids.append(nid)
        for dept in entities.get("departments", []):
            nid = self._entity_index["departments"].get(dept.lower())
            if nid:
                node_ids.append(nid)
        for loc in entities.get("locations", []):
            nid = self._entity_index["locations"].get(loc.lower())
            if nid:
                node_ids.append(nid)
        for mentor in entities.get("mentors", []):
            nid = self._entity_index["mentors"].get(mentor.lower())
            if nid:
                node_ids.append(nid)
        return node_ids

    # ------------------------------------------------------------------
    # Graph scoring
    # ------------------------------------------------------------------

    def compute_graph_score(self, alumni_node_id: str, query_entity_node_ids: list,
                            other_candidate_ids: list = None,
                            ppr_scores: dict = None) -> float:
        """
        Compute a graph-based relevance score for a candidate alumni node.

        Score components:
          1. PPR centrality (personalized if ppr_scores supplied, else global)
          2. Entity overlap — shared connections with query-mentioned entities
          3. Relationship density — connections to other top candidates
        """
        if alumni_node_id not in self.graph:
            return 0.0

        # 1. Centrality
        if ppr_scores:
            centrality = ppr_scores.get(alumni_node_id, 0.0)
        else:
            centrality = self.get_centrality(alumni_node_id)

        # 2. Entity overlap
        entity_overlap = 0.0
        alumni_neighbors = set(self.graph.neighbors(alumni_node_id))
        for entity_nid in query_entity_node_ids:
            if entity_nid in alumni_neighbors:
                entity_overlap += 1
            elif entity_nid in self.graph:
                entity_neighbors = set(self.graph.neighbors(entity_nid))
                if alumni_neighbors & entity_neighbors:
                    entity_overlap += 0.5

        max_entities = max(len(query_entity_node_ids), 1)
        entity_score = min(entity_overlap / max_entities, 1.0)

        # 3. Relationship density
        density_score = 0.0
        if other_candidate_ids:
            shared = sum(
                1 for oid in other_candidate_ids
                if oid != alumni_node_id and oid in self.graph and
                (alumni_neighbors & set(self.graph.neighbors(oid)))
            )
            density_score = min(shared / max(len(other_candidate_ids), 1), 1.0)

        from config import CENTRALITY_WEIGHT, ENTITY_OVERLAP_WEIGHT, RELATIONSHIP_DENSITY_WEIGHT
        score = (
            CENTRALITY_WEIGHT * centrality +
            ENTITY_OVERLAP_WEIGHT * entity_score +
            RELATIONSHIP_DENSITY_WEIGHT * density_score
        )
        return round(score, 6)

    # ------------------------------------------------------------------
    # Node2Vec (PRD §3.9)
    # ------------------------------------------------------------------

    def _build_node2vec(self):
        """
        Build Node2Vec embeddings in a background thread.
        Sets self.node2vec_ready = True when complete.
        """
        try:
            import faiss as _faiss
            from node2vec import Node2Vec  # pip install node2vec

            print("[Node2Vec] Starting background embedding build…")

            # Build on alumni-only subgraph to keep it tractable
            alumni_nodes = list(self.alumni_ids)
            subgraph = self.graph.subgraph(alumni_nodes).copy()

            n2v = Node2Vec(
                subgraph,
                dimensions=NODE2VEC_DIMENSIONS,
                walk_length=NODE2VEC_WALK_LENGTH,
                num_walks=NODE2VEC_NUM_WALKS,
                workers=NODE2VEC_WORKERS,
                quiet=True,
            )
            model = n2v.fit(window=10, min_count=1, batch_words=4)
            self.node2vec_model = model

            # Build a HNSW FAISS index for node embeddings
            vectors = []
            ids = []
            for i, nid in enumerate(alumni_nodes):
                try:
                    vec = model.wv[nid]
                    vectors.append(vec)
                    ids.append(nid)
                except KeyError:
                    pass

            if vectors:
                import numpy as _np
                vecs = _np.array(vectors, dtype=_np.float32)
                # Normalize
                norms = _np.linalg.norm(vecs, axis=1, keepdims=True)
                vecs = vecs / _np.where(norms > 0, norms, 1)

                inner = _faiss.IndexHNSWFlat(NODE2VEC_DIMENSIONS, 16)
                n2v_index = _faiss.IndexIDMap2(inner)
                n2v_index.add_with_ids(vecs, _np.arange(len(ids), dtype=_np.int64))

                self.node2vec_faiss = n2v_index
                self.node2vec_id_map = ids

            self.node2vec_ready = True
            print(f"[Node2Vec] Done — {len(ids)} node embeddings built.")

            # Notify logger
            try:
                from backend.logger import set_node2vec_ready
                set_node2vec_ready(True)
            except Exception:
                pass

        except ImportError:
            print("[Node2Vec] node2vec package not installed — skipping. pip install node2vec to enable.")
        except Exception as e:
            print(f"[Node2Vec] Background build failed: {e}")

    def get_node2vec_similarity(self, query_nid: str, candidate_nids: list) -> dict:
        """
        Return Node2Vec cosine similarity scores for candidates relative to a query node.
        Returns empty dict if Node2Vec is not ready.
        """
        if not self.node2vec_ready or self.node2vec_model is None:
            return {}
        results = {}
        try:
            for nid in candidate_nids:
                try:
                    sim = self.node2vec_model.wv.similarity(query_nid, nid)
                    results[nid] = float(sim)
                except KeyError:
                    results[nid] = 0.0
        except Exception:
            pass
        return results

    # ------------------------------------------------------------------
    # Visualization helpers (unchanged from original)
    # ------------------------------------------------------------------

    def get_neighborhood(self, alumni_node_id: str, max_hops: int = 2) -> dict:
        """Get the graph neighborhood of an alumni node for vis.js rendering."""
        if alumni_node_id not in self.graph:
            return {"nodes": [], "edges": [], "center_id": alumni_node_id}

        visited = {alumni_node_id}
        frontier = [alumni_node_id]
        all_nodes = [alumni_node_id]

        for hop in range(max_hops):
            next_frontier = []
            for node in frontier:
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.append(neighbor)
                        all_nodes.append(neighbor)
            frontier = next_frontier

        if len(all_nodes) > 80:
            one_hop = [alumni_node_id] + list(self.graph.neighbors(alumni_node_id))
            all_nodes = one_hop[:80]
            visited = set(all_nodes)

        color_map = {
            "alumni":    {"background": "#6366f1", "border": "#4f46e5"},
            "company":   {"background": "#f59e0b", "border": "#d97706"},
            "skill":     {"background": "#10b981", "border": "#059669"},
            "department":{"background": "#8b5cf6", "border": "#7c3aed"},
            "batch":     {"background": "#3b82f6", "border": "#2563eb"},
            "location":  {"background": "#ef4444", "border": "#dc2626"},
            "mentor":    {"background": "#ec4899", "border": "#db2777"},
        }
        size_map = {
            "alumni": 25, "company": 20, "skill": 15,
            "department": 18, "batch": 18, "location": 16, "mentor": 20,
        }

        nodes = []
        edges = []

        for nid in all_nodes:
            data = self.graph.nodes[nid]
            node_type = data.get("node_type", "unknown")
            label = data.get("name", nid)

            if node_type == "alumni":
                title = f"{label}<br>{data.get('role', '')} at {data.get('company', '')}<br>Batch {data.get('batch_year', '')}"
            else:
                title = f"{node_type.title()}: {label}"

            node = {
                "id": nid,
                "label": label,
                "group": node_type,
                "title": title,
                "size": size_map.get(node_type, 15),
                "color": color_map.get(node_type, {"background": "#94a3b8", "border": "#64748b"}),
            }
            if nid == alumni_node_id:
                node["size"] = 35
                node["borderWidth"] = 3
                node["font"] = {"size": 16, "bold": True, "color": "#ffffff"}
            nodes.append(node)

        for nid in all_nodes:
            for neighbor in self.graph.neighbors(nid):
                if neighbor in visited:
                    edge_data = self.graph.edges[nid, neighbor]
                    relation = edge_data.get("relation", "CONNECTED")
                    weight = edge_data.get("weight", 1.0)
                    edge_id = tuple(sorted([nid, neighbor]))
                    if not any(
                        (e.get("from") == edge_id[0] and e.get("to") == edge_id[1]) or
                        (e.get("from") == edge_id[1] and e.get("to") == edge_id[0])
                        for e in edges
                    ):
                        edges.append({
                            "from": edge_id[0],
                            "to": edge_id[1],
                            "label": relation,
                            "width": min(weight * 0.5, 5),   # Edge thickness ~ weight
                            "color": {"color": "#475569", "opacity": 0.6},
                            "font": {"size": 9, "color": "#94a3b8", "strokeWidth": 0},
                        })

        return {"nodes": nodes, "edges": edges, "center_id": alumni_node_id}

    def get_alumni_by_name(self, name: str) -> Optional[str]:
        """Find alumni node ID by name (case-insensitive partial match)."""
        name_lower = name.lower()
        for nid in self.alumni_ids:
            node_name = self.graph.nodes[nid].get("name", "").lower()
            if name_lower in node_name or node_name in name_lower:
                return nid
        return None

    def find_path(self, alumni_id_1: int, alumni_id_2: int) -> dict:
        """Find the shortest path between two alumni and return vis.js graph data."""
        node_id_1 = f"alumni_{alumni_id_1}"
        node_id_2 = f"alumni_{alumni_id_2}"

        if node_id_1 not in self.graph or node_id_2 not in self.graph:
            return {"nodes": [], "edges": [], "path": [], "length": -1}

        try:
            path = nx.shortest_path(self.graph, node_id_1, node_id_2)
        except nx.NetworkXNoPath:
            return {"nodes": [], "edges": [], "path": [], "length": -1}

        node_colors = {
            "alumni": "#6366f1", "company": "#f59e0b", "skill": "#10b981",
            "department": "#8b5cf6", "batch": "#3b82f6", "location": "#ef4444",
            "mentor": "#ec4899",
        }
        node_shapes = {"alumni": "dot", "company": "diamond"}
        path_set = set(path)
        nodes, edges, seen = [], [], set()

        for nid in path:
            if nid not in seen:
                seen.add(nid)
                nd = self.graph.nodes[nid]
                ntype = nd.get("node_type", "unknown")
                is_endpoint = (nid == node_id_1 or nid == node_id_2)
                nodes.append({
                    "id": nid,
                    "label": nd.get("name", nid.split("_", 1)[-1] if "_" in nid else nid),
                    "group": ntype,
                    "color": node_colors.get(ntype, "#94a3b8"),
                    "shape": node_shapes.get(ntype, "dot"),
                    "size": 30 if is_endpoint else 18,
                    "font": {"color": "#e8e8f0", "size": 14 if is_endpoint else 11},
                    "borderWidth": 4 if is_endpoint else 2,
                    "shadow": {"enabled": True, "size": 20, "color": "rgba(99,102,241,0.4)"} if is_endpoint else False,
                })

        for i in range(len(path) - 1):
            edge_data = self.graph.edges.get((path[i], path[i + 1]), {})
            edges.append({
                "from": path[i],
                "to": path[i + 1],
                "label": edge_data.get("relation", ""),
                "color": {"color": "#f59e0b", "opacity": 0.9},
                "width": 3,
            })

        for nid in list(path_set):
            for neighbor in self.graph.neighbors(nid):
                if neighbor not in seen:
                    nd = self.graph.nodes[neighbor]
                    ntype = nd.get("node_type", "unknown")
                    if ntype == "alumni" and len(seen) < 30:
                        seen.add(neighbor)
                        nodes.append({
                            "id": neighbor,
                            "label": nd.get("name", neighbor),
                            "group": ntype,
                            "color": "#475569",
                            "shape": "dot",
                            "size": 10,
                            "font": {"color": "#94a3b8", "size": 9},
                        })
                        edges.append({
                            "from": nid,
                            "to": neighbor,
                            "color": {"color": "#334155", "opacity": 0.3},
                            "width": 1,
                        })

        path_names = [self.graph.nodes[nid].get("name", nid) for nid in path]
        return {
            "nodes": nodes,
            "edges": edges,
            "path": path_names,
            "length": len(path) - 1,
            "source": node_id_1,
            "target": node_id_2,
        }

    def get_all_entity_names(self) -> dict:
        """Get all entity names for entity extraction matching."""
        return {
            "companies":   list(self._entity_index["companies"].keys()),
            "skills":      list(self._entity_index["skills"].keys()),
            "departments": list(self._entity_index["departments"].keys()),
            "batches":     list(self._entity_index["batches"].keys()),
            "locations":   list(self._entity_index["locations"].keys()),
            "mentors":     list(self._entity_index["mentors"].keys()),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str = None):
        """Save graph to disk."""
        path = path or GRAPH_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Graph saved to {path}")

    @staticmethod
    def load(path: str = None):
        """Load graph from disk."""
        path = path or GRAPH_PATH
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)
