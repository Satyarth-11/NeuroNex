# NeuroNex — AI-Powered Criminal Network Analysis System
### Smart India Hackathon 2024 · PS ID: SIH26189

> **Decision Support Tool Only.** NeuroNex is an explainable, graph-based criminal intelligence
> platform. It assists — never replaces — human investigators. Every AI-generated insight requires
> human analyst review before any action is taken.

---

## ⚠️ Data Provenance

This prototype uses entirely synthetic, generated data (see `backend/data/synthetic/`) as
structural analogs of seven real-world investigative source types: FIRs/police reports,
Call Detail Records (CDRs), financial transaction records, surveillance reports, social media
intelligence, criminal history databases, and intelligence agency reports.

Real records of these types are legally restricted to authorised law-enforcement personnel
under judicial/departmental oversight and are not used, referenced, or accessible anywhere
in this codebase. Each synthetic file mirrors the field structure and data characteristics
investigators described, so the ingestion, NLP, entity-resolution, knowledge-graph, and
analytics pipeline can be demonstrated end-to-end exactly as it would run against real records
once authorised and integrated with an agency's actual data systems.

Public reference material used to ground schema realism: NCRB "Crime in India" reports and
CCTNS documentation (ncrb.gov.in) — aggregate public statistics only, no individual records.

---

## 🧠 Architecture

```
React Frontend (Cytoscape.js) ──REST/JSON──> FastAPI Backend ──> { Neo4j (graph), SQLite (app data) }
```

### Pipeline Stages

```
Multi-Source Data Ingestion → Cleaning/Normalisation → NLP/NER (spaCy + regex)
→ Entity Resolution (rapidfuzz) → Knowledge Graph (Neo4j) → Graph Analytics (NetworkX)
→ Community Detection (Louvain) → Explainable Insights → Human Analyst Review
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Cytoscape.js, Recharts |
| Backend | Python 3.11, FastAPI, Uvicorn |
| NLP/NER | spaCy `en_core_web_sm` + regex extractors |
| Entity Resolution | rapidfuzz (fuzzy) + rule-based exact matching |
| Graph DB | Neo4j 5.x (Community) |
| App DB | SQLite (async, via SQLAlchemy) — swappable to PostgreSQL |
| Graph Analytics | NetworkX |
| Community Detection | python-louvain (Louvain) + greedy-modularity fallback |
| Deployment | Docker Compose |

---

## 🚀 Quick Start — Docker Compose (recommended)

```bash
# 1. Clone / extract the project
cd neuronex

# 2. Copy environment config
cp .env.example .env

# 3. Start all services (Neo4j + Backend + Frontend)
docker compose up --build

# 4. Open the application
#    Frontend:     http://localhost:3001
#    Backend API:  http://localhost:8000/docs
#    Neo4j Browser: http://localhost:7474  (login: neo4j / neuronex_demo)
```

The backend Dockerfile automatically runs `generate_synthetic_data.py` during build,
so all synthetic data files are present when the container starts.

---

## 🛠️ Manual Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy NER model
python -m spacy download en_core_web_sm

# Generate synthetic data
python data/synthetic/generate_synthetic_data.py

# Copy and configure .env
cp ../.env.example .env
# Edit .env: set NEO4J_URI to your running Neo4j instance

# Start Neo4j (if not running via Docker)
# Download Neo4j Community from https://neo4j.com/download/ and start it

# Run the backend
cd ..
uvicorn app.main:app --reload --port 8000
# API docs available at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server (proxies /api to localhost:8000)
npm run dev
# Open http://localhost:3001
```

---

## 📊 Generating Synthetic Data

The synthetic data generator creates all 7 source files deterministically from a fixed seed (42):

```bash
python backend/data/synthetic/generate_synthetic_data.py
```

**Output files** (all labeled `[SYNTHETIC]` in terminal output):
| File | Source Type | Records |
|---|---|---|
| `cases_manifest.json` | 10 Distinct Investigation Cases | 10 cases |
| `fir_reports.csv` | FIR / Police Reports | 10 FIRs |
| `cdr_records.csv` | Call Detail Records | 20 CDR rows |
| `financial_transactions.csv` | Financial Transactions | 10 transactions |
| `surveillance_reports.txt` | Surveillance Reports | 4 reports |
| `social_media_posts.csv` | Social Media Intelligence | 8 posts |
| `criminal_history.csv` | Criminal History Database | 6 records |
| `intelligence_reports.txt` | Intelligence Agency Reports | 3 reports |
| `ground_truth_pairs.csv` | Validation ground truth | 20 pairs (16 positive, 4 negative) |

