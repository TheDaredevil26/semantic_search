"""
Conversational Multi-Turn Search Engine — rule-based stub.

Key design: STATELESS per-request. All conversation state lives on the
client (frontend sends conversation_history with every request).
The server just resolves the current turn against the provided history.

This avoids cross-user session contamination when deployed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Turn:
    role: str   # "user" | "assistant"
    content: str


@dataclass
class ConversationalResult:
    """Output of resolve_turn()."""
    resolved_query: str
    company_filter: Optional[str] = None
    location_filter: Optional[str] = None
    batch_year_filter: Optional[str] = None
    skills_filter: List[str] = field(default_factory=list)
    intent: str = "SEMANTIC"


# ---------------------------------------------------------------------------
# Regex patterns (order matters — more specific first)
# ---------------------------------------------------------------------------

# Batch year: single year OR range variants
# Captures: "batch 2015", "2015 batch", "graduated 2019",
#           "from 2015 to 2020", "2015-2020", "between 2015 and 2020",
#           "after 2015", "before 2020", "since 2018",
#           "show me 2018", "only 2019", "change to 2020"
_BATCH_SINGLE = re.compile(
    r"\b(?:"
    r"batch\s+(\d{4})"
    r"|(\d{4})\s+batch"
    r"|graduated?\s+(?:in\s+)?(\d{4})"
    # Filter-command + bare year: 'show me 2018', 'only 2019', 'change to 2020', 'update to 2021'
    r"|(?:show(?:\s+me)?|only|just|change\s+to|update\s+to|make\s+it|now\s+only)\s+(\d{4})"
    r")",
    re.I,
)
_BATCH_RANGE = re.compile(
    r"\b(?:"
    r"(?:batch(?:es)?\s+)?(?:from\s+)?(\d{4})\s*(?:to|-|through|thru)\s*(\d{4})"  # "from 2015 to 2020", "2015-2020"
    r"|between\s+(\d{4})\s+and\s+(\d{4})"                                           # "between 2015 and 2020"
    r")",
    re.I,
)
_BATCH_OPEN = re.compile(
    r"\b(?:"
    r"(?:after|since|from)\s+(\d{4})"   # captured in group 1
    r"|(?:before|until|up\s+to)\s+(\d{4})"  # captured in group 2
    r"|(?:from\s+)?(\d{4})\s*onwards?"  # captured in group 3
    r")",
    re.I,
)

# Shared transition keywords that terminate a filter value match
_BREAK_WORDS = (
    r"at|in|from|with|who|skilled|knowing|batch|company|dept|department|"
    r"onwards?|between|and|or|joined|living|located|based"
)
_BREAKER = rf"(?:\s+(?:{_BREAK_WORDS})|[,.]|$)"

# Location: "in X" / "based in X" / "located in X" / "from X"
# Captures lists e.g., "from Delhi, Mumbai and Bangalore"
_LOCATION_PATTERN = re.compile(
    rf"\b(?:in|based in|located in|living in|from)\s+([A-Za-z\'\s,]+?(?:\s+(?:and|or)\s+[A-Za-z\'\s]+?)?)(?={_BREAKER})",
    re.I
)

# Words that must never be treated as location names
_LOCATION_DENY = {
    "batch", "batches", "that", "the", "a", "an", "my", "our", "onwards",
    "this", "all", "india", "us", "uk", "usa",
    "cs", "it", "ece", "eee", "mech", "civil", "chemical", "biotech",
    "ai", "ml", "ds", "nlp", "cv", "cloud", "devops",
    "computer science", "information technology", "electronics", "communication",
    "electronics & communication", "biotechnology", "electrical engineering", 
    "mechanical engineering", "chemical engineering", "civil engineering",
    "department", "dept", "engineering", "development", "data science",
    "machine learning", "artificial intelligence"
}

# Whitelist of cities to catch mentions WITHOUT an "in/from" prefix
_KNOWN_CITIES = {
    "hyderabad", "chennai", "bangalore", "mumbai", "pune", "toronto", "dublin", 
    "coimbatore", "seattle", "singapore", "noida", "kolkata", "berlin", "kochi", 
    "chandigarh", "san francisco", "jaipur", "ahmedabad", "delhi ncr", "tokyo", 
    "gurgaon", "amsterdam", "indore", "london", "new york", "delhi", "new delhi"
}
_NAKED_LOCATION = re.compile(
    rf"\b({'|'.join(re.escape(c) for c in _KNOWN_CITIES)})\b",
    re.I
)

# Company: "at X" / "working at X" / "filter to X" / "at company X"
_COMPANY_PATTERN = re.compile(
    rf"\b(?:(?:working\s+at|joined|at(?:\s+company)?|filter\s+(?:to|by)|company)\s+)([A-Z][A-Za-z0-9 &.]{{0,40}}?)(?={_BREAKER})",
    re.I
)

# Skills: "with Python", "who know X", "skilled in X", "using X"
_SKILL_PATTERN = re.compile(
    rf"\b(?:with|knows?|knowing|skilled\s+in|using|who\s+knows?|expertise\s+in|skills?(?:\s+in|\s+are)?)\s+([A-Za-z0-9.# +,]+?(?:\s+(?:and|or)\s+[A-Za-z0-9.# +]+?)?)(?={_BREAKER})",
    re.I
)

# Conversational reset signals
_RESET_KEYWORDS = {
    "new search", "start over", "clear", "reset", "forget",
    "something different", "ignore that", "never mind",
}

# Short follow-up signals
_FOLLOW_UP_PREFIXES = re.compile(
    r"^(?:also|and|but|now|then|additionally|what about|how about|"
    r"filter|narrow|show|only|just|from|in|at|with|who|same)\b",
    re.I
)

# Topic-shift phrases where the user provides a new semantic topic but wants to keep filters
_TOPIC_SHIFT = re.compile(
    r"^(?:also(?:\s+try|\s+find)?|what\s+about|how\s+about|show\s+me|find(?:\s+me)?|search(?:\s+for)?|instead(?:\s+try)?|or\s+maybe)\s+(.+)",
    re.I
)

def _clean_topic_shift(query: str) -> str:
    """If query is a topic shift like 'what about managers', strip the prefix so FAISS gets a clean query."""
    m = _TOPIC_SHIFT.match(query.strip())
    if m:
        return m.group(1).strip()
    return ""


# ---------------------------------------------------------------------------
# Core resolver (stateless — takes full history as input)
# ---------------------------------------------------------------------------

def _is_reset(query: str) -> bool:
    q = query.lower().strip()
    return any(kw in q for kw in _RESET_KEYWORDS)


def _is_follow_up(query: str) -> bool:
    """Heuristic: is this query a narrowing follow-up vs a fresh search?

    A query is a follow-up if:
    - It's very short (<=2 words) — pure filter additions like 'in Bangalore'
    - It starts with a known follow-up prefix word and is <=5 words
    - It contains ONLY filter-like patterns (company/location/batch) with no topic noun

    Intentionally conservative: 3-word queries like 'Find ML engineers' are NOT follow-ups.
    """
    q = query.strip()
    words = q.split()

    # <=2-word queries are always follow-ups
    if len(words) <= 2:
        return True

    # Explicit filter-only patterns regardless of length
    _FILTER_ONLY = re.compile(
        r"^(?:"
        r"(?:working\s+at|at\s+company|filter\s+(?:to|by)|only\s+from|only\s+at)\s+\S"
        r"|(?:from|in)\s+\d{4}"                            # "from 2019", "in 2020"
        r"|batch\s+\d{4}"                                  # "batch 2019"
        r"|\d{4}\s+batch"                                  # "2019 batch"
        r"|\d{4}\s*(?:to|-|through)\s*\d{4}"              # "2015 to 2020"
        r"|batch(?:es)?\s+from\s+\d{4}"                   # "batches from 2015 to 2020"
        r"|between\s+\d{4}"                                # "between 2015 and 2020"
        r"|after\s+\d{4}|before\s+\d{4}|since\s+\d{4}"   # open ranges
        # Slot-only overrides: "show me 2018", "only 2019", "change to 2020" etc.
        r"|(?:show(?:\s+me)?|only|just|make\s+it|change\s+to|update\s+to|now\s+only)\s+\d{4}"
        r"|(?:show(?:\s+me)?|only|just)\s+(?:from\s+)?\d{4}(?:\s+(?:to|through|-)\s+\d{4})?"
        r"|only\s+(?:batch\s+)?\d{4}"
        r")",
        re.I,
    )
    if _FILTER_ONLY.match(q):
        return True

    # If it is a clear topic shift (e.g. "what about managers"), it is NOT a pure-filter follow-up
    if _TOPIC_SHIFT.match(q):
        return False

    # Starts with a follow-up prefix AND is short enough to be a filter addition
    if len(words) <= 5 and _FOLLOW_UP_PREFIXES.match(q):
        return True

    return False


def _extract_slots_from_query(query: str) -> dict:
    """
    Extract structured slots from a single query string.
    Returns dict with keys: company, location, batch_year, skills.

    batch_year is returned as a string understood by _parse_batch_filter:
      "2019"       — single year
      "2015-2020"  — inclusive range
    """
    slots = {"company": None, "location": None, "batch_year": None, "skills": []}

    # Batch year — check range first, then open-ended, then single
    m_range = _BATCH_RANGE.search(query)
    m_open  = _BATCH_OPEN.search(query)
    m_single = _BATCH_SINGLE.search(query)

    if m_range:
        # Closed range: either "X to Y" (groups 1,2) or "between X and Y" (groups 3,4)
        g = m_range.groups()
        lo = g[0] or g[2]
        hi = g[1] or g[3]
        if lo and hi:
            lo_i, hi_i = int(lo), int(hi)
            slots["batch_year"] = f"{min(lo_i,hi_i)}-{max(lo_i,hi_i)}"
    elif m_open:
        g = m_open.groups()
        after_year  = g[0]  # "after/since/from X"
        before_year = g[1]  # "before/until X"
        onwards_year = g[2] # "X onwards"
        current_year = 2025
        if after_year:
            slots["batch_year"] = f"{after_year}-{current_year}"
        elif before_year:
            slots["batch_year"] = f"2000-{before_year}"
        elif onwards_year:
            slots["batch_year"] = f"{onwards_year}-{current_year}"
    elif m_single:
        year = next((g for g in m_single.groups() if g), None)
        if year:
            slots["batch_year"] = year.strip()

    # 1. Skills (Explicit prefixes)
    for m in _SKILL_PATTERN.finditer(query):
        skill_raw = m.group(1).strip()
        parts = re.split(r'\s*(?:\b(?:and|or)\b|,)\s*', skill_raw, flags=re.I)
        for p in parts:
            p = p.strip()
            if p and len(p) > 1 and p not in slots["skills"]:
                slots["skills"].append(p)

    # 2. Company
    m = _COMPANY_PATTERN.search(query)
    if m:
        val = m.group(1).strip()
        _COMPANY_REJECT = {"the", "a", "an", "me", "us", "my", "our", "it", "this", "that", "all"}
        if val and len(val) > 1 and val.lower() not in _COMPANY_REJECT:
            slots["company"] = val.title()

    # 3. Location (run after company to avoid double-matches)
    valid_parts = []
    
    # A. Search for "in/from X"
    for m in _LOCATION_PATTERN.finditer(query):
        raw_val = m.group(1).strip().title()
        parts = re.split(r'\s*(?:\b(?:and|or)\b|,)\s*', raw_val, flags=re.I)
        for p in parts:
            p = p.strip()
            p_clean = re.sub(r'^(the|a|an)\s+', '', p.lower()).strip()
            p_clean = re.sub(r'\s+(department|dept)$', '', p_clean).strip()
            
            # If it matches a technical term in the denylist, move it to skills if not already there
            if p_clean in _LOCATION_DENY:
                if len(p_clean) > 1 and p_clean not in ["the", "a", "an", "in", "at"]:
                    # Clean the skill name (strip 'the', 'a' etc)
                    skill_name = p.title()
                    skill_name = re.sub(r'^(The|A|An)\s+', '', skill_name).strip()
                    if skill_name.lower() not in [s.lower() for s in slots["skills"]]:
                        slots["skills"].append(skill_name)
                continue

            if p and len(p) > 1 and p != slots.get("company"):
                valid_parts.append(p)

    # B. Search for "naked" locations (whitelist)
    if not valid_parts:
        for m in _NAKED_LOCATION.finditer(query):
            city = m.group(1).strip().title()
            if city != slots.get("company") and city.lower() not in [s.lower() for s in slots["skills"]]:
                valid_parts.append(city)
                
    if valid_parts:
        slots["location"] = "|".join(dict.fromkeys(valid_parts))

    return slots


def resolve_turn(query: str, history: List[Turn]) -> ConversationalResult:
    """
    Stateless resolver: given the current query + full conversation history,
    produce a ConversationalResult with accumulated filter state.

    Steps:
    1. Replay history to accumulate filter state up to this point.
    2. Extract slots from the current query.
    3. Merge: new slots override inherited slots; inherited slots fill gaps.
    4. Decide the resolved_query (use prior base query if this is a follow-up).
    """
    if _is_reset(query):
        return ConversationalResult(resolved_query=query)

    # --- Step 1: Replay prior user turns to build inherited state ---
    inherited = ConversationalResult(resolved_query="")
    base_query = ""

    for turn in history:
        if turn.role != "user":
            continue
        prior_slots = _extract_slots_from_query(turn.content)
        if not _is_follow_up(turn.content):
            # The query wasn't a pure filter follow-up.
            # Could be a clean topic shift (keep filters, change base) or a full fresh reset.
            shifted_topic = _clean_topic_shift(turn.content)
            if shifted_topic:
                # It's a topic shift: e.g. "what about managers" -> "managers"
                base_query = shifted_topic
                # We optionally let it inherit previous filters, so do NOT reset `inherited` here.
            else:
                # Full fresh search: completely wipe filters and establish new base
                base_query = turn.content
                inherited = ConversationalResult(resolved_query=base_query)

        # Merge slots from this prior turn
        if prior_slots["company"]:
            inherited.company_filter = prior_slots["company"]
        if prior_slots["location"]:
            inherited.location_filter = prior_slots["location"]
        if prior_slots["batch_year"]:
            inherited.batch_year_filter = prior_slots["batch_year"]
        for s in prior_slots["skills"]:
            if s.lower() not in [x.lower() for x in inherited.skills_filter]:
                inherited.skills_filter.append(s)

    if not base_query:
        base_query = query  # No prior history — this IS the base

    # --- Step 2: Extract slots from the current query ---
    current_slots = _extract_slots_from_query(query)

    # --- Step 3: Decide resolved_query ---
    if _is_follow_up(query):
        resolved_query = base_query  # Pure filter extension -> keep base topic
    else:
        shifted_topic = _clean_topic_shift(query)
        if shifted_topic:
            resolved_query = shifted_topic  # Topic shift -> update topic, keep filters
        else:
            resolved_query = query          # Fresh search -> new topic

    # --- Step 4: Merge (current overrides inherited) ---
    company    = current_slots["company"]    or inherited.company_filter
    location   = current_slots["location"]   or inherited.location_filter
    batch_year = current_slots["batch_year"] or inherited.batch_year_filter
    skills     = list(inherited.skills_filter)
    for s in current_slots["skills"]:
        if s.lower() not in [x.lower() for x in skills]:
            skills.append(s)

    intent = "SEMANTIC"
    if any([company, location, batch_year, skills]):
        intent = "STRUCTURED"

    return ConversationalResult(
        resolved_query=resolved_query,
        company_filter=company,
        location_filter=location,
        batch_year_filter=batch_year,
        skills_filter=skills,
        intent=intent,
    )


# ---------------------------------------------------------------------------
# ConversationalSearchEngine (thin wrapper, now stateless by default)
# ---------------------------------------------------------------------------

class ConversationalSearchEngine:
    """
    Thin wrapper around resolve_turn().

    Kept as a class so callers using the old handle_turn() API still work.
    State is now CLIENT-SIDE: the frontend sends conversation_history on every
    request; the server replays it to reconstruct filter state.

    llm_backend: "none" | "openai" | "local"
    """

    def __init__(self, llm_backend: str = "none"):
        self.llm_backend = llm_backend

    def handle_turn(self, query: str, history: Optional[List[Turn]] = None) -> ConversationalResult:
        """
        Stateless resolution: replay history to accumulate filter state.
        Falls back to LLM adapters if configured.
        """
        history = history or []

        if self.llm_backend == "openai":
            try:
                return self._resolve_openai(query, history)
            except Exception as e:
                print(f"[ConversationalSearch] OpenAI failed ({e}), using rule-based fallback")

        elif self.llm_backend == "local":
            try:
                return self._resolve_local(query, history)
            except Exception as e:
                print(f"[ConversationalSearch] Local LLM failed ({e}), using rule-based fallback")

        return resolve_turn(query, history)

    def reset(self):
        """No-op — state is now client-side."""
        pass

    # ------------------------------------------------------------------
    # LLM adapters
    # ------------------------------------------------------------------

    def _resolve_openai(self, query: str, history: List[Turn]) -> ConversationalResult:
        import os, json, openai

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        client = openai.OpenAI(api_key=api_key)
        system_prompt = (
            "You are a search query resolver for an alumni network. "
            "Given a conversation history and a new user query, output a JSON with:\n"
            "  resolved_query: the core search topic (string)\n"
            "  company_filter: company name or null\n"
            "  location_filter: city name or null\n"
            "  batch_year_filter: graduation year as string or null\n"
            "  skills_filter: list of skills (may be empty)\n"
            "  intent: one of SEMANTIC, STRUCTURED, GRAPH\n"
            "Only output valid JSON."
        )
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-8:]:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        data = json.loads(response.choices[0].message.content)
        return ConversationalResult(
            resolved_query=data.get("resolved_query", query),
            company_filter=data.get("company_filter"),
            location_filter=data.get("location_filter"),
            batch_year_filter=data.get("batch_year_filter"),
            skills_filter=data.get("skills_filter", []),
            intent=data.get("intent", "SEMANTIC"),
        )

    def _resolve_local(self, query: str, history: List[Turn]) -> ConversationalResult:
        import sys, os, json
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config import LOCAL_LLM_PATH  # type: ignore
        from llama_cpp import Llama

        llm = Llama(model_path=LOCAL_LLM_PATH, n_ctx=2048, verbose=False)
        history_text = "\n".join(f"{t.role}: {t.content}" for t in history[-6:])
        prompt = (
            f"Conversation:\n{history_text}\nUser: {query}\n\n"
            "Extract search filters as JSON (resolved_query, company_filter, "
            "location_filter, batch_year_filter, skills_filter, intent):\n"
        )
        output = llm(prompt, max_tokens=256, stop=["\n\n"])
        data = json.loads(output["choices"][0]["text"].strip())
        return ConversationalResult(
            resolved_query=data.get("resolved_query", query),
            company_filter=data.get("company_filter"),
            location_filter=data.get("location_filter"),
            batch_year_filter=data.get("batch_year_filter"),
            skills_filter=data.get("skills_filter", []),
            intent=data.get("intent", "SEMANTIC"),
        )
