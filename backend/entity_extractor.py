"""
Entity Extractor — Extracts known entities (skills, companies, batches, etc.)
from natural language queries via keyword matching.
"""
import re


class EntityExtractor:
    """
    Fast keyword-based entity extraction from search queries.
    Matches against known entities in the alumni graph.
    """

    def __init__(self):
        self.known_entities = {
            "companies": [],
            "skills": [],
            "departments": [],
            "batches": [],
            "locations": [],
            "mentors": [],
        }

    def load_entities(self, entity_names: dict):
        """
        Load known entity names from the graph.
        
        Args:
            entity_names: dict with keys matching self.known_entities
        """
        self.known_entities = {
            k: [name.lower() for name in v]
            for k, v in entity_names.items()
        }

    def extract(self, query: str) -> dict:
        """
        Extract entities from a natural language query.
        
        Args:
            query: User's search query string.
        
        Returns:
            dict with keys 'companies', 'skills', 'batches', 'departments',
            'locations', 'mentors', each containing lists of matched values.
        """
        query_lower = query.lower()

        result = {
            "companies": [],
            "skills": [],
            "batches": [],
            "departments": [],
            "locations": [],
            "mentors": [],
        }

        # --- Extract batch years ---
        year_pattern = r'\b(20[0-2][0-9])\b'
        years = re.findall(year_pattern, query)
        for y in years:
            if y in self.known_entities.get("batches", []):
                result["batches"].append(y)

        # --- Extract companies ---
        for company in self.known_entities.get("companies", []):
            if len(company) >= 3 and company in query_lower:
                result["companies"].append(company)

        # --- Extract skills ---
        for skill in self.known_entities.get("skills", []):
            # Skills can be short (e.g., "ML", "AI", "R") — need word boundary
            if len(skill) <= 2:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, query_lower):
                    result["skills"].append(skill)
            elif skill in query_lower:
                result["skills"].append(skill)

        # --- Semantic skill expansion ---
        # Map common query terms to known skills
        skill_synonyms = {
            "machine learning": ["machine learning", "ml"],
            "ml": ["machine learning", "ml"],
            "artificial intelligence": ["machine learning", "deep learning", "natural language processing"],
            "ai": ["machine learning", "deep learning", "natural language processing"],
            "deep learning": ["deep learning", "tensorflow", "pytorch"],
            "data science": ["python", "machine learning", "data analysis", "sql"],
            "web development": ["react", "node.js", "javascript", "html"],
            "frontend": ["react", "javascript", "typescript", "angular"],
            "backend": ["python", "java", "node.js", "sql", "rest apis"],
            "cloud": ["aws", "azure", "cloud computing", "docker", "kubernetes"],
            "devops": ["docker", "kubernetes", "ci/cd", "aws"],
            "nlp": ["natural language processing", "python", "machine learning"],
            "cv": ["computer vision", "deep learning", "python"],
            "product management": ["product manager"],
            "startup": ["founder", "co-founder", "entrepreneur"],
        }

        for term, expansions in skill_synonyms.items():
            if term in query_lower:
                for exp in expansions:
                    if exp in self.known_entities.get("skills", []) and exp not in result["skills"]:
                        result["skills"].append(exp)

        # --- Extract departments ---
        dept_aliases = {
            "computer science": "computer science",
            "cs": "computer science",
            "cse": "computer science",
            "ece": "electronics & communication",
            "electronics": "electronics & communication",
            "mechanical": "mechanical engineering",
            "electrical": "electrical engineering",
            "civil": "civil engineering",
            "it": "information technology",
            "chemical": "chemical engineering",
            "biotech": "biotechnology",
            "biotechnology": "biotechnology",
        }
        for alias, dept in dept_aliases.items():
            if alias in query_lower:
                if dept in self.known_entities.get("departments", []) and dept not in result["departments"]:
                    result["departments"].append(dept)

        # --- Extract locations ---
        for loc in self.known_entities.get("locations", []):
            if len(loc) >= 3 and loc in query_lower:
                result["locations"].append(loc)

        # --- Extract mentors ---
        for mentor in self.known_entities.get("mentors", []):
            if mentor in query_lower:
                result["mentors"].append(mentor)

        return result

    def generate_explanation(self, query: str, profile: dict, vector_score: float,
                             graph_score: float, entities: dict) -> str:
        """
        Generate a human-readable explanation for why a result was returned.
        
        Args:
            query: Original search query.
            profile: Alumni profile dict.
            vector_score: Cosine similarity score.
            graph_score: Graph-based score.
            entities: Extracted entities from query.
        
        Returns:
            Explanation string.
        """
        reasons = []

        # Skill matches
        profile_skills = [s.lower() for s in profile.get("skills_list", [])]
        matched_skills = []
        for skill in entities.get("skills", []):
            for ps in profile_skills:
                if skill in ps or ps in skill:
                    matched_skills.append(ps.title())
                    break
        if matched_skills:
            reasons.append(f"Skills: {', '.join(matched_skills[:4])}")

        # Batch match
        for batch in entities.get("batches", []):
            if str(profile.get("batch_year", "")) == str(batch):
                reasons.append(f"Batch: {batch}")
                break

        # Company match
        company = profile.get("current_company", "").lower()
        for qc in entities.get("companies", []):
            if qc in company:
                reasons.append(f"Company: {profile.get('current_company', '')}")
                break

        # Department match
        dept = profile.get("department", "").lower()
        for qd in entities.get("departments", []):
            if qd in dept:
                reasons.append(f"Dept: {profile.get('department', '')}")
                break

        # Location match
        city = profile.get("city", "").lower()
        for ql in entities.get("locations", []):
            if ql in city:
                reasons.append(f"Location: {profile.get('city', '')}")
                break

        # Role relevance (check if query mentions role-related terms)
        role = profile.get("current_role", "").lower()
        role_terms = ["engineer", "scientist", "manager", "founder", "researcher", 
                       "developer", "analyst", "consultant", "lead", "director"]
        for term in role_terms:
            if term in query.lower() and term in role:
                reasons.append(f"Role: {profile.get('current_role', '')}")
                break

        # Semantic match note
        if vector_score > 0.5:
            reasons.append(f"High semantic similarity ({vector_score:.0%})")
        elif vector_score > 0.3:
            reasons.append(f"Semantic match ({vector_score:.0%})")

        # Graph boost note
        if graph_score > 0.5:
            reasons.append("Strong graph connections")
        elif graph_score > 0.2:
            reasons.append("Related in alumni network")

        if not reasons:
            reasons.append("Profile semantically related to query")

        return " | ".join(reasons)