The shared cast of 14 fictional persons, phones, accounts, vehicles, and 2 organisations is
distributed across 10 distinct investigation cases with realistic name variation (full name in FIR,
alias in criminal history, handle in social media). This cross-case overlap exercises entity resolution,
produces multiple connected communities, and demonstrates cross-case graph discovery.

---

## ⚡ Instant Live Demo (One-Click Seeding)

For hackathon presentations and evaluator walk-throughs:
1. Open the **Overview** page at `http://localhost:3001`
2. Click **⚡ Load Demo Data (10 cases)**
3. The system automatically creates 10 distinct cases, parses multi-source evidence (FIRs, CDRs, Financial, Surveillance, Social Media, Criminal History, Intel Reports), constructs the knowledge graph in Neo4j, and executes system-wide entity resolution.
4. When done, explore the populated network graph, communities, AI insights, and cross-case duplicate reviews immediately!
5. To reset before another demonstration, click **🗑️ Reset Demo Data** (wipes all SQLite tables and clears Neo4j).

---

## 🔄 Manual Workflow

1. **Create a case** → Cases page → enter case code and title
2. **Upload files** → Upload page → select source type → drag-and-drop synthetic file → Upload
3. **Process files** → click "Process → KG" for each uploaded document
4. **View the graph** → Knowledge Graph page → filter by entity type or source type
5. **Explore entities** → Entity Explorer → search and trace any entity back to its source docs
6. **View communities** → Communities page → see Louvain-detected network clusters
7. **View insights** → Insights page → read AI-generated leads with source evidence
8. **Review leads** → Analyst Review page → approve / reject / flag insights and merge cross-case duplicates
9. **Run validation** → Validation page → click Run → view Precision / Recall / F1 chart

---

## ✅ Running Validation

```bash
# Ensure synthetic data has been generated (ground_truth_pairs.csv must exist)
python backend/data/synthetic/generate_synthetic_data.py

# Via API (after at least one document has been processed)
curl -X POST http://localhost:8000/api/validation/run

# Via UI: Validation page → Run Validation button
```

---

## 📁 Folder Structure

```
neuronex/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Env-driven settings
│   │   ├── db_sql.py            # SQLAlchemy async engine
│   │   ├── db_graph.py          # Neo4j driver singleton
│   │   ├── models_sql.py        # ORM models (6 tables)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── ingestion/           # 7 source-type adapters
│   │   ├── pipeline/            # cleaning, NER, resolution, KG, analytics, communities, explainability
│   │   └── routers/             # 8 FastAPI routers
│   └── data/synthetic/          # Generated synthetic data files
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/client.js        # Centralised API client
        ├── components/          # 6 shared components
        └── pages/               # 9 page components
```

---

## 🔒 Key Design Principles

1. **No blockchain** — not used anywhere.
2. **Synthetic data only** — all 7 source files generated; UI shows SYNTHETIC badge throughout.
3. **Explainability** — every insight carries `explanation`, `source_refs`, and `contributing_source_types`.
4. **Human-in-the-loop** — all insights stay "proposed" until a human analyst approves/rejects/flags.
5. **criminal_history_flag** is informational context only — never used for automated scoring.
6. **Swappable components** — NER model (`ner.py::extract_entities`), resolver, and community
   algorithm are each isolated behind a single function for easy upgrade.

---

## 🏗️ PS ID: SIH26189 — Problem Statement Alignment

| Requirement | Implementation |
|---|---|
| Multi-source data ingestion | 7 distinct adapters in `ingestion/` |
| Entity Resolution | rapidfuzz + exact matching, thresholds in config |
| Knowledge Graph | Neo4j with canonical deterministic IDs |
| Graph Analytics | NetworkX degree + betweenness centrality |
| Community Detection | Louvain (python-louvain) + greedy-modularity fallback |
| Explainability | Plain-language insights with source tracing |
| Human Review | Approve/reject/flag workflow with audit log |
| Validation | Precision/Recall/F1 vs. ground-truth pairs |
| No blockchain | ✅ Not present anywhere |
| Synthetic data | ✅ Clearly labeled throughout |
