"""
Graph Builder — Constructs a NetworkX property graph from alumni data
with centrality scoring and neighbor traversal.
"""
import networkx as nx
import pandas as pd
import pickle
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GRAPH_PATH


class AlumniGraph:
    """
    NetworkX-based property graph for alumni relationships.
    
    Node types: alumni, company, skill, department, batch, location, mentor
    Edge types: WORKS_AT, HAS_SKILL, IN_DEPARTMENT, SAME_BATCH, LIVES_IN, MENTORED_BY
    """

    def __init__(self):
        self.graph = nx.Graph()
        self.alumni_ids = set()
        self.centrality_scores = {}
        self._entity_index = {
            "companies": {},  # company_name -> node_id
            "skills": {},
            "departments": {},
            "batches": {},
            "locations": {},
            "mentors": {},
        }

    def build_from_dataframe(self, df: pd.DataFrame):
        """Build the full graph from a normalized alumni DataFrame."""
        print("Building alumni graph...")

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

            # --- Company node + edge ---
            company = row["current_company"]
            cid = f"company_{company.lower().replace(' ', '_')}"
            if not self.graph.has_node(cid):
                self.graph.add_node(cid, node_type="company", name=company)
                self._entity_index["companies"][company.lower()] = cid
            self.graph.add_edge(aid, cid, relation="WORKS_AT")

            # --- Skill nodes + edges ---
            for skill in row.get("skills_list", []):
                sid = f"skill_{skill.lower().replace(' ', '_')}"
                if not self.graph.has_node(sid):
                    self.graph.add_node(sid, node_type="skill", name=skill)
                    self._entity_index["skills"][skill.lower()] = sid
                self.graph.add_edge(aid, sid, relation="HAS_SKILL")

            # --- Department node + edge ---
            dept = row["department"]
            did = f"dept_{dept.lower().replace(' ', '_').replace('&', 'and')}"
            if not self.graph.has_node(did):
                self.graph.add_node(did, node_type="department", name=dept)
                self._entity_index["departments"][dept.lower()] = did
            self.graph.add_edge(aid, did, relation="IN_DEPARTMENT")

            # --- Batch node + edge ---
            batch = row["batch_year"]
            bid = f"batch_{batch}"
            if not self.graph.has_node(bid):
                self.graph.add_node(bid, node_type="batch", name=str(batch), year=batch)
                self._entity_index["batches"][str(batch)] = bid
            self.graph.add_edge(aid, bid, relation="SAME_BATCH")

            # --- Location node + edge ---
            city = row["city"]
            lid = f"loc_{city.lower().replace(' ', '_')}"
            if not self.graph.has_node(lid):
                self.graph.add_node(lid, node_type="location", name=city)
                self._entity_index["locations"][city.lower()] = lid
            self.graph.add_edge(aid, lid, relation="LIVES_IN")

            # --- Mentor node + edge ---
            mentor = row.get("mentor_id", "")
            if mentor and mentor.strip():
                mid = f"mentor_{mentor.lower().replace(' ', '_').replace('.', '')}"
                if not self.graph.has_node(mid):
                    self.graph.add_node(mid, node_type="mentor", name=mentor)
                    self._entity_index["mentors"][mentor.lower()] = mid
                self.graph.add_edge(aid, mid, relation="MENTORED_BY")

        # --- Compute centrality ---
        self._compute_centrality()

        node_counts = {}
        for _, data in self.graph.nodes(data=True):
            nt = data.get("node_type", "unknown")
            node_counts[nt] = node_counts.get(nt, 0) + 1

        print(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        for nt, count in sorted(node_counts.items()):
            print(f"  {nt}: {count}")

    def _compute_centrality(self):
        """Compute PageRank and store as node attribute."""
        print("Computing graph centrality scores...")
        pr = nx.pagerank(self.graph, alpha=0.85)
        self.centrality_scores = pr

        # Normalize to [0, 1]
        max_pr = max(pr.values()) if pr else 1.0
        for node_id, score in pr.items():
            self.graph.nodes[node_id]["centrality"] = score / max_pr

    def get_centrality(self, alumni_node_id: str) -> float:
        """Get normalized centrality score for an alumni node."""
        return self.graph.nodes.get(alumni_node_id, {}).get("centrality", 0.0)

    def get_entity_node_ids(self, entities: dict) -> list:
        """
        Given extracted entities from a query, find matching graph node IDs.
        
        Args:
            entities: dict with keys 'companies', 'skills', 'batches', 'departments'
        
        Returns:
            List of matching node IDs in the graph.
        """
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

    def compute_graph_score(self, alumni_node_id: str, query_entity_node_ids: list,
                            other_candidate_ids: list = None) -> float:
        """
        Compute a graph-based relevance score for a candidate alumni node.
        
        Score components:
        1. Centrality (PageRank) — how important this alumnus is in the network
        2. Entity overlap — shared connections with query-mentioned entities
        3. Relationship density — connections to other top candidates
        """
        if alumni_node_id not in self.graph:
            return 0.0

        # 1. Centrality score (normalized 0-1)
        centrality = self.get_centrality(alumni_node_id)

        # 2. Entity overlap — count how many query entities this alumni is connected to
        entity_overlap = 0
        alumni_neighbors = set(self.graph.neighbors(alumni_node_id))

        for entity_nid in query_entity_node_ids:
            if entity_nid in alumni_neighbors:
                entity_overlap += 1
            else:
                # Check 2-hop connectivity
                if entity_nid in self.graph:
                    entity_neighbors = set(self.graph.neighbors(entity_nid))
                    if alumni_neighbors & entity_neighbors:
                        entity_overlap += 0.5

        # Normalize entity overlap
        max_entities = max(len(query_entity_node_ids), 1)
        entity_score = min(entity_overlap / max_entities, 1.0)

        # 3. Relationship density — connections to other top candidates
        density_score = 0.0
        if other_candidate_ids:
            shared = 0
            for other_id in other_candidate_ids:
                if other_id == alumni_node_id:
                    continue
                if other_id in self.graph:
                    other_neighbors = set(self.graph.neighbors(other_id))
                    if alumni_neighbors & other_neighbors:
                        shared += 1
            density_score = min(shared / max(len(other_candidate_ids), 1), 1.0)

        # Weighted combination
        from config import CENTRALITY_WEIGHT, ENTITY_OVERLAP_WEIGHT, RELATIONSHIP_DENSITY_WEIGHT
        score = (
            CENTRALITY_WEIGHT * centrality +
            ENTITY_OVERLAP_WEIGHT * entity_score +
            RELATIONSHIP_DENSITY_WEIGHT * density_score
        )

        return round(score, 6)

    def get_neighborhood(self, alumni_node_id: str, max_hops: int = 2) -> dict:
        """
        Get the graph neighborhood of an alumni node for vis.js rendering.
        
        Returns dict with 'nodes' and 'edges' lists in vis.js format.
        """
        if alumni_node_id not in self.graph:
            return {"nodes": [], "edges": [], "center_id": alumni_node_id}

        # BFS to collect nodes within max_hops
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

        # Limit nodes for performance
        if len(all_nodes) > 80:
            # Keep center + 1-hop neighbors + limited 2-hop
            one_hop = [alumni_node_id] + list(self.graph.neighbors(alumni_node_id))
            all_nodes = one_hop[:80]
            visited = set(all_nodes)

        # Color mapping for node types
        color_map = {
            "alumni": {"background": "#6366f1", "border": "#4f46e5"},
            "company": {"background": "#f59e0b", "border": "#d97706"},
            "skill": {"background": "#10b981", "border": "#059669"},
            "department": {"background": "#8b5cf6", "border": "#7c3aed"},
            "batch": {"background": "#3b82f6", "border": "#2563eb"},
            "location": {"background": "#ef4444", "border": "#dc2626"},
            "mentor": {"background": "#ec4899", "border": "#db2777"},
        }

        size_map = {
            "alumni": 25,
            "company": 20,
            "skill": 15,
            "department": 18,
            "batch": 18,
            "location": 16,
            "mentor": 20,
        }

        nodes = []
        edges = []

        for nid in all_nodes:
            data = self.graph.nodes[nid]
            node_type = data.get("node_type", "unknown")
            label = data.get("name", nid)

            # Tooltip
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

            # Highlight center node
            if nid == alumni_node_id:
                node["size"] = 35
                node["borderWidth"] = 3
                node["font"] = {"size": 16, "bold": True, "color": "#ffffff"}

            nodes.append(node)

        # Collect edges between visible nodes
        for nid in all_nodes:
            for neighbor in self.graph.neighbors(nid):
                if neighbor in visited:
                    edge_data = self.graph.edges[nid, neighbor]
                    relation = edge_data.get("relation", "CONNECTED")
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
                            "color": {"color": "#475569", "opacity": 0.6},
                            "font": {"size": 9, "color": "#94a3b8", "strokeWidth": 0},
                        })

        return {
            "nodes": nodes,
            "edges": edges,
            "center_id": alumni_node_id,
        }

    def get_alumni_by_name(self, name: str) -> str:
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

        # Build vis.js data for the path and immediate surroundings
        node_colors = {
            "alumni": "#6366f1", "company": "#f59e0b", "skill": "#10b981",
            "department": "#8b5cf6", "batch": "#3b82f6", "location": "#ef4444",
            "mentor": "#ec4899",
        }
        node_shapes = {"alumni": "dot", "company": "diamond"}

        path_set = set(path)
        nodes = []
        edges = []
        seen_nodes = set()

        for nid in path:
            if nid not in seen_nodes:
                seen_nodes.add(nid)
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
                "label": edge_data.get("relationship", ""),
                "color": {"color": "#f59e0b", "opacity": 0.9},
                "width": 3,
            })

        # Add context nodes (1-hop neighbors of path nodes that are alumni)
        for nid in list(path_set):
            for neighbor in self.graph.neighbors(nid):
                if neighbor not in seen_nodes:
                    nd = self.graph.nodes[neighbor]
                    ntype = nd.get("node_type", "unknown")
                    # Only add alumni neighbors for context (limit to prevent clutter)
                    if ntype == "alumni" and len(seen_nodes) < 30:
                        seen_nodes.add(neighbor)
                        nodes.append({
                            "id": neighbor,
                            "label": nd.get("name", neighbor),
                            "group": ntype,
                            "color": "#475569",
                            "shape": "dot",
                            "size": 10,
                            "font": {"color": "#94a3b8", "size": 9},
                        })
                        edge_data = self.graph.edges.get((nid, neighbor), {})
                        edges.append({
                            "from": nid,
                            "to": neighbor,
                            "color": {"color": "#334155", "opacity": 0.3},
                            "width": 1,
                        })

        path_names = []
        for nid in path:
            nd = self.graph.nodes[nid]
            path_names.append(nd.get("name", nid))

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
            "companies": list(self._entity_index["companies"].keys()),
            "skills": list(self._entity_index["skills"].keys()),
            "departments": list(self._entity_index["departments"].keys()),
            "batches": list(self._entity_index["batches"].keys()),
            "locations": list(self._entity_index["locations"].keys()),
            "mentors": list(self._entity_index["mentors"].keys()),
        }

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
