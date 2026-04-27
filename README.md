<p align="center">
  <h1 align="center">Aether AI — Generative AI Analysis Platform</h1>
  <p align="center">
    A full-stack intelligent data analysis platform that empowers non-technical business users to query, clean, visualize, and forecast data using natural language — powered by Google Gemini AI.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_AI-2.0_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Accuracy-97.6%25-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup (Manual)](#local-setup-manual)
  - [Docker Setup](#docker-setup)
  - [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Pipeline Accuracy](#pipeline-accuracy)
- [Security Architecture](#security-architecture)
- [Deployment Guide](#deployment-guide)
- [Testing](#testing)
- [Design Principles](#design-principles)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Overview

Traditional data analysis requires SQL expertise, Python proficiency, and visualization tool knowledge — skills most business users lack. **Aether AI** bridges this gap by providing a natural-language interface where users simply type or speak their questions in plain English.

**How It Works:**
```
User: "Show the average AQI by city, sorted highest first"
  |
  v
[Gemini AI generates Pandas code] --> [AST Validator] --> [Sandboxed Executor]
  |
  v
[Auto-selects Bar Chart] --> [Generates Insights] --> [Detects Anomalies]
  |
  v
User sees: Chart + Insights + AI Narration + Follow-up Suggestions
```

The platform handles the complete data lifecycle: **Upload → Clean → Query → Visualize → Forecast → Report**.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React 19 + Vite 7)                    │
│                                                                     │
│   Landing ─ Auth ─ Dashboard ─ Upload ─ Cleaning ─ Query ─ Join    │
│   Forecast ─ Profile ─ History ─ Compare ─ What-If ─ Alerts        │
│                                                                     │
│   Components: ChartRenderer │ VoiceRecorder │ ChatSidebar │        │
│               ReportBuilder │ NotificationBell │ ErrorBoundary      │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ REST API (JWT + Refresh Tokens)
┌─────────────────────────▼───────────────────────────────────────────┐
│                      BACKEND (FastAPI + Python)                      │
│                                                                      │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────────────┐  │
│  │ Auth Layer   │  │ Dataset Engine   │  │ Query Pipeline         │  │
│  │              │  │                  │  │                        │  │
│  │ • JWT Tokens │  │ • Upload/Parse   │  │ NL Question            │  │
│  │ • Refresh    │  │ • Schema Extract │  │   ↓                    │  │
│  │ • Ownership  │  │ • Data Profiling │  │ Gemini Code Gen        │  │
│  │ • bcrypt     │  │ • Data Cleaning  │  │   ↓                    │  │
│  │              │  │ • Neon Persist   │  │ AST Validation         │  │
│  └──────────────┘  └─────────────────┘  │   ↓                    │  │
│                                          │ Sandboxed Execution    │  │
│  ┌──────────────────────────────────┐   │   ↓                    │  │
│  │ Intelligence Layer               │   │ Viz Selection          │  │
│  │                                  │   │   ↓                    │  │
│  │ • Anomaly Detection (Z/IQR)     │   │ Insight Generation     │  │
│  │ • Forecasting (LR + MA)         │   │   ↓                    │  │
│  │ • Smart Alerts                   │   │ Anomaly Detection      │  │
│  │ • Scenario Analysis              │   │   ↓                    │  │
│  │ • Cross-Dataset JOIN             │   │ AI Narration           │  │
│  └──────────────────────────────────┘   └────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ Voice: STT (Whisper) ←→ TTS (gTTS)                          │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│            PostgreSQL (Neon Serverless) / SQLite (dev)               │
│                                                                      │
│  Tables: users │ datasets │ query_logs │ saved_queries │ alerts      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite 7, Recharts, React Router 7, React Grid Layout, jsPDF, html2canvas |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pandas, NumPy, Pydantic |
| **Authentication** | JWT (python-jose), bcrypt, Refresh Tokens |
| **LLM / AI** | Google Gemini 2.0 Flash API (with keyword-based stub fallback) |
| **Voice** | Whisper (STT), gTTS (TTS) |
| **Database** | PostgreSQL (Neon Serverless) / SQLite (local dev) |
| **Deployment** | Docker, Docker Compose, Render / Railway / Vercel |
| **Design System** | Aether Flow — Glassmorphism, dark mode, mesh gradient backgrounds |

---

## Features

### Core Analysis Pipeline
| Feature | Description |
|---|---|
| **Natural Language Querying** | Ask data questions in plain English — Gemini generates Pandas code automatically |
| **Voice Input/Output** | Record voice queries (Speech-to-Text) and listen to AI narration (Text-to-Speech) |
| **Auto-Visualization** | AI selects the optimal chart type: Bar, Line, Pie, Scatter, Histogram, Heatmap, or Table |
| **AI Insights** | Automated analyst-style highlights with rankings, comparisons, and trend detection |
| **Anomaly Detection** | Z-score and IQR-based outlier detection with contextual insights |
| **Smart Suggestions** | AI-powered follow-up questions after every query |

### Data Management
| Feature | Description |
|---|---|
| **Dataset Upload** | CSV and Excel support with automatic schema extraction and validation |
| **Data Profiling** | Rich statistical profiles: distributions, correlations, missing value analysis |
| **Power BI-Style Data Cleaning** | Dedicated cleaning page with 10+ quick actions (Remove Duplicates, Fill Nulls, Trim Whitespace, etc.) and NL cleaning |
| **Applied Steps Log** | Full audit trail of cleaning transformations with before/after row counts |

### Advanced Analytics
| Feature | Description |
|---|---|
| **Predictive Forecasting** | Linear Regression and Moving Average with R² confidence scores |
| **Multi-Dataset JOIN** | Cross-reference data across multiple datasets with automatic key detection |
| **What-If Scenario Analysis** | Adjust variables and see predicted outcomes |
| **Dataset Comparison** | Side-by-side statistical comparison of two datasets |
| **Smart Alerts** | Set threshold-based alerts on any metric |

### Enterprise Features
| Feature | Description |
|---|---|
| **Dashboard Builder** | Pin query results to a Power BI-style drag-and-drop dashboard (persistent) |
| **PDF Report Export** | Generate branded reports with charts, insights, and narration |
| **Query History** | Full history with re-run, save, and search capabilities |
| **Saved Queries** | Bookmark frequently used queries for quick access |
| **Conversational Chat** | Multi-turn contextual chat sidebar for follow-up analysis |
| **Notification System** | Real-time alert notifications with a bell icon |

### Security & UX
| Feature | Description |
|---|---|
| **JWT + Refresh Tokens** | Secure authentication with automatic token refresh |
| **AST-Level Sandboxing** | LLM-generated code validated before execution — blocks imports, dunder access, destructive operations |
| **Read-Only Execution** | Queries run on in-memory DataFrame copies — original data never mutated |
| **Dataset Ownership** | Users can only access their own datasets |
| **Error Boundary** | Graceful error handling prevents white-screen crashes |
| **Responsive Design** | Fully responsive with collapsible sidebar navigation |

---

## Screenshots

> After cloning, run the app locally and visit `http://localhost:5173` to see the full UI.

| Page | Description |
|---|---|
| **Landing** | Animated hero section with feature showcase |
| **Dashboard** | Power BI-style multi-chart pinboard with drag-and-drop |
| **Query** | NL input with voice, chart output, insights, and suggestions |
| **Data Cleaning** | Power Query-style editor with quick actions and applied steps log |
| **Forecast** | Interactive forecasting with confidence intervals |
| **Data Profile** | Rich statistical dashboard with distributions and correlations |

---

## Project Structure

```
aether-ai-platform/
│
├── frontend/                          # React 19 (Vite) Application
│   ├── Dockerfile                     # Multi-stage build (Node → Nginx)
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── api/                       # HTTP Client & Service Modules
│       │   ├── axiosClient.js         #   Axios instance with JWT interceptor
│       │   ├── auth.js                #   Login, Register, Token refresh
│       │   ├── datasets.js            #   Upload, List, Profile, Schema
│       │   ├── queries.js             #   NL Query, Clean, Forecast
│       │   ├── savedQueries.js        #   Bookmark management
│       │   └── alerts.js              #   Alert CRUD
│       │
│       ├── components/                # Reusable UI Components
│       │   ├── ChartRenderer.jsx      #   Bar, Line, Pie, Scatter, Histogram, Heatmap
│       │   ├── ChatSidebar.jsx        #   Conversational AI chat panel
│       │   ├── VoiceRecorder.jsx      #   Speech-to-Text recording widget
│       │   ├── InsightDisplay.jsx     #   AI insight cards with icons
│       │   ├── ReportBuilder.jsx      #   PDF export with charts & insights
│       │   ├── NotificationBell.jsx   #   Alert notification dropdown
│       │   ├── Navbar.jsx             #   Collapsible sidebar navigation
│       │   ├── ErrorBoundary.jsx      #   Graceful error handling
│       │   ├── ConfirmModal.jsx       #   Reusable confirmation dialog
│       │   ├── SaveQueryModal.jsx     #   Save/bookmark query dialog
│       │   └── ProtectedRoute.jsx     #   Auth guard for routes
│       │
│       ├── context/                   # React Context Providers
│       │   ├── AuthContext.jsx         #   JWT auth state + auto-refresh
│       │   └── DashboardContext.jsx    #   Pinned dashboard widgets
│       │
│       ├── pages/                     # 14 Page Components
│       │   ├── Landing.jsx            #   Public marketing page
│       │   ├── Login.jsx              #   User authentication
│       │   ├── Register.jsx           #   User registration
│       │   ├── Dashboard.jsx          #   Power BI-style pinboard
│       │   ├── Upload.jsx             #   Dataset upload & management
│       │   ├── DataCleaning.jsx       #   Power Query-style cleaning editor
│       │   ├── Query.jsx              #   NL query interface + voice
│       │   ├── MultiQuery.jsx         #   Cross-dataset JOIN
│       │   ├── Forecast.jsx           #   Predictive analytics
│       │   ├── DataProfile.jsx        #   Statistical profiling dashboard
│       │   ├── History.jsx            #   Query history with re-run
│       │   ├── Compare.jsx            #   Side-by-side dataset comparison
│       │   ├── WhatIf.jsx             #   Scenario analysis
│       │   └── Alerts.jsx             #   Smart alert management
│       │
│       ├── styles/
│       │   └── global.css             #   Aether Flow design system (1900+ lines)
│       └── utils/
│           └── formatters.js          #   Number/date formatting helpers
│
├── backend/                           # FastAPI Application
│   ├── Dockerfile                     # Python 3.11 + ffmpeg
│   ├── requirements.txt               # 15 Python dependencies
│   ├── main.py                        # App entry point + CORS + routers
│   │
│   ├── api/                           # Route Handlers (11 routers)
│   │   ├── datasets.py                #   Upload, List, Delete, Profile, Schema
│   │   ├── queries.py                 #   NL Query, Clean, Forecast, Voice
│   │   ├── voice.py                   #   STT (Whisper) + TTS (gTTS)
│   │   ├── multi_query.py             #   Cross-dataset JOIN operations
│   │   ├── chat.py                    #   Conversational multi-turn chat
│   │   ├── compare.py                 #   Dataset comparison
│   │   ├── scenario.py                #   What-If analysis
│   │   ├── saved_queries.py           #   Query bookmarking
│   │   ├── alerts.py                  #   Smart alert CRUD + evaluation
│   │   └── reports.py                 #   PDF report generation
│   │
│   ├── auth/                          # Authentication
│   │   └── router.py                  #   Register, Login, Token refresh, Me
│   │
│   ├── core/
│   │   └── config.py                  #   Pydantic Settings (.env parsing)
│   │
│   ├── database/
│   │   ├── models.py                  #   SQLAlchemy ORM models
│   │   └── session.py                 #   Engine + Session factory
│   │
│   ├── llm/                           # LLM Integration
│   │   ├── llm_engine.py              #   Gemini API + keyword stub fallback
│   │   └── prompt_templates.py        #   Engineered prompts for code gen
│   │
│   ├── services/                      # Business Logic (15 modules)
│   │   ├── query_validator.py         #   AST syntax + blocked pattern checks
│   │   ├── query_executor.py          #   Sandboxed Pandas execution
│   │   ├── viz_selector.py            #   Auto chart type selection (7 types)
│   │   ├── insight_generator.py       #   Analyst-style textual insights
│   │   ├── anomaly_detector.py        #   Z-score + IQR outlier detection
│   │   ├── forecaster.py              #   Linear Regression + Moving Average
│   │   ├── schema_extractor.py        #   Column type + stats extraction
│   │   ├── data_profiler.py           #   Full dataset profiling
│   │   ├── data_validator.py          #   Upload validation
│   │   ├── data_differ.py             #   Dataset comparison engine
│   │   ├── context_manager.py         #   Conversation history tracking
│   │   ├── alert_engine.py            #   Threshold evaluation engine
│   │   ├── query_logger.py            #   Query history persistence
│   │   └── report_exporter.py         #   PDF generation service
│   │
│   ├── voice/                         # Voice Processing
│   │   └── processor.py               #   Audio transcription + synthesis
│   │
│   ├── tests/                         # Test Suite
│   │   ├── test_core.py               #   Unit tests for all services
│   │   └── accuracy_benchmark.py      #   67-test accuracy benchmark suite
│   │
│   └── utils/
│       └── helpers.py                 #   Shared utility functions
│
├── datasets/                          # Uploaded files (gitignored)
├── logs/                              # Application logs (gitignored)
├── docker-compose.yml                 # Full-stack container orchestration
├── .env                               # Environment variables (gitignored)
├── .gitignore                         # Git exclusion rules
└── README.md                          # This file
```

---

## Getting Started

### Prerequisites

| Software | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Backend runtime |
| **Node.js** | 18+ | Frontend build |
| **pip** | Latest | Python package manager |
| **npm** | Latest | Node package manager |
| **Git** | Latest | Version control |
| **Docker** *(optional)* | Latest | Containerized deployment |

### Local Setup (Manual)

#### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/aether-ai-platform.git
cd aether-ai-platform
```

#### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Database (use SQLite for quick local dev)
DATABASE_URL=sqlite:///./database.db

# For PostgreSQL (Neon):
# DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname?sslmode=require

# Security (generate a strong key for production)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM — Google Gemini (get free key at https://aistudio.google.com/apikeys)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173

# File Upload
UPLOAD_DIR=../datasets
MAX_FILE_SIZE_MB=50
```

#### 3. Start the Backend
```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend is live at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

#### 4. Start the Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend is live at: `http://localhost:5173`

#### 5. Use the Platform
1. Open `http://localhost:5173` in your browser
2. Register a new account
3. Upload a CSV or Excel file
4. Start asking questions in natural language!

---

### Docker Setup

One-command deployment with Docker Compose:

```bash
# Build and start all services (Backend + Frontend + PostgreSQL)
docker compose up --build

# Stop everything
docker compose down

# Stop and remove data volumes
docker compose down -v
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `sqlite:///./database.db` | Database connection string |
| `SECRET_KEY` | Yes | Auto-generated | JWT signing key |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key ([Get free key](https://aistudio.google.com/apikeys)) |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name |
| `FRONTEND_URL` | No | `http://localhost:5173` | CORS allowed origin |
| `UPLOAD_DIR` | No | `../datasets` | Dataset storage path |
| `MAX_FILE_SIZE_MB` | No | `50` | Max upload size |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT token TTL |

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create new account |
| `POST` | `/api/auth/login` | Login and get JWT tokens |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `GET` | `/api/auth/me` | Get current user info |

### Datasets
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/datasets/upload` | Upload CSV/Excel file |
| `GET` | `/api/datasets/` | List user's datasets |
| `GET` | `/api/datasets/{id}/schema` | Get dataset schema |
| `GET` | `/api/datasets/{id}/full-profile` | Get full data profile |
| `DELETE` | `/api/datasets/{id}` | Delete a dataset |

### Queries & Analysis
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/queries/` | Execute NL query |
| `POST` | `/api/queries/clean` | Clean dataset with NL instruction |
| `POST` | `/api/queries/forecast` | Generate forecast |
| `POST` | `/api/multi-query/join` | Cross-dataset JOIN |
| `POST` | `/api/compare/` | Compare two datasets |
| `POST` | `/api/scenario/` | What-If analysis |

### Voice
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/voice/transcribe` | Speech-to-Text |
| `POST` | `/api/voice/synthesize` | Text-to-Speech |

### Other
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/` | Multi-turn conversational chat |
| `GET/POST` | `/api/saved-queries/` | Saved query CRUD |
| `GET/POST` | `/api/alerts/` | Smart alert CRUD |
| `POST` | `/api/reports/generate` | Generate PDF report |
| `GET` | `/health` | Health check |

Full interactive API docs available at `/docs` (Swagger UI).

---

## Pipeline Accuracy

Measured across **67 automated tests** using the built-in accuracy benchmark suite:

| Component | Accuracy | Tests | Method |
|---|---|---|---|
| **Code Generation** | 100.0% | 15 NL queries | Valid syntax + executable + correct results |
| **Query Validation** | 100.0% | 20 tests | 10 safe code accepted, 10 dangerous code blocked |
| **Visualization Selector** | 83.3% | 6 tests | Correct chart type selection |
| **Insight Generator** | 100.0% | 6 checks | Highlights, summaries, rankings present |
| **Anomaly Detector** | 100.0% | 6 checks | Known injected outliers detected |
| **Forecaster** | 100.0% | 9 checks | R²=1.0 (linear), R²=0.983 (noisy data) |
| **End-to-End Pipeline** | 100.0% | 5 tests | Full NL → chart + insights |
| **Overall** | **97.6%** | **67** | |

Run the benchmark yourself:
```bash
cd backend
python -m tests.accuracy_benchmark
```

---

## Security Architecture

```
User Input (NL Query)
    │
    ▼
┌─────────────────────────┐
│  1. Gemini Code Gen     │  LLM generates Pandas code string
└────────────┬────────────┘
             │
    ▼
┌─────────────────────────┐
│  2. Regex Validation    │  Blocks: import, exec, eval, open, os.*, subprocess,
│                         │  to_csv, to_excel, .drop(), DELETE, DROP, etc.
└────────────┬────────────┘
             │
    ▼
┌─────────────────────────┐
│  3. AST Safety Check    │  Walks the Abstract Syntax Tree to block:
│                         │  • Dunder access (__class__, __mro__, __globals__)
│                         │  • Import statements
│                         │  • Dangerous calls (exec, eval, open, getattr)
└────────────┬────────────┘
             │
    ▼
┌─────────────────────────┐
│  4. Schema Validation   │  Checks column names against actual dataset schema
└────────────┬────────────┘
             │
    ▼
┌─────────────────────────┐
│  5. Sandboxed Execution │  • Runs on IN-MEMORY COPY (original never touched)
│                         │  • Restricted namespace: only df + pd available
│                         │  • __builtins__ = {} (no built-in functions)
│                         │  • 10-second timeout (kills infinite loops)
└────────────┬────────────┘
             │
    ▼
    Result (safe data only)
```

---

## Deployment Guide

### Deploying to Render.com (Free)

#### Backend (Web Service)
1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo, set **Root Directory** = `backend`, **Runtime** = Docker
4. Add environment variables (DATABASE_URL, GEMINI_API_KEY, SECRET_KEY, FRONTEND_URL)
5. Deploy

#### Frontend (Static Site)
1. New Static Site on Render
2. **Root Directory** = `frontend`
3. **Build Command** = `npm ci && npm run build`
4. **Publish Directory** = `dist`
5. Add env var: `VITE_API_URL` = your backend URL
6. Add Rewrite Rule: `/*` → `/index.html` (for SPA routing)

### Other Options
- **Railway.app** — Supports `docker-compose.yml` natively, $5/mo free credits
- **Vercel** (frontend) + **Render** (backend) — Best frontend performance

### Cost: $0/month
| Service | Free Tier |
|---|---|
| Render Backend | 750 hrs/month |
| Render Frontend | Unlimited (CDN) |
| Neon PostgreSQL | 0.5 GB storage |
| Gemini API | 1,500 requests/day |

---

## Testing

### Unit Tests
```bash
cd backend
pytest tests/ -v
```

Covers: Query Validator, Query Executor, Schema Extractor, Forecaster, Auth endpoints, Voice API, and Insight Generator.

### Accuracy Benchmark
```bash
cd backend
python -m tests.accuracy_benchmark
```

Runs 67 automated tests across all 7 pipeline components and outputs a detailed accuracy report.

### Production Build Check
```bash
cd frontend
npm run build    # Verifies the frontend compiles without errors
```

---

## Design Principles

| Principle | Implementation |
|---|---|
| **Security First** | Multi-layer validation (regex → AST → schema → sandbox) ensures LLM output is never executed blindly |
| **Separation of Concerns** | Frontend handles UI only; all business logic lives in 15 independent backend service modules |
| **Graceful Degradation** | If Gemini API is unavailable/exhausted, the keyword-based stub engine handles 15+ common query patterns |
| **Read-Only by Default** | All queries execute on in-memory DataFrame copies — original data is never mutated |
| **Modular Architecture** | Each service is independently testable and replaceable without affecting others |
| **Zero-Config Local Dev** | SQLite fallback + auto-generated SECRET_KEY means the app works without any configuration |

---

## Gemini API Quota

| Limit | Free Tier |
|---|---|
| Requests per minute | 15 RPM |
| Requests per day | 1,500 RPD |
| Daily reset time | Midnight Pacific Time (12:30 PM IST) |
| Per-query cost | ~3 API calls (code gen + narration + suggestions) |
| Effective queries/day | ~500 full queries |

When the quota is exhausted, the platform automatically falls back to the keyword-based stub engine — users still get results with no interruption.

---

## Future Enhancements

- [ ] Column-level context menu on data tables (rename, change type, filter)
- [ ] Dataset version history with undo/rollback
- [ ] Scheduled report delivery via email (SMTP integration ready)
- [ ] Multi-user collaboration with shared dashboards
- [ ] Export dashboards as interactive HTML
- [ ] Support for additional LLMs (OpenAI GPT, Claude, Llama)

---

## License

Academic project — all rights reserved.

---

<p align="center">
  Built with FastAPI, React, and Google Gemini AI
</p>
