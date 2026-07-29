# Generative AI–Led Analysis Platform for Non-Technical Business Users

A full-stack intelligent data analysis platform that enables non-technical users to query datasets using natural language (text or voice), powered by a locally running open-source LLM.

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
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Voice: STT (Whisper) ←→ TTS (pyttsx3)                   ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer       | Technology                            |
|-------------|---------------------------------------|
| Frontend    | React 18, Vite, Recharts              |
| Backend     | FastAPI, SQLAlchemy, Pandas            |
| Auth        | JWT (python-jose, bcrypt)             |
| LLM         | Transformers (Phi-3 Mini stub)        |
| Voice       | Whisper (STT), pyttsx3 (TTS)          |
| Database    | SQLite                                |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip, npm

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Copy `.env` to the project root and update `SECRET_KEY` for production.

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
│   ├── llm/           # LLM integration
│   ├── services/      # Business logic
│   ├── voice/         # Speech-to-Text / Text-to-Speech
│   └── utils/         # Shared utilities
├── datasets/          # Uploaded datasets (gitignored)
├── logs/              # Query logs
├── .env               # Environment variables
├── docker-compose.yml # Container orchestration
└── README.md          # This file
```

## Key Design Principles

1. **Security First** — LLM output is never executed directly; it passes through a deterministic validation layer that blocks destructive operations.
2. **Separation of Concerns** — Frontend handles UI only; all business logic lives in backend services.
3. **Modularity** — Each backend module is independently testable and replaceable.
4. **Read-Only Execution** — Queries run on in-memory copies of DataFrames; original data is never mutated.

## License

Academic project — all rights reserved.
