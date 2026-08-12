# Aether AI — Generative AI Analysis Platform

> A full-stack intelligent data analysis platform that enables non-technical users to query datasets using **natural language** (text or voice), powered by **Google Gemini 2.0 Flash**.

[![Tests](https://img.shields.io/badge/tests-405%20passed-brightgreen)](./backend/tests)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688)](https://fastapi.tiangolo.com)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React/Vite)                  │
│  Login ─ Dashboard ─ Upload ─ Query ─ Charts ─ History      │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API (JWT Auth)
┌───────────────────────▼─────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Auth     │  │ Dataset      │  │ Query Pipeline          │ │
│  │ (JWT)    │  │ Upload +     │  │ NL → LLM → Validate →  │ │
│  │          │  │ Validate +   │  │ Execute → Visualize →   │ │
│  │          │  │ Schema       │  │ Insight                 │ │
│  └──────────┘  └──────────────┘  └────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ML Services: Anomaly Detection · Clustering · Forecast  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Voice: STT (Whisper) ←→ TTS (pyttsx3)                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer       | Technology                                       |
|-------------|--------------------------------------------------|
| Frontend    | React 18, Vite, Recharts                         |
| Backend     | FastAPI, SQLAlchemy, Pandas                       |
| Auth        | JWT (python-jose, bcrypt)                        |
| LLM         | Google Gemini 2.0 Flash (free tier, 15 req/min)  |
| ML          | scikit-learn (Isolation Forest, K-Means, PCA)    |
| Voice       | Whisper (STT), pyttsx3 (TTS)                     |
| Database    | SQLite (swap to PostgreSQL for production)        |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip, npm

### 1. Clone & configure environment
```bash
git clone <repo-url>
cd <repo-folder>
cp .env.example .env
# Edit .env: set GEMINI_API_KEY and generate a new SECRET_KEY
# python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** — API docs at **http://localhost:8000/docs**.

## Running Tests

```bash
cd backend
pytest tests/ -v
```

All **405 tests** across 14 test files pass. Coverage includes:
- Data pipeline (file loading, profiling, schema extraction)
- ML services (anomaly detection, clustering, forecasting)
- Query engine (validation, execution, semantic matching)
- API endpoints (auth, upload, query, history)
- LLM & prompts (templates, stub generation, memory)
- Visualization & E2E pipeline
- Security (injection prevention, cross-user isolation)
- SDLC design compliance & MLOps monitoring

## Folder Structure

```
ROOT/
├── frontend/          # React (Vite) application
│   └── src/
│       ├── api/       # HTTP client & service modules
│       ├── components/# Reusable UI components
│       ├── context/   # React Context (Auth)
│       ├── hooks/     # Custom hooks
│       ├── pages/     # Page components
│       ├── styles/    # CSS files
│       └── utils/     # Helper functions
├── backend/           # FastAPI application
│   ├── api/           # Route handlers
│   ├── auth/          # JWT authentication
│   ├── core/          # App configuration
│   ├── database/      # SQLAlchemy models & session
│   ├── llm/           # LLM integration (Gemini)
│   ├── services/      # Business logic & ML services
│   ├── tests/         # pytest test suite (405 tests)
│   ├── voice/         # Speech-to-Text / Text-to-Speech
│   └── utils/         # Shared utilities
├── datasets/          # Uploaded datasets (gitignored)
├── logs/              # Runtime logs (gitignored)
├── .env.example       # Environment variable template (copy to .env)
├── docker-compose.yml # Container orchestration
└── README.md
```

## Key Design Principles

1. **Security First** — LLM output is never executed directly; it passes through a deterministic AST validation layer that blocks dangerous operations (`os`, `subprocess`, `exec`, file writes, etc.).
2. **Separation of Concerns** — Frontend handles UI only; all business logic lives in backend services.
3. **Modularity** — Each backend module is independently testable and replaceable.
4. **Read-Only Execution** — Queries run on in-memory DataFrame copies; original data is never mutated.
5. **Graceful Degradation** — Every ML service (Gemini, Whisper, Prophet, scikit-learn) has a deterministic fallback so the platform works without optional dependencies.

## License

Academic project — all rights reserved.
