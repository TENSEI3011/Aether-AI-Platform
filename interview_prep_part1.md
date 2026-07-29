# 🎯 Infosys Interview Prep — Part 1: Project Overview & Architecture

## PROJECT TITLE
**Generative AI–Led Analysis Platform for Non-Technical Business Users**

---

## Q1. Tell me about your project in brief.

**Answer:**
I built a full-stack intelligent data analysis platform that enables non-technical business users to query datasets using natural language — both text and voice. Instead of writing SQL or Python, a user simply types a question like "Show me average sales by region" and the platform uses Google Gemini AI to convert that into Pandas code, validates it for safety, executes it, auto-selects the best chart, generates analyst-style insights, detects anomalies, and even narrates the result using text-to-speech. The backend is built with FastAPI (Python), the frontend with React + Vite, and it uses PostgreSQL (Neon DB) for persistence. The entire app is containerised with Docker.

---

## Q2. What problem does your project solve?

**Answer:**
In most organisations, business users (marketing managers, HR leads, sales heads) depend on data analysts or developers to get insights from data. This creates a bottleneck — the analyst is busy, the business user waits. My platform eliminates this bottleneck by letting non-technical users upload a CSV/Excel file and ask questions in plain English. The AI handles the translation to code, the validation, execution, visualization, and insight generation — all automatically. It democratises data analysis.

---

## Q3. Explain the complete architecture of your project.

**Answer:**
The architecture is a **3-tier client-server model**:

### Tier 1 — Frontend (Presentation Layer)
- **React 18 + Vite** single-page application
- 13 pages: Login, Register, Dashboard, Upload, Query, History, DataProfile, MultiQuery, Forecast, Compare, Alerts, WhatIf, Landing
- 11 reusable components: ChartRenderer, ChatSidebar, ErrorBoundary, Navbar, VoiceRecorder, etc.
- Communicates with backend via REST API using Axios with JWT Bearer tokens
- Uses Recharts for data visualization (bar, line, pie, scatter, histogram, heatmap)

### Tier 2 — Backend (Application/Business Logic Layer)
- **FastAPI** (Python) with 11 route modules
- Modular service layer: LLM Engine, Query Validator, Query Executor, Schema Extractor, Insight Generator, Anomaly Detector, Forecaster, Viz Selector, Context Manager, Data Profiler, Voice (STT/TTS)
- JWT authentication with access + refresh tokens
- CORS middleware for cross-origin requests

### Tier 3 — Database (Data Layer)
- **PostgreSQL** via Neon DB (serverless) for production
- SQLite fallback for local development
- SQLAlchemy ORM with 8 tables: users, query_logs, conversation_ctx, dataset_records, saved_queries, scheduled_reports, smart_alerts, alert_notifications

### How They Connect:
```
User → React Frontend → Axios HTTP (JWT in header) → FastAPI Backend → 
  → LLM Engine (Gemini API) → Validator → Executor → Viz Selector → 
  → Insight Generator → Anomaly Detector → Response JSON → React → Charts
```

---

## Q4. What is the tech stack and why did you choose each technology?

| Layer | Technology | Why Chosen |
|-------|-----------|------------|
| Frontend | **React 18** | Component-based, virtual DOM for fast re-renders, huge ecosystem |
| Build Tool | **Vite** | 10x faster than webpack, instant HMR (Hot Module Replacement) |
| Charts | **Recharts** | Built specifically for React, declarative API, responsive |
| HTTP Client | **Axios** | Interceptors for JWT auto-refresh, cleaner API than fetch |
| Backend | **FastAPI** | Async support, automatic OpenAPI docs, Pydantic validation, fastest Python framework |
| ORM | **SQLAlchemy** | Industry standard, supports both PostgreSQL and SQLite |
| Auth | **python-jose + bcrypt** | JWT standard (RFC 7519), bcrypt is the gold standard for password hashing |
| LLM | **Google Gemini API** | Free tier, excellent code generation, fast response times |
| Database | **PostgreSQL (Neon)** | ACID compliant, serverless = zero infra management, free tier |
| Voice STT | **SpeechRecognition** | Free Google API, no API key needed |
| Voice TTS | **gTTS** | Free Google TTS, generates MP3, no API key needed |
| Containerisation | **Docker + Docker Compose** | Reproducible environments, easy deployment |
| PDF Export | **jsPDF + html2canvas** | Client-side PDF generation, no server load |

---

## Q5. How does the frontend communicate with the backend?

**Answer:**
The frontend uses **Axios** as the HTTP client. I created a centralised `axiosClient.js` that:

1. **Sets the base URL** to `http://localhost:8000` (backend)
2. **Request interceptor**: Automatically attaches the JWT access token from localStorage to every request's `Authorization: Bearer <token>` header
3. **Response interceptor**: If a 401 (Unauthorized) response comes back, it automatically calls the `/api/auth/refresh` endpoint with the refresh token, gets a new access token, stores it, and retries the original request — all transparently
4. **CORS**: The backend has CORS middleware that allows requests from `http://localhost:5173` (frontend URL)

This means the user never sees token expiry — the app silently refreshes tokens in the background.

---

## Q6. Explain your folder structure and why it's organised this way.

**Answer:**
I followed **Separation of Concerns** and **Modular Architecture**:

**Backend:**
- `api/` — Route handlers only (no business logic). Each file = one API domain (queries, datasets, voice, etc.)
- `auth/` — JWT token creation, verification, auth endpoints
- `core/` — App configuration via pydantic-settings (reads .env)
- `database/` — SQLAlchemy models and session factory
- `llm/` — LLM engine + prompt templates (isolated from routes)
- `services/` — All business logic: validator, executor, forecaster, etc. Each service is independently testable
- `voice/` — STT and TTS modules
- `tests/` — Unit tests (pytest)

**Frontend:**
- `api/` — HTTP client modules (one per backend domain)
- `components/` — Reusable UI components (ChartRenderer, ErrorBoundary, etc.)
- `context/` — React Context providers (AuthContext, DashboardContext)
- `hooks/` — Custom React hooks (useAuth, useDashboard)
- `pages/` — Page-level components (one per route)
- `styles/` — CSS design system
- `utils/` — Helper functions

This structure means each module can be developed, tested, and replaced independently.

---

## Q7. What design principles did you follow?

**Answer:**
1. **Security First** — LLM output is never executed directly; it passes through AST-level validation
2. **Separation of Concerns** — Frontend handles UI only; all business logic is in backend services
3. **Modularity** — Each backend module is independently testable and replaceable
4. **Read-Only Execution** — Queries run on in-memory copies of DataFrames; original data is never mutated
5. **Graceful Degradation** — If Gemini API is down or quota exhausted, a keyword-based stub engine generates valid Pandas code
6. **Defence in Depth** — Multiple layers of validation (regex patterns + AST walking + restricted namespace)
