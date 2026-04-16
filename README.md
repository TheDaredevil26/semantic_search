# 🔍 Semantic Search on Alumni Graph

An AI-powered semantic search engine over alumni networks that combines **vector similarity** (Sentence-BERT + FAISS) with **graph-based relationship scoring** (NetworkX + PageRank) to deliver contextually rich, explainable search results. 

The application utilizes a powerful Python FastAPI backend driving advanced ML architectures, and a sleek, modern React 18 frontend built with Vite and Tailwind CSS.

![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?logo=tailwind-css&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Hybrid Search** | Fuses FAISS vector similarity with NetworkX graph scoring for contextual results |
| **Conversational Search** | Chat interface that retains contextual history for deep multi-turn queries. |
| **Network Graph Visualization** | Interactive vis.js force-directed Network showing colored clustering by node-type. |
| **Connection PathFinder** | Determine the shortest navigational degree of separation between any two alumni and visualize the path inline. |
| **Global Command Palette** | Strike `Cmd+K` from anywhere in the app to search instantly across all directories using the Autocomplete AI. |
| **Profile Comparison Matrix** | Select up to 3 individual alumni to launch a side-by-side comparison modal evaluating factors. |
| **Interactive Graph Clustering** | Dynamically collapse massive webs by clustering alumni by Department, Company, or Batch grouping. |
| **Explainable Results** | Every matching result includes a "Why this result?" breakdown measuring semantic weights against topological weights. |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────┐
│                  React + Vite SPA                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Search UI│  │ Network  │  │ Dashboard        │  │
│  │ + Chat   │  │ Graph    │  │ + Comparison     │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└──────────────────────┬─────────────────────────────┘
                       │ REST API (JSON Proxy :8000)
┌──────────────────────┴─────────────────────────────┐
│                  FastAPI Backend                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ SBERT    │  │ FAISS    │  │ NetworkX Graph   │  │
│  │ Embedder │  │ Index    │  │ + PageRank       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Entity   │  │ Hybrid   │  │ Path Finder      │  │
│  │ Extractor│  │ Reranker │  │ Engine           │  │
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

- Node.js 18+
- Python 3.10+
- pip

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd semantic_search
```

2. **Start the Backend server**
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (runs on port 8000)
python run.py
```
> The server will generate synthetic alumni data on first launch, compute FAISS embeddings, and build the NetworkX structures.

3. **Start the Frontend development server**
```bash
# Open a second terminal window
cd frontend

# Install node dependencies
npm install

# Start Vite client on localhost:5173
npm run dev
```

---

## 📁 Project Structure

```
semantic_search/
├── run.py                      # Main Python server entrypoint
├── config.py                   # Global Model configurations
├── backend/
│   ├── main.py                 # FastAPI app + REST endpoints
│   ├── graph_builder.py        # NetworkX graph construction
│   ├── search_engine.py        # Logic pipeline for Hybrid Search
│   └── embeddings.py           # SBERT FAISS encoding
├── frontend/
│   ├── index.html              # React Injection Source
│   ├── vite.config.js          # Client Proxy Build Configs
│   ├── src/
│   │   ├── api/                # API client mappers
│   │   ├── components/         # Modular React views
│   │   ├── hooks/              # Native state logic
│   │   └── pages/              # Main App Routes
└── data/                       
    ├── generate_alumni.py      # Synthetic dataset creation
    └── alumni.csv              # Underlying source data
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | Perform hybrid semantic search |
| `POST` | `/api/chat` | Multi-turn conversational interaction endpoint |
| `GET` | `/api/alumni/{id}` | Get alumni profile |
| `GET` | `/api/alumni/{id}/graph` | Generates graph topology logic for an individual |
| `GET` | `/api/path/{id1}/{id2}` | Yield the shortest degree of separation between alumni |
| `GET` | `/api/autocomplete?q=...` | Global string prediction |
| `GET` | `/api/export?query=...` | CSV dataset pipeline |

Interactive API docs natively accessible via: `http://localhost:8000/docs`

---

## 🎨 Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI/ML** | Sentence-BERT (`all-MiniLM-L6-v2`), FAISS |
| **Graphing** | NetworkX, Personalized PageRank, Node2Vec |
| **Backend** | Python, FastAPI, Uvicorn, Pandas |
| **Frontend** | React 18, Vite, React Router, Tailwind CSS |
| **Vis JS** | vis-network HTML5 Canvas mapping |

---

## 📝 License

MIT License
