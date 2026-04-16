# Alumni Graph Search — Improvement Specification

> **Document Version:** 1.1  
> **Based on:** `semantic_search-main` codebase analysis + codebase_analysis report  
> **Scope:** Bug fixes, UI overhaul, new database fields, Connect feature, How-It-Works section

---

## Table of Contents

1. [Minor Bug Fixes (from Analysis Report)](#1-minor-bug-fixes)
2. [UI Overhaul — Vibrant Pastel Theme](#2-ui-overhaul--vibrant-pastel-theme)
3. [Search Bar — Highlighted Autocomplete Selection](#3-search-bar--highlighted-autocomplete-selection)
4. [Database Extension — Phone & Email Fields](#4-database-extension--phone--email-fields)
5. [Connect Feature — Phone & Email Display](#5-connect-feature--phone--email-display)
6. [How It Works — Vector & Graph Search Explainer](#6-how-it-works--vector--graph-search-explainer)

---

## 1. Minor Bug Fixes

These are all quick, isolated fixes identified in the codebase analysis. Each takes under 30 minutes.

---

### BUG-01 — Fix: Apostrophe Breaks Bookmark Button

**File:** `frontend/app.js`  
**Function:** `escapeHtml()`

The current implementation escapes `<`, `>`, `&`, and `"` but not single quotes. Alumni with names like `D'Souza` or `O'Brien` generate broken inline onclick handlers, silently disabling the bookmark button for that card.

**Current code:**
```js
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
```

**Fixed code:**
```js
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');   // ← ADD THIS LINE
}
```

---

### BUG-02 — Fix: Division-by-Zero in `search_similar()`

**File:** `backend/search_engine.py`  
**Line:** ~226

The `search()` method already has a guard for `vs_range == 0`, but the identical normalization step in `search_similar()` was never updated with the same guard. When all candidates have identical vector scores, this crashes.

**Current code (search_similar):**
```python
norm_vs = (cand["vector_score"] - min_vs) / vs_range
```

**Fixed code:**
```python
norm_vs = (cand["vector_score"] - min_vs) / vs_range if vs_range > 0 else cand["vector_score"]
```

---

### BUG-03 — Fix: Add Input Length Validation

**File:** `backend/models.py`  
**Class:** `SearchRequest`

No max length means a 100,000-character query string reaches the SBERT encoder, using excess memory and CPU. One-line Pydantic fix:

**Current code:**
```python
query: str = Field(..., description="Natural language search query")
```

**Fixed code:**
```python
query: str = Field(..., max_length=500, description="Natural language search query")
```

---

### BUG-04 — Fix: Wire the Graph Cache (Dead Code)

**File:** `backend/main.py`  
**Function:** `startup()`

The `AlumniGraph.save()` and `AlumniGraph.load()` methods exist but are never called. The graph is fully rebuilt from scratch on every restart (5–10 seconds wasted).

**Add these two lines to the startup handler:**

```python
# BEFORE building the graph, try loading from cache:
try:
    alumni_graph = AlumniGraph.load()
    print("\n[3/4] Graph loaded from cache.")
except Exception:
    print("\n[3/4] Building alumni graph from scratch...")
    alumni_graph = AlumniGraph()
    alumni_graph.build_from_dataframe(df)
    alumni_graph.save()   # ← cache for next restart
```

---

### BUG-05 — Fix: Deprecated `@app.on_event("startup")`

**File:** `backend/main.py`

FastAPI deprecated `@app.on_event` in v0.93. The server prints a deprecation warning on every startup. Migrate to the `lifespan` context manager:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # All the current startup() code goes here
    await startup_logic()
    yield
    # (teardown code here if needed)

app = FastAPI(..., lifespan=lifespan)
```

---

### BUG-06 — Fix: GitHub Link in Footer

**File:** `frontend/index.html`  
**Line:** ~343

The footer links to `https://github.com` (the GitHub homepage, not the actual repo).

```html
<!-- BEFORE -->
<a href="https://github.com" target="_blank">GitHub Repository</a>

<!-- AFTER — replace with real repo URL -->
<a href="https://github.com/YOUR_ORG/semantic-search-alumni" target="_blank">GitHub Repository</a>
```

---

### BUG-07 — Fix: First-Run Import Crash

**File:** `backend/main.py`  
**Line:** ~62

When `alumni.csv` is missing, the code does a bare `from data.generate_alumni import ...` which fails due to a `sys.path` mismatch. Replace with a subprocess call:

```python
if not os.path.exists(ALUMNI_CSV_PATH):
    print("\n[1/4] Generating alumni data...")
    import subprocess
    subprocess.run(
        [sys.executable, str(DATA_DIR / "generate_alumni.py")],
        check=True
    )
else:
    print("\n[1/4] Alumni data found.")
```

---

## 2. UI Overhaul — Vibrant Pastel Theme

Replace the current dark purple monochrome palette with a **vibrant pastel system** — warm, airy, and energetic. The theme uses a soft off-white base with pastel accent pops: coral, lavender, mint, peach, sky blue, and butter yellow.

### CSS Design Token Replacements

Replace the entire `:root` block in `frontend/styles.css`:

```css
/* ==========================================
   ALUMNI GRAPH SEARCH — Vibrant Pastel Theme
   ========================================== */

:root {
  /* === Base Backgrounds === */
  --bg-primary: #faf8ff;          /* near-white with a violet tint */
  --bg-secondary: #f3f0ff;        /* soft lavender page bg */
  --bg-card: rgba(255, 255, 255, 0.85);
  --bg-card-hover: rgba(255, 255, 255, 0.97);
  --bg-glass: rgba(255, 255, 255, 0.55);
  --bg-glass-hover: rgba(255, 255, 255, 0.75);

  /* === Text === */
  --text-primary: #2d2250;        /* deep indigo — readable on light bg */
  --text-secondary: #6b5ea8;      /* muted violet */
  --text-muted: #a89ec9;
  --text-bright: #1a1040;

  /* === Pastel Accent Palette === */
  --accent-lavender:  #b8a9f5;    /* soft purple */
  --accent-coral:     #ff8fa3;    /* warm pink-red */
  --accent-mint:      #7de8c8;    /* fresh green */
  --accent-sky:       #85d1f8;    /* light blue */
  --accent-peach:     #ffb38a;    /* warm orange */
  --accent-butter:    #ffe58a;    /* sunny yellow */
  --accent-rose:      #f9a8c9;    /* pink */
  --accent-lilac:     #d4aaff;    /* deeper lavender */

  /* Primary interactive colour — used for buttons, focus rings, highlights */
  --accent-primary:   #9b7ef8;    /* vibrant violet */
  --accent-primary-glow: rgba(155, 126, 248, 0.22);

  /* === Gradients === */
  --gradient-hero:   linear-gradient(135deg, #c4b0ff 0%, #ffb3c6 50%, #ffe5a0 100%);
  --gradient-card:   linear-gradient(145deg, rgba(184,169,245,0.12) 0%, rgba(255,143,163,0.06) 100%);
  --gradient-search: linear-gradient(90deg, #b8a9f5, #ff8fa3, #ffb38a);
  --gradient-score-vector: linear-gradient(90deg, #85d1f8, #7de8c8);
  --gradient-score-graph:  linear-gradient(90deg, #d4aaff, #f9a8c9);
  --gradient-score-final:  linear-gradient(90deg, #9b7ef8, #7de8c8);

  /* === Borders === */
  --border-subtle:  rgba(155, 126, 248, 0.12);
  --border-medium:  rgba(155, 126, 248, 0.22);
  --border-accent:  rgba(155, 126, 248, 0.45);

  /* === Shadows (softer, coloured) === */
  --shadow-sm:   0 2px 10px rgba(155, 126, 248, 0.10);
  --shadow-md:   0 6px 24px rgba(155, 126, 248, 0.16);
  --shadow-lg:   0 12px 48px rgba(155, 126, 248, 0.20);
  --shadow-glow: 0 0 36px rgba(155, 126, 248, 0.22);

  /* === Typography === */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* === Spacing (unchanged) === */
  --space-xs:  4px;
  --space-sm:  8px;
  --space-md:  16px;
  --space-lg:  24px;
  --space-xl:  32px;
  --space-2xl: 48px;
  --space-3xl: 64px;

  /* === Radii (slightly rounder for a friendlier feel) === */
  --radius-sm:  8px;
  --radius-md:  14px;
  --radius-lg:  20px;
  --radius-xl:  28px;
  --radius-full: 9999px;

  /* === Transitions (unchanged) === */
  --transition-fast:   150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow:   400ms ease;
}
```

### Background Orbs — Pastel Recolour

Update the three background orb colours in `styles.css`:

```css
.bg-orb-1 {
  background: radial-gradient(circle, rgba(184,169,245,0.35) 0%, transparent 70%);
  width: 700px; height: 700px;
  top: -200px; left: -200px;
}
.bg-orb-2 {
  background: radial-gradient(circle, rgba(255,143,163,0.28) 0%, transparent 70%);
  width: 600px; height: 600px;
  bottom: -100px; right: -150px;
}
.bg-orb-3 {
  background: radial-gradient(circle, rgba(125,232,200,0.22) 0%, transparent 70%);
  width: 500px; height: 500px;
  top: 50%; left: 55%;
}
```

### Body Background

```css
body {
  background: var(--bg-secondary);
  background-image:
    radial-gradient(ellipse at 20% 10%, rgba(184,169,245,0.18) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(255,143,163,0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(133,209,248,0.10) 0%, transparent 60%);
  color: var(--text-primary);
}
```

### Header

```css
header {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px) saturate(160%);
  border-bottom: 1px solid var(--border-subtle);
  box-shadow: 0 2px 16px rgba(155, 126, 248, 0.08);
}
.logo h1 { color: var(--text-bright); }
.logo-icon {
  background: var(--gradient-hero);
  border-radius: var(--radius-md);
  color: white;
}
```

### Cards

```css
.result-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-normal), transform var(--transition-normal);
}
.result-card:hover {
  box-shadow: var(--shadow-md), 0 0 0 1px var(--accent-primary);
  transform: translateY(-3px);
}
```

### Search Button

```css
.search-btn {
  background: var(--gradient-search);
  background-size: 200% auto;
  color: white;
  border: none;
  border-radius: var(--radius-full);
  transition: background-position var(--transition-normal), box-shadow var(--transition-normal);
}
.search-btn:hover {
  background-position: right center;
  box-shadow: 0 6px 20px rgba(155, 126, 248, 0.40);
}
```

### Stat Cards — Pastel Colour Rotation

```css
.stat-card:nth-child(1) { border-top: 3px solid var(--accent-lavender); }
.stat-card:nth-child(2) { border-top: 3px solid var(--accent-coral);    }
.stat-card:nth-child(3) { border-top: 3px solid var(--accent-mint);     }
.stat-card:nth-child(4) { border-top: 3px solid var(--accent-sky);      }
```

### Light Theme Override

Since the new theme is already light-first, the `[data-theme="light"]` block should simply remove the dark-mode overrides and set `--bg-primary: #ffffff` for maximum contrast.

---

## 3. Search Bar — Highlighted Autocomplete Selection

### Problem

When a user navigates the autocomplete dropdown (mouse hover or keyboard ↑↓), the "active" item shows only a left-border highlight but does **not** fill the background. The selection is visually weak.

### CSS Fix (`frontend/styles.css`)

```css
/* Replace the existing .autocomplete-item:hover / .autocomplete-item.active block */

.autocomplete-item:hover,
.autocomplete-item.active {
  background: linear-gradient(90deg,
    rgba(155, 126, 248, 0.18) 0%,
    rgba(255, 143, 163, 0.10) 100%
  );
  border-left: 3px solid var(--accent-primary);
  color: var(--text-bright);
  cursor: pointer;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

/* Highlighted type badge when active */
.autocomplete-item.active .ac-type {
  background: rgba(155, 126, 248, 0.25);
  color: var(--accent-primary);
  font-weight: 600;
}

/* Icon accent when active */
.autocomplete-item.active .ac-icon {
  color: var(--accent-primary);
}

/* Animate the active item in with a subtle slide */
.autocomplete-item.active {
  animation: acSlideIn 120ms ease;
}

@keyframes acSlideIn {
  from { transform: translateX(-4px); opacity: 0.7; }
  to   { transform: translateX(0);    opacity: 1;   }
}
```

### JS Enhancement (`frontend/app.js`)

Ensure keyboard selection also scrolls the item into view (prevents items being navigated off-screen in a tall dropdown):

```js
// Inside the keydown handler where .active class is set:
function updateActiveAutocompleteItem(index) {
  const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');
  items.forEach((item, i) => {
    item.classList.toggle('active', i === index);
    if (i === index) {
      item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  });
}
```

---

## 4. Database Extension — Phone & Email Fields

### 4.1 Data Generator (`data/generate_alumni.py`)

Add two new generated fields per alumni record: a plausible Indian mobile number and a work email derived from name + company.

```python
import re

MOBILE_PREFIXES = ["98", "97", "96", "95", "94", "93", "91", "89", "88", "87", "86", "79", "78", "77"]

def generate_phone():
    """Generate a plausible Indian mobile number (10 digits, starts with 6-9)."""
    prefix = random.choice(MOBILE_PREFIXES)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+91 {prefix}{suffix[:4]} {suffix[4:]}"

def generate_email(full_name: str, company: str) -> str:
    """Derive a realistic work email from name and company."""
    # Normalise name → firstname.lastname
    parts = full_name.lower().split()
    first = re.sub(r'[^a-z]', '', parts[0])
    last  = re.sub(r'[^a-z]', '', parts[-1]) if len(parts) > 1 else ""
    
    # Normalise company → domain slug
    domain_slug = re.sub(r'[^a-z0-9]', '', company.lower())[:12]
    
    formats = [
        f"{first}.{last}@{domain_slug}.com",
        f"{first[0]}{last}@{domain_slug}.com",
        f"{first}_{last}@{domain_slug}.in",
    ]
    return random.choice(formats)
```

**In `generate_alumni()`, add to each record dict:**
```python
record["phone"]  = generate_phone()
record["email"]  = generate_email(record["full_name"], record["current_company"])
```

**Update `write_csv()` to include the new columns in the header:**
```python
FIELDNAMES = [
    "alumnus_id", "full_name", "batch_year", "department",
    "current_company", "current_role", "city", "skills", "bio",
    "mentor_id",
    "phone",   # ← NEW
    "email",   # ← NEW
]
```

---

### 4.2 Data Loader (`backend/data_loader.py`)

Ensure the new columns are read and kept (they won't need normalisation):

```python
def load_alumni_data() -> pd.DataFrame:
    df = pd.read_csv(ALUMNI_CSV_PATH)
    # ... existing normalisation ...

    # Keep phone and email; fill missing values gracefully
    df["phone"] = df.get("phone", pd.Series(dtype=str)).fillna("N/A")
    df["email"] = df.get("email", pd.Series(dtype=str)).fillna("N/A")
    return df
```

---

### 4.3 Pydantic Model (`backend/models.py`)

Add the two new fields to `AlumniProfile`:

```python
class AlumniProfile(BaseModel):
    alumnus_id:       str
    full_name:        str
    batch_year:       int
    department:       str
    current_company:  str
    current_role:     str
    city:             str
    skills:           List[str]
    bio:              str
    mentor_id:        Optional[str] = None
    phone:            Optional[str] = None   # ← NEW
    email:            Optional[str] = None   # ← NEW
```

---

### 4.4 API Serialisation (`backend/main.py`)

In the section that builds `AlumniProfile` objects from the DataFrame rows, add the two new fields:

```python
profile = AlumniProfile(
    alumnus_id      = str(row["alumnus_id"]),
    full_name       = row["full_name"],
    batch_year      = int(row["batch_year"]),
    department      = row["department"],
    current_company = row["current_company"],
    current_role    = row["current_role"],
    city            = row["city"],
    skills          = row["skills_list"],
    bio             = row["bio"],
    mentor_id       = row.get("mentor_id"),
    phone           = row.get("phone"),    # ← NEW
    email           = row.get("email"),    # ← NEW
)
```

---

## 5. Connect Feature — Phone & Email Display

### 5.1 Result Card — "Connect" Button

In `frontend/app.js`, inside the `renderResultCard()` function, replace the existing modal-open action with a dedicated **Connect** button that sits alongside the existing "View Profile" and "Graph" buttons:

```js
// Inside renderResultCard() where action buttons are built:
const connectBtn = `
  <button
    class="connect-btn"
    data-id="${result.id}"
    data-name="${escapeHtml(profile.full_name)}"
    data-phone="${escapeHtml(profile.phone || '')}"
    data-email="${escapeHtml(profile.email || '')}"
    onclick="openConnectModal(this)"
    title="Connect with ${escapeHtml(profile.full_name)}"
  >
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07
               A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0 012.2
               0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0 01-.45
               2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2 0 012.11-.45
               c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
    </svg>
    Connect
  </button>
`;
```

---

### 5.2 Profile Modal — Contact Section

Inside the `openProfileModal()` function in `app.js`, add a **Contact** section to the rendered modal body HTML (after the Skills section):

```js
// After the skills section HTML string:
const contactSection = `
  <div class="modal-divider"></div>
  <div class="modal-section-title">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
         stroke="currentColor" stroke-width="2">
      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07
               A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0
               012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0
               01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2
               0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
    </svg>
    Contact
  </div>
  <div class="modal-contact-row">
    <a class="modal-contact-chip phone-chip"
       href="tel:${escapeHtml(profile.phone || '')}" title="Call">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2.5">
        <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07
                 A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2
                 0 012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2
                 2 0 01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28
                 a2 2 0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
      </svg>
      ${escapeHtml(profile.phone || 'Not available')}
    </a>
    <a class="modal-contact-chip email-chip"
       href="mailto:${escapeHtml(profile.email || '')}" title="Email">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12a2 2 0 01-2 2H4a2 2
                 0 01-2-2V6c0-1.1.9-2 2-2z"/>
        <polyline points="22,6 12,13 2,6"/>
      </svg>
      ${escapeHtml(profile.email || 'Not available')}
    </a>
  </div>
`;
```

---

### 5.3 Connect Modal (New Component)

Add a dedicated **Connect Modal** that pops up when "Connect" is clicked on a result card — lightweight, focused, no clutter:

**HTML to add to `index.html`** (before closing `</main>`):

```html
<!-- Connect Modal -->
<div id="connect-modal" class="connect-modal" style="display:none" role="dialog" aria-modal="true">
  <div class="connect-modal-content">
    <button id="close-connect-modal" class="close-btn connect-close-btn" aria-label="Close">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2.5">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <div class="connect-modal-header">
      <div class="connect-avatar" id="connect-avatar">AK</div>
      <div>
        <h3 id="connect-name">Alumni Name</h3>
        <p id="connect-role" class="connect-role">Role at Company</p>
      </div>
    </div>

    <p class="connect-intro">Reach out and start a conversation:</p>

    <div class="connect-options">
      <a id="connect-phone-link" href="#" class="connect-option-card phone-option">
        <div class="connect-option-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2">
            <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07
                     A19.5 19.5 0 013.07 9.81 19.79 19.79 0 01.22 1.18 2 2 0
                     012.2 0h3a2 2 0 012 1.72c.127.96.36 1.903.7 2.81a2 2 0
                     01-.45 2.11L6.27 7.91a16 16 0 006.29 6.29l1.28-1.28a2 2
                     0 012.11-.45c.907.34 1.85.573 2.81.7A2 2 0 0122 16.92z"/>
          </svg>
        </div>
        <div>
          <div class="connect-option-label">Call</div>
          <div class="connect-option-value" id="connect-phone-display">—</div>
        </div>
        <svg class="connect-arrow" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </a>

      <a id="connect-email-link" href="#" class="connect-option-card email-option">
        <div class="connect-option-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12a2 2 0 01-2 2H4a2 2
                     0 01-2-2V6c0-1.1.9-2 2-2z"/>
            <polyline points="22,6 12,13 2,6"/>
          </svg>
        </div>
        <div>
          <div class="connect-option-label">Send Email</div>
          <div class="connect-option-value" id="connect-email-display">—</div>
        </div>
        <svg class="connect-arrow" width="16" height="16" viewBox="0 0 24 24"
             fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </a>
    </div>

    <p class="connect-note">
      Always introduce yourself and mention your shared connection (batch, department, skill) when reaching out.
    </p>
  </div>
</div>
```

**JS to add to `app.js`:**

```js
const connectModal   = document.getElementById('connect-modal');
const closeConnectBtn = document.getElementById('close-connect-modal');

closeConnectBtn.addEventListener('click', () => {
  connectModal.style.display = 'none';
  overlay.style.display      = 'none';
});

function openConnectModal(btn) {
  const name  = btn.dataset.name;
  const phone = btn.dataset.phone || 'Not available';
  const email = btn.dataset.email || 'Not available';

  // Avatar initials
  const initials = name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();
  document.getElementById('connect-avatar').textContent       = initials;
  document.getElementById('connect-name').textContent         = name;
  document.getElementById('connect-phone-display').textContent = phone;
  document.getElementById('connect-email-display').textContent = email;

  const phoneLink = document.getElementById('connect-phone-link');
  const emailLink = document.getElementById('connect-email-link');
  phoneLink.href  = phone !== 'Not available' ? `tel:${phone}` : '#';
  emailLink.href  = email !== 'Not available' ? `mailto:${email}` : '#';

  connectModal.style.display = 'flex';
  overlay.style.display      = 'block';
}
```

**CSS to add to `styles.css`:**

```css
/* === Connect Modal === */
.connect-modal {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
}

.connect-modal-content {
  background: var(--bg-card);
  backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2xl);
  max-width: 440px;
  width: 100%;
  position: relative;
  animation: modalSlideUp 260ms ease;
}

.connect-close-btn {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
}

.connect-modal-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.connect-avatar {
  width: 56px; height: 56px;
  border-radius: var(--radius-full);
  background: var(--gradient-hero);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; font-weight: 700; color: white;
  flex-shrink: 0;
}

.connect-intro {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--space-md);
}

.connect-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.connect-option-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  text-decoration: none;
  color: var(--text-primary);
  transition: background var(--transition-fast), border-color var(--transition-fast),
              box-shadow var(--transition-fast);
}

.connect-option-card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 16px rgba(155, 126, 248, 0.18);
}

.phone-option:hover { background: rgba(125, 232, 200, 0.12); }  /* mint tint */
.email-option:hover { background: rgba(133, 209, 248, 0.12); }  /* sky tint */

.connect-option-icon {
  width: 42px; height: 42px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.phone-option .connect-option-icon { background: rgba(125, 232, 200, 0.20); color: #3cb87e; }
.email-option .connect-option-icon { background: rgba(133, 209, 248, 0.20); color: #2a8fc2; }

.connect-option-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

.connect-option-value {
  font-size: 0.925rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-top: 2px;
}

.connect-arrow {
  margin-left: auto;
  color: var(--text-muted);
  flex-shrink: 0;
}

.connect-note {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.5;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-glass);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--accent-peach);
}

/* Contact chips inside the full profile modal */
.modal-contact-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.modal-contact-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  border: 1px solid var(--border-subtle);
  transition: background var(--transition-fast), box-shadow var(--transition-fast);
}

.phone-chip {
  color: #2d8c64;
  background: rgba(125, 232, 200, 0.12);
}
.phone-chip:hover {
  background: rgba(125, 232, 200, 0.25);
  box-shadow: 0 3px 10px rgba(125, 232, 200, 0.25);
}

.email-chip {
  color: #1f7aad;
  background: rgba(133, 209, 248, 0.12);
}
.email-chip:hover {
  background: rgba(133, 209, 248, 0.25);
  box-shadow: 0 3px 10px rgba(133, 209, 248, 0.25);
}

/* Connect button on result cards */
.connect-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: var(--radius-full);
  font-size: 0.82rem;
  font-weight: 600;
  border: 1px solid rgba(125, 232, 200, 0.5);
  color: #2d8c64;
  background: rgba(125, 232, 200, 0.12);
  cursor: pointer;
  transition: background var(--transition-fast), box-shadow var(--transition-fast);
}
.connect-btn:hover {
  background: rgba(125, 232, 200, 0.25);
  box-shadow: 0 3px 12px rgba(125, 232, 200, 0.30);
}
```

---

## 6. How It Works — Vector & Graph Search Explainer

Add a collapsible, visually rich **"How It Works"** section to `index.html`. Place it between the Path Finder section and the Results section, so it's always visible on first load.

### 6.1 HTML (`frontend/index.html`)

```html
<!-- HOW IT WORKS SECTION — place after #path-finder-section -->
<section id="how-it-works" class="how-it-works-section">
  <div class="hiw-toggle" id="hiw-toggle" onclick="toggleHowItWorks()" aria-expanded="false">
    <div class="hiw-toggle-left">
      <div class="hiw-toggle-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <span>How does the search work?</span>
    </div>
    <svg class="hiw-chevron" width="18" height="18" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="2.5">
      <polyline points="6 9 12 15 18 9"/>
    </svg>
  </div>

  <div class="hiw-body" id="hiw-body" style="display:none">

    <!-- Intro -->
    <p class="hiw-intro">
      This system uses <strong>two complementary AI techniques</strong> to find the most relevant alumni —
      not just those who share keywords with your query, but those who are
      semantically and relationally closest to what you're looking for.
    </p>

    <div class="hiw-cards">

      <!-- VECTOR SEARCH CARD -->
      <div class="hiw-card vector-card">
        <div class="hiw-card-header">
          <div class="hiw-card-icon vector-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <h4 class="hiw-card-title">Vector Search</h4>
            <span class="hiw-card-badge">Sentence-BERT + FAISS</span>
          </div>
        </div>
        <div class="hiw-card-body">
          <p>
            Every alumni profile is converted into a <strong>384-dimensional vector</strong>
            (a list of numbers) using a Sentence-BERT language model. This vector encodes the
            <em>semantic meaning</em> of the profile — not just which words appear, but what
            concepts they represent.
          </p>
          <p>
            When you type a query, it is encoded into its own vector using the same model.
            FAISS (Facebook AI Similarity Search) then finds the profiles whose vectors are
            closest in this 384-dimensional space — a process called
            <strong>cosine similarity search</strong>.
          </p>
          <div class="hiw-example">
            <span class="hiw-example-label">Why this matters</span>
            A search for <em>"AI engineer"</em> will surface profiles that mention
            "machine learning practitioner" or "deep learning researcher" — even without
            any exact keyword match — because those phrases encode to similar vector positions.
          </div>
        </div>
        <div class="hiw-pipeline">
          <div class="hiw-step">Your query</div>
          <div class="hiw-step-arrow">→</div>
          <div class="hiw-step">SBERT encodes to vector</div>
          <div class="hiw-step-arrow">→</div>
          <div class="hiw-step">FAISS finds nearest neighbours</div>
          <div class="hiw-step-arrow">→</div>
          <div class="hiw-step">Top-N candidates ranked by cosine similarity</div>
        </div>
      </div>

      <!-- GRAPH SEARCH CARD -->
      <div class="hiw-card graph-card">
        <div class="hiw-card-header">
          <div class="hiw-card-icon graph-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2">
              <circle cx="18" cy="5" r="3"/>
              <circle cx="6"  cy="12" r="3"/>
              <circle cx="18" cy="19" r="3"/>
              <line x1="8.59"  y1="13.51" x2="15.42" y2="17.49"/>
              <line x1="15.41" y1="6.51"  x2="8.59"  y2="10.49"/>
            </svg>
          </div>
          <div>
            <h4 class="hiw-card-title">Graph Search</h4>
            <span class="hiw-card-badge">NetworkX Property Graph</span>
          </div>
        </div>
        <div class="hiw-card-body">
          <p>
            All 500 alumni records are loaded into a <strong>property graph</strong> with
            7 node types: Alumni, Company, Skill, Department, Batch, Location, and Mentor.
            Each relationship (worked at, has skill, mentored by…) is an edge.
          </p>
          <p>
            For each vector search candidate, a <strong>graph relevance score</strong> is
            computed using three signals: <em>PageRank centrality</em> (how well-connected is
            this alumnus overall?), <em>entity overlap</em> (how many entities from your query
            appear in their graph neighbourhood?), and <em>relationship density</em> (how rich
            are their connections to other relevant nodes?).
          </p>
          <div class="hiw-example">
            <span class="hiw-example-label">Why this matters</span>
            Two profiles may have identical vector scores, but the one who is also a mentor,
            worked at two companies you mentioned, and shares a batch with a reference profile
            will rank higher — because their graph position is more relevant.
          </div>
        </div>
        <div class="hiw-pipeline">
          <div class="hiw-step">Vector candidates</div>
          <div class="hiw-step-arrow">→</div>
          <div class="hiw-step">PageRank + entity overlap + density</div>
          <div class="hiw-step-arrow">→</div>
          <div class="hiw-step">Graph score (0–1)</div>
        </div>
      </div>

    </div><!-- /hiw-cards -->

    <!-- HYBRID FUSION -->
    <div class="hiw-fusion-card">
      <div class="hiw-fusion-header">
        <div class="hiw-card-icon fusion-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h4>Hybrid Fusion — The Final Score</h4>
      </div>
      <p class="hiw-fusion-desc">
        The two scores are combined using a configurable <strong>graph weight (α)</strong>
        that you can adjust with the slider in the search bar:
      </p>
      <div class="hiw-formula">
        <span class="formula-part vector-part">( 1 − α ) × Vector Score</span>
        <span class="formula-plus">+</span>
        <span class="formula-part graph-part">α × Graph Score</span>
        <span class="formula-equals">=</span>
        <span class="formula-part final-part">Final Ranking Score</span>
      </div>
      <p class="hiw-fusion-note">
        At <strong>α = 0.0</strong>, ranking is pure semantic similarity (vector only).
        At <strong>α = 1.0</strong>, ranking is purely graph-based (relationship richness).
        The default of <strong>α = 0.4</strong> balances both signals.
        Each result card also shows a breakdown of its vector score, graph score,
        and final score so you can see exactly how the ranking was decided.
      </p>
    </div>

  </div><!-- /hiw-body -->
</section>
```

### 6.2 JS (`frontend/app.js`)

```js
function toggleHowItWorks() {
  const body    = document.getElementById('hiw-body');
  const toggle  = document.getElementById('hiw-toggle');
  const chevron = toggle.querySelector('.hiw-chevron');
  const isOpen  = body.style.display !== 'none';

  if (isOpen) {
    body.style.display = 'none';
    toggle.setAttribute('aria-expanded', 'false');
    chevron.style.transform = 'rotate(0deg)';
  } else {
    body.style.display = 'block';
    toggle.setAttribute('aria-expanded', 'true');
    chevron.style.transform = 'rotate(180deg)';
    body.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}
```

### 6.3 CSS (`frontend/styles.css`)

```css
/* === How It Works Section === */
.how-it-works-section {
  max-width: 960px;
  margin: 0 auto var(--space-2xl);
  padding: 0 var(--space-lg);
}

.hiw-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast), box-shadow var(--transition-fast);
  font-weight: 600;
  color: var(--text-primary);
}
.hiw-toggle:hover {
  background: var(--bg-card-hover);
  box-shadow: var(--shadow-sm);
}

.hiw-toggle-left {
  display: flex; align-items: center; gap: var(--space-sm);
}

.hiw-toggle-icon {
  width: 32px; height: 32px;
  border-radius: var(--radius-sm);
  background: rgba(155, 126, 248, 0.15);
  color: var(--accent-primary);
  display: flex; align-items: center; justify-content: center;
}

.hiw-chevron {
  color: var(--text-muted);
  transition: transform var(--transition-normal);
}

.hiw-body {
  margin-top: var(--space-md);
  animation: fadeInDown 300ms ease;
}

.hiw-intro {
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.7;
  max-width: 700px;
  margin: 0 auto var(--space-xl);
}

.hiw-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}
@media (max-width: 700px) {
  .hiw-cards { grid-template-columns: 1fr; }
}

.hiw-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex; flex-direction: column; gap: var(--space-md);
}
.vector-card { border-top: 3px solid var(--accent-sky);     }
.graph-card  { border-top: 3px solid var(--accent-lavender); }

.hiw-card-header {
  display: flex; align-items: center; gap: var(--space-md);
}

.hiw-card-icon {
  width: 44px; height: 44px;
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.vector-icon { background: rgba(133,209,248,0.18); color: #1f7aad; }
.graph-icon  { background: rgba(184,169,245,0.18); color: #7b5ccc; }
.fusion-icon { background: rgba(125,232,200,0.18); color: #2d8c64; }

.hiw-card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-bright);
  margin: 0 0 4px;
}

.hiw-card-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.hiw-card-body p {
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0;
}
.hiw-card-body p + p { margin-top: var(--space-sm); }

.hiw-example {
  background: var(--bg-glass);
  border-left: 3px solid var(--accent-butter);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: var(--space-sm) var(--space-md);
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.6;
}
.hiw-example-label {
  display: block;
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--accent-peach);
  margin-bottom: 4px;
}

.hiw-pipeline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-glass);
  border-radius: var(--radius-md);
  font-size: 0.78rem;
}
.hiw-step {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 3px 10px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  white-space: nowrap;
}
.hiw-step-arrow { color: var(--text-muted); font-size: 0.85rem; }

/* Fusion card */
.hiw-fusion-card {
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-top: 3px solid var(--accent-mint);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.hiw-fusion-header {
  display: flex; align-items: center; gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.hiw-fusion-header h4 {
  font-size: 1.05rem; font-weight: 700;
  color: var(--text-bright); margin: 0;
}

.hiw-fusion-desc {
  font-size: 0.875rem; color: var(--text-secondary);
  line-height: 1.6; margin-bottom: var(--space-md);
}

.hiw-formula {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-lg);
  background: var(--bg-glass);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-md);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  font-weight: 600;
}

.formula-part {
  padding: 6px 16px;
  border-radius: var(--radius-full);
}
.vector-part { background: rgba(133,209,248,0.18); color: #1f7aad; }
.graph-part  { background: rgba(184,169,245,0.18); color: #7b5ccc; }
.final-part  { background: rgba(125,232,200,0.18); color: #2d8c64; }
.formula-plus, .formula-equals {
  font-size: 1.1rem; color: var(--text-muted); font-weight: 700;
}

.hiw-fusion-note {
  font-size: 0.82rem; color: var(--text-muted); line-height: 1.6;
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0);    }
}
```

---

## Summary Checklist

| # | Area | File(s) | Effort |
|---|------|---------|--------|
| BUG-01 | Apostrophe fix in `escapeHtml()` | `app.js` | < 5 min |
| BUG-02 | Division-by-zero in `search_similar()` | `search_engine.py` | < 5 min |
| BUG-03 | Input `max_length` in `SearchRequest` | `models.py` | < 2 min |
| BUG-04 | Wire graph cache (save + load) | `main.py` | ~15 min |
| BUG-05 | Migrate `@app.on_event` → lifespan | `main.py` | ~20 min |
| BUG-06 | Fix GitHub footer link | `index.html` | < 2 min |
| BUG-07 | Fix first-run import crash | `main.py` | ~10 min |
| UI | Vibrant pastel CSS theme overhaul | `styles.css` | ~2 hrs |
| UI | Autocomplete selection highlight + scroll-into-view | `styles.css`, `app.js` | ~30 min |
| DB | Phone + email fields in generator, loader, models, API | 4 files | ~1 hr |
| FEAT | Connect modal with phone/email | `index.html`, `app.js`, `styles.css` | ~2 hrs |
| FEAT | Contact chips in full profile modal | `app.js`, `styles.css` | ~30 min |
| FEAT | How It Works collapsible section | `index.html`, `app.js`, `styles.css` | ~1.5 hrs |

---

*All changes are backward-compatible. The existing alumni CSV can be regenerated to include phone/email fields by deleting `data/alumni.csv` and restarting the server — the generator will re-run automatically.*
