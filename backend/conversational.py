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

# Batch year: must be 4-digit number with clear context
_BATCH_PATTERN = re.compile(
    r"\b(?:batch\s+(\d{4})|(\d{4})\s+batch|graduated?\s+(?:in\s+)?(\d{4}))\b", re.I
)

# Location: "in X" / "based in X" / "located in X"
_LOCATION_PATTERN = re.compile(
    r"\b(?:in|based in|located in|from|living in|at)\s+([A-Z][A-Za-z\s]{1,30}?)(?:\s+(?:batch|company|department|from|\d{4})|[,.]|$)",
    re.I
)

# Company: "at X" / "working at X" / "filter to X" / "only X" / "at company X"
_COMPANY_PATTERN = re.compile(
    r"\b(?:(?:working\s+at|joined|at(?:\s+company)?|filter\s+(?:to|by)|only|show(?:\s+from)?)\s+)([A-Z][A-Za-z0-9 &.]{0,40}?)(?:\s+(?:in|and|from|\d{4})|[,.]|$)",
    re.I
)

# Skills: "with Python", "who know X", "skilled in X", "using X"
_SKILL_PATTERN = re.compile(
    r"\b(?:with|knows?|skilled\s+in|using|who\s+know|expertise\s+in)\s+([A-Za-z0-9.# +]{2,30}?)(?:\s+(?:in|at|and|from)|[,.]|$)",
    re.I
)

# Conversational reset signals
_RESET_KEYWORDS = {
    "new search", "start over", "clear", "reset", "forget",
    "something different", "ignore that", "never mind",
}

# Short follow-up signals (no main entity)
_FOLLOW_UP_PREFIXES = re.compile(
    r"^(?:also|and|but|now|then|additionally|what about|how about|"
    r"filter|narrow|show|only|just|from|in|at|with|who|same)\b",
    re.I
)


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
        r"|(?:from|in)\s+\d{4}"       # "from 2019", "in 2020"
        r"|batch\s+\d{4}"             # "batch 2019"
        r"|\d{4}\s+batch"             # "2019 batch"
        r")",
        re.I,
    )
    if _FILTER_ONLY.match(q):
        return True

    # Starts with a follow-up prefix AND is short enough to be a filter addition
    if len(words) <= 5 and _FOLLOW_UP_PREFIXES.match(q):
        return True

    return False


def _extract_slots_from_query(query: str) -> dict:
    """
    Extract structured slots from a single query string.
    Returns dict with keys: company, location, batch_year, skills.
    """
    slots = {"company": None, "location": None, "batch_year": None, "skills": []}

    # Batch year (most unambiguous — match first)
    m = _BATCH_PATTERN.search(query)
    if m:
        year = next((g for g in m.groups() if g), None)
        if year:
            slots["batch_year"] = year.strip()

    # Company
    m = _COMPANY_PATTERN.search(query)
    if m:
        val = m.group(1).strip().title()
        # Reject if it looks like a location or is too generic
        if val and len(val) > 1 and not val.lower() in ("the", "a", "an"):
            slots["company"] = val

    # Location (run after company to avoid double-matches)
    m = _LOCATION_PATTERN.search(query)
    if m:
        val = m.group(1).strip().title()
        # Don't overwrite company with a location token
        if val and len(val) > 1 and val != slots["company"]:
            slots["location"] = val

    # Skills
    for m in _SKILL_PATTERN.finditer(query):
        skill = m.group(1).strip()
        if skill and len(skill) > 1:
            slots["skills"].append(skill)

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
            # This was a "fresh" search → becomes the new base query
            base_query = turn.content
            # Reset accumulated filters when base query changes
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
        resolved_query = base_query  # Inherit the base topic
    else:
        resolved_query = query

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
