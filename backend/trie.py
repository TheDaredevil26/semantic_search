"""
Prefix Trie — O(k) autocomplete for alumni names, companies, skills, and locations.
Built once at startup. Replaces the O(n) row-by-row linear scan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    # Each leaf stores a list of suggestion dicts
    suggestions: List[dict] = field(default_factory=list)
    # Limit stored suggestions per node to avoid memory bloat
    MAX_SUGGESTIONS: int = field(default=20, init=False, repr=False)


class AutocompleteTrie:
    """
    Prefix Trie for O(k) autocomplete where k = prefix length.

    Each inserted token stores a suggestion dict:
        { "text": str, "category": str, "icon": str }

    Only lowercase keys are stored for case-insensitive lookup.
    """

    def __init__(self):
        self._root = TrieNode()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def insert(self, token: str, suggestion: dict):
        """Insert a token → suggestion mapping into the trie."""
        token = token.lower().strip()
        if not token:
            return
        node = self._root
        for ch in token:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            if len(node.suggestions) < node.MAX_SUGGESTIONS:
                # Deduplicate by text
                if not any(s["text"] == suggestion["text"] for s in node.suggestions):
                    node.suggestions.append(suggestion)

    def build_from_data(self, df):
        """
        Populate the trie from a pandas DataFrame.

        Indexes:
          - full_name tokens (alumnus names → category "alumni")
          - current_company values → category "company"
          - skills_list items → category "skill"
          - city values → category "location"
          - batch_year values → category "batch"
        """
        # Alumni names — index each word token separately too
        for name in df["full_name"].unique():
            suggestion = {"text": name, "category": "alumni", "icon": "👤"}
            self.insert(name, suggestion)
            for word in name.split():
                if len(word) >= 2:
                    self.insert(word, suggestion)

        # Companies
        for company in df["current_company"].unique():
            suggestion = {"text": company, "category": "company", "icon": "🏢"}
            self.insert(company, suggestion)
            for word in company.split():
                if len(word) >= 3:
                    self.insert(word, suggestion)

        # Skills
        all_skills = set(s for skills in df["skills_list"] for s in skills)
        for skill in all_skills:
            suggestion = {"text": skill, "category": "skill", "icon": "⚡"}
            self.insert(skill, suggestion)
            for word in skill.split():
                if len(word) >= 2:
                    self.insert(word, suggestion)

        # Locations
        for city in df["city"].unique():
            suggestion = {"text": city, "category": "location", "icon": "📍"}
            self.insert(city, suggestion)

        # Batch years
        for year in df["batch_year"].unique():
            suggestion = {"text": str(year), "category": "batch", "icon": "🎓"}
            self.insert(str(year), suggestion)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def search(self, prefix: str, top_k: int = 10) -> List[dict]:
        """
        Return up to top_k suggestion dicts matching the given prefix.

        Args:
            prefix: Query prefix string (case-insensitive).
            top_k:  Maximum number of results.

        Returns:
            List of suggestion dicts, e.g.:
              [{"text": "Google", "category": "company", "icon": "🏢"}, ...]
        """
        prefix = prefix.lower().strip()
        if not prefix:
            return []

        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        # Collect all suggestions from this node (already deduplicated at insert time)
        results = node.suggestions[:top_k]
        return results
