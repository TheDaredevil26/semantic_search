# 🔍 Semantic Search on Alumni Graph

An AI-powered semantic search engine over alumni networks that combines **vector similarity** (Sentence-BERT + FAISS) with **graph-based relationship scoring** (NetworkX + PageRank) to deliver contextually rich, explainable search results.

![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Hybrid Search** | Fuses FAISS vector similarity with NetworkX graph scoring for contextual results |
| **Natural Language Queries** | Ask anything: "Find ML engineers from 2020 batch at product companies" |
| **Graph Visualization** | Interactive vis.js force-directed network showing alumni connections |
| **Profile Detail Modal** | Click any name to see full bio, skills, and connections |
| **Analytics Dashboard** | Animated bar charts for skills, companies, departments, locations |
| **Autocomplete** | Real-time suggestions as you type (alumni, skills, companies, cities) |
| **CSV Export** | Download search results as CSV for further analysis |
| **Explainable Results** | Every result includes a "Why this result?" explanation |
| **Search History** | Recent searches persisted via localStorage |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────┐
│                    Frontend                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Search UI│  │ Graph    │  │ Profile Modal    │  │
│  │ + Auto-  │  │ vis.js   │  │ + Dashboard      │  │
│  │ complete │  │ Network  │  │ + Charts         │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└──────────────────────┬─────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────┴─────────────────────────────┐
│                  FastAPI Backend                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ SBERT    │  │ FAISS    │  │ NetworkX Graph   │  │
│  │ Embedder │  │ Index    │  │ + PageRank       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Entity   │  │ Hybrid   │  │ CSV Export       │  │
│  │ Extractor│  │ Reranker │  │ + Autocomplete   │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Hybrid Scoring Formula

```
final_score = (1 - graph_weight) × vector_similarity + graph_weight × graph_score

graph_score = 0.4 × PageRank + 0.3 × entity_overlap + 0.3 × relationship_density
```

Default: `graph_weight = 0.4` (adjustable via slider)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd semantic

# Install dependencies
pip install -r requirements.txt

# Start the server
python run.py
```

The server will:
1. Generate synthetic alumni data (500 records) on first run
2. Build the NetworkX property graph
3. Generate Sentence-BERT embeddings + FAISS index (cached after first run)
4. Start serving on `http://localhost:8000`

**First run** takes ~30s (model download). **Subsequent runs** take ~11s (cached).

---

## 📁 Project Structure

```
semantic/
├── run.py                      # Entry point
├── config.py                   # Configuration (model, weights, paths)
├── requirements.txt            # Python dependencies
├── data/
│   ├── generate_alumni.py      # Synthetic data generator
│   └── alumni.csv              # 500 alumni records
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + REST endpoints
│   ├── models.py               # Pydantic schemas
│   ├── data_loader.py          # CSV ingestion + normalization
│   ├── graph_builder.py        # NetworkX graph + PageRank
│   ├── embeddings.py           # SBERT + FAISS indexing
│   ├── entity_extractor.py     # Keyword entity extraction
│   └── search_engine.py        # Hybrid search pipeline
├── frontend/
│   ├── index.html              # SPA (Single Page Application)
│   ├── styles.css              # Premium dark-mode design system
│   └── app.js                  # Frontend logic
└── cache/                      # Auto-generated indexes
    ├── embeddings.npy
    ├── faiss.index
    └── graph.pickle
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | Perform hybrid semantic search |
| `GET` | `/api/alumni/{id}` | Get alumni profile |
| `GET` | `/api/alumni/{id}/graph` | Get graph neighborhood for vis.js |
| `GET` | `/api/similar/{id}` | Find similar alumni |
| `GET` | `/api/stats` | Dashboard statistics + distributions |
| `GET` | `/api/filters` | Available filter options |
| `GET` | `/api/autocomplete?q=...` | Search autocomplete suggestions |
| `GET` | `/api/export?query=...` | Export search results as CSV |

Interactive API docs: `http://localhost:8000/docs`

---

## 🎨 Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI/ML** | Sentence-BERT (`all-MiniLM-L6-v2`), FAISS |
| **Graph** | NetworkX, PageRank centrality |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | Vanilla HTML/CSS/JS, vis.js |
| **Data** | Pandas, NumPy |

---

## 📊 Dataset

The synthetic dataset contains 500 realistic Indian alumni records with:

- Full names, batch years (2015–2024), departments (8 types)
- Current roles, companies (74 unique), cities (25)
- Skills (121 unique, 3-8 per person)
- Bios and mentor relationships

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_WEIGHT = 0.6        # Default vector weight
GRAPH_WEIGHT = 0.4         # Default graph weight
FAISS_TOP_K = 50           # FAISS candidates
GRAPH_HOPS = 2             # Neighborhood depth
```

---

## 📝 License

MIT License
