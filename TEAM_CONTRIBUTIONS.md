# 🧠 Aether AI Platform — Team Contribution Guide

> **Project:** Generative AI-Led Data Analysis Platform  
> **Team Size:** 4 Members (2 Backend + 2 Frontend)  
> **Tech Stack:** FastAPI (Python) · React + Vite (JavaScript) · SQLAlchemy · Google Gemini AI · PostgreSQL · Docker

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Backend Team Contributions](#-backend-team-contributions)
4. [Frontend Team Contributions](#-frontend-team-contributions)
5. [Shared / DevOps Contributions](#-shared--devops-contributions)
6. [How to Answer "What Did You Contribute?"](#-how-to-answer-what-did-you-contribute)

---

## Project Overview

Aether AI is a **full-stack Generative AI platform** that allows non-technical business users to upload CSV/Excel datasets and ask natural-language questions like *"Show average sales by region"*. The platform uses **Google Gemini AI** to convert those questions into Pandas code, executes the code in a sandboxed environment, auto-selects the best chart type, generates analyst-style insights, and renders interactive visualizations — all without the user writing a single line of code.

---

## Architecture Summary

```
┌────────────────────────────────────────────────────┐
│                   FRONTEND (React + Vite)           │
│  Pages: Landing, Login, Register, Dashboard,        │
│         Upload, Cleaning, Query, History,            │
│         DataProfile, MultiQuery, Forecast,           │
│         Compare, Alerts, WhatIf                      │
│  Components: ChartRenderer, ChatSidebar, Navbar,     │
│         VoiceRecorder, ReportBuilder, etc.            │
│  State: AuthContext, DashboardContext                 │
│  HTTP: Axios with JWT interceptors + auto-refresh    │
├────────────────────────────────────────────────────┤
│                      REST API (JSON)                 │
├────────────────────────────────────────────────────┤
│                   BACKEND (FastAPI + Python)          │
│  API Routers: auth, datasets, queries, voice,        │
│         multi-query, saved-queries, alerts,           │
│         reports, compare, chat, scenario              │
│  Services: LLM Engine, Query Executor, Insight       │
│         Generator, Viz Selector, Forecaster,          │
│         Anomaly Detector, Data Profiler, etc.         │
│  Database: SQLAlchemy ORM → PostgreSQL / SQLite       │
│  AI: Google Gemini API with keyword-stub fallback     │
└────────────────────────────────────────────────────┘
```

---

## 🔧 BACKEND TEAM CONTRIBUTIONS

### Backend Member 1 — Core API, Authentication & Database

#### What You Built

**1. Authentication System (`backend/auth/`)**
- **`router.py`** — Built the complete auth flow with 4 REST endpoints:
  - `POST /api/auth/register` — User registration with **bcrypt** password hashing, input validation (regex for username, email format, password length), duplicate detection
  - `POST /api/auth/login` — Credential verification, returns JWT access + refresh token pair
  - `POST /api/auth/refresh` — Token rotation (exchange expired access token for new pair)
  - `GET /api/auth/me` — Returns authenticated user profile
- **`jwt_handler.py`** — Implemented JWT token lifecycle:
  - `create_access_token()` — Short-lived tokens (2 hours) with HS256 signing
  - `create_refresh_token()` — Long-lived tokens (7 days)
  - `get_current_user()` — FastAPI dependency that extracts & validates JWT from `Authorization: Bearer` header, queries DB for user
  - `decode_refresh_token()` — Validates refresh token type claim

**2. Database Layer (`backend/database/`)**
- **`models.py`** — Designed and implemented **8 SQLAlchemy ORM models**:
  - `User` — id, username, email, hashed_password, created_at
  - `QueryLog` — Logs every query: natural_query, generated_code, is_valid, result_summary, chart_type
  - `ConversationContext` — Persistent conversational memory (session_id, turn_index, query, code, explanation)
  - `DatasetRecord` — Metadata for uploads: dataset_id, filename, filepath, row_count, column_count, schema_summary
  - `SavedQuery` — Bookmarked query templates for one-click re-use
  - `ScheduledReport` — Automated report scheduling (daily/weekly/monthly)
  - `SmartAlert` — Alert rules with column, condition (gt/lt/eq/gte/lte), threshold
  - `AlertNotification` — Generated notifications when alerts fire
- **`session.py`** — Database session management:
  - Dual-dialect support: **PostgreSQL** (production) and **SQLite** (local dev)
  - Connection pooling for PostgreSQL (pool_size=5, max_overflow=10, pool_pre_ping, pool_recycle=300s)
  - `get_db()` FastAPI dependency with proper session cleanup

**3. Core Configuration (`backend/core/config.py`)**
- Centralized settings using **pydantic-settings** with `.env` file support
- Manages: JWT secrets, DB URL, Gemini API key, CORS origins, upload limits, SMTP config
- Auto-generates cryptographic secret if default is detected (security measure)

**4. Application Entry Point (`backend/main.py`)**
- FastAPI app initialization with lifespan events
- CORS middleware configuration (supports localhost + production URLs)
- Mounted **11 API routers** with proper prefixes and tags
- Health-check endpoint reporting LLM mode, model name, and DB dialect
- Dataset restoration from DB on startup

#### Key Technical Decisions You Made
- Used **bcrypt** directly instead of passlib wrapper for password hashing (simpler, fewer dependencies)
- Chose **HS256** JWT algorithm (symmetric) since backend is the only token issuer
- Designed dual-database support so team can develop locally with SQLite while deploying to PostgreSQL
- Used `pool_pre_ping=True` to handle Render's free-tier connection recycling

#### Potential Interview Questions for You
- *"How does your JWT refresh flow work?"* → Explain access/refresh token pair, 401 interception, token rotation
- *"How did you secure passwords?"* → bcrypt hashing with random salt, never storing plaintext
- *"Why dual database support?"* → Local development ease with SQLite, production reliability with PostgreSQL
- *"How do you handle database sessions in FastAPI?"* → `get_db()` dependency with `yield` and `finally: close()`

---

### Backend Member 2 — AI Engine, Services & Business Logic

#### What You Built

**1. LLM Engine (`backend/llm/`)**
- **`llm_engine.py`** — The core AI brain of the platform (631 lines):
  - `generate_code()` — Converts natural language → Pandas code using **Google Gemini API**
  - `generate_narration()` — Produces 2-3 sentence analyst-style narrative summaries
  - `generate_suggestions()` — Generates 3 smart follow-up questions based on current query + result
  - **Keyword-based stub fallback** — When Gemini API is unavailable (no key / quota exhausted), uses intelligent keyword matching + schema-aware column extraction to generate valid Pandas code
  - Handles 10+ query patterns: average, sum, count, correlation, trend, outlier, clustering, risk analysis, comparison, ranking
  - Response parsing: extracts code from markdown fences, cleans explanations
  - Graceful degradation on API errors (429 quota, network failures)
- **`prompt_templates.py`** — Structured prompts for Gemini with schema context and conversation history

**2. Query Processing Pipeline (`backend/services/`)**
- **`query_executor.py`** — Secure sandboxed code execution:
  - **AST-level safety** — Walks the Abstract Syntax Tree to block dangerous patterns (`__class__`, `__mro__`, `__subclasses__`, imports, exec/eval/open calls)
  - Executes on an **in-memory DataFrame copy** (original never mutated)
  - Restricted namespace: only `df` and `pd` available, `__builtins__` set to empty dict
  - **Cross-platform timeout** (10 seconds) using threading to prevent infinite loops
  - Handles DataFrame, Series, scalar, and string results with proper JSON serialization
- **`query_validator.py`** — Validates generated code before execution (dangerous pattern detection)
- **`schema_extractor.py`** — Extracts column names, types (numeric/categorical/datetime/boolean), and sample values for LLM context

**3. Intelligence Services (`backend/services/`)**
- **`insight_generator.py`** — Generates analyst-style textual insights:
  - Detects highest/lowest values with label context (e.g., "Kolkata records highest NO₂ at 56.25")
  - Calculates ratios ("3.2× higher than Aizawl")
  - Produces top-3 rankings, spread observations, trend detection (first-half vs second-half comparison)
  - Special handling for correlation matrices and scalar results
- **`viz_selector.py`** — Auto-selects the best chart type based on data shape:
  - Category + Numeric → Bar chart
  - DateTime + Numeric → Line chart
  - Small categories (≤6) → Pie chart
  - Two numeric, many rows → Scatter plot
  - Single numeric → Histogram
  - Square numeric matrix → Heatmap
  - Supports manual override via `graph_type` parameter
- **`anomaly_detector.py`** — Outlier detection using dual methods:
  - **Z-score method** (flags |z| > 3)
  - **IQR method** (flags values outside Q1-1.5×IQR to Q3+1.5×IQR)
  - Returns flagged points with messages for chart highlighting
- **`forecaster.py`** — Time-series prediction:
  - **Linear regression** with R² confidence score, trend detection (rising/falling/stable)
  - **Moving average** with configurable window size
  - Generates human-readable forecast summaries
- **`data_profiler.py`** — Comprehensive dataset profiling:
  - Shape, memory usage, duplicate detection
  - Missing value analysis (count + percentage per column)
  - Data type distribution (numeric/datetime/boolean/categorical)
  - Top-5 values for categorical columns
  - Descriptive statistics + correlation matrix for numeric columns
- **`data_validator.py`** — Upload validation:
  - File format checking (CSV, XLSX, XLS)
  - Missing value detection, duplicate row counting
  - Mixed-type column detection (>80% numeric = likely data error)
- **`context_manager.py`** — Conversational memory (DB-backed):
  - Hybrid approach: in-memory dict for fast access + PostgreSQL for persistence across restarts
  - Scoped by (session_id, dataset_id) to prevent cross-dataset hallucinations
  - Builds formatted context strings for follow-up queries
  - Auto-trims to last 6 conversation turns
- **`data_differ.py`** — Dataset comparison service
- **`query_logger.py`** — Logs all queries to database for history tracking
- **`report_exporter.py`** — Server-side report generation

**4. Voice Processing (`backend/voice/`)**
- **`stt.py`** — Speech-to-Text using SpeechRecognition + Google's free API
  - Supports WAV directly, converts webm/mp3/ogg via pydub
  - Graceful fallbacks if libraries are missing
- **`tts.py`** — Text-to-Speech using **gTTS** (Google Text-to-Speech)
  - Returns base64-encoded MP3 audio
  - Duration estimation, text truncation (1000 char limit)

**5. API Routers (`backend/api/`)**
- **`queries.py`** — Main query endpoint orchestrating the full pipeline: LLM → validate → execute → insights → viz → anomalies → narration → suggestions
- **`datasets.py`** — File upload, listing, deletion, data cleaning operations (drop nulls, fill mean/median/mode, remove duplicates, drop columns)
- **`chat.py`** — Conversational AI chat with context memory
- **`multi_query.py`** — Cross-dataset querying
- **`alerts.py`** — CRUD for smart alert rules + checking/triggering
- **`reports.py`** — Report scheduling and generation
- **`compare.py`** — Side-by-side dataset comparison
- **`scenario.py`** — What-if scenario simulation
- **`saved_queries.py`** — Save/load/delete query bookmarks
- **`voice.py`** — Voice input/output endpoints

#### Key Technical Decisions You Made
- **Sandboxed execution with AST checking** — Prevents code injection attacks (blocks `__class__.__mro__.__subclasses__()` traversal)
- **Keyword-based stub fallback** — Platform works even without Gemini API key
- **Dual outlier detection** — Z-score catches global outliers, IQR catches distribution outliers
- **Hybrid context management** — In-memory for speed, DB-backed for persistence

#### Potential Interview Questions for You
- *"How do you safely execute AI-generated code?"* → AST safety check, restricted namespace, in-memory copy, timeout protection
- *"How does the NL-to-code pipeline work?"* → Schema extraction → prompt building → Gemini API → code extraction → validation → sandboxed execution
- *"How does your anomaly detector work?"* → Z-score (statistical deviation) + IQR (distribution-based), dual methods reduce false negatives
- *"How does conversational context work?"* → DB-backed memory scoped by session+dataset, builds formatted history string for LLM prompt

---

## 🎨 FRONTEND TEAM CONTRIBUTIONS

### Frontend Member 1 — Core Pages, Routing & State Management

#### What You Built

**1. Application Shell (`frontend/src/`)**
- **`App.jsx`** — Root component with:
  - React Router v7 with 14 routes (2 public + 12 protected)
  - `<ProtectedRoute>` wrapper checking JWT before rendering
  - Animated mesh gradient background
  - Sidebar layout with ChatSidebar always accessible
  - ErrorBoundary wrapper for graceful error handling

**2. Authentication Pages**
- **`Login.jsx`** — Login form with:
  - Username/password fields with validation
  - Error display for invalid credentials
  - Redirect to dashboard on success
  - "Register" link for new users
- **`Register.jsx`** — Registration form with:
  - Username, email, password fields
  - Client-side validation (username format, email format, password length)
  - Real-time error feedback
  - Auto-login after successful registration

**3. State Management**
- **`AuthContext.jsx`** — JWT authentication state:
  - Stores user object and token in React Context
  - `login()` — Calls API, saves access + refresh token to localStorage
  - `register()` — Same flow with registration endpoint
  - `logout()` — Clears localStorage and state
  - Auto-validates existing token on app mount via `getMe()` call
- **`DashboardContext.jsx`** — Dashboard panel management:
  - Power BI-style multi-chart dashboard with localStorage persistence
  - `addPanel()` / `removePanel()` / `clearPanels()` operations
  - react-grid-layout integration (12-column grid, drag/resize)
  - Layout positions stored separately for persistence
- **Custom Hooks:**
  - `useAuth.js` — Convenience hook for consuming AuthContext
  - `useDashboard.js` — Convenience hook for consuming DashboardContext

**4. Core Data Pages**
- **`Dashboard.jsx`** — Power BI-style dashboard:
  - Displays pinned chart panels in a draggable/resizable grid
  - Each panel shows query, chart, and insights
  - "Clear All" and per-panel remove buttons
  - Empty state with guidance
- **`Upload.jsx`** — Dataset upload page:
  - Drag-and-drop file upload (CSV/Excel)
  - File size validation (50MB limit)
  - Upload progress indicator
  - Dataset list with metadata (rows, columns, upload date)
  - Delete dataset functionality
- **`DataCleaning.jsx`** — Data cleaning operations:
  - Drop null rows, fill missing values (mean/median/mode)
  - Remove duplicates, drop specific columns
  - Before/after preview with data quality metrics
  - Operation history tracking
- **`History.jsx`** — Query history page:
  - Lists all past queries with timestamps
  - Shows generated code, chart type, and validity
  - Re-run queries with one click
- **`Landing.jsx`** — Public landing page with feature showcase

**5. API Client Layer (`frontend/src/api/`)**
- **`axiosClient.js`** — Configured Axios instance:
  - Automatic JWT attachment via request interceptor
  - **401 auto-refresh** — On 401 response, queues failed requests, refreshes token, retries all queued requests
  - Failed queue pattern prevents duplicate refresh calls
  - Auto-redirect to login on refresh failure
- **`auth.js`** — Login, register, getMe API calls
- **`datasets.js`** — Upload, list, delete, clean dataset calls
- **`queries.js`** — Query execution API calls
- **`health.js`** — Backend health check

#### Key Technical Decisions You Made
- **Token refresh with request queuing** — Multiple simultaneous 401s don't trigger multiple refresh calls
- **localStorage for dashboard persistence** — Panels survive page refreshes and browser restarts
- **react-grid-layout** — Enables Power BI-style drag/resize dashboard without building custom layout engine

#### Potential Interview Questions for You
- *"How does your auth flow work end-to-end?"* → Register/login → JWT stored in localStorage → Axios interceptor attaches to every request → 401 triggers auto-refresh → Failure redirects to login
- *"How did you handle token expiration?"* → Axios response interceptor catches 401, queues failed requests, calls refresh endpoint, retries all queued with new token
- *"How does the dashboard work?"* → DashboardContext stores panels in localStorage, react-grid-layout provides drag/resize, each panel renders ChartRenderer with pinned query data

---

### Frontend Member 2 — Visualization, Components & Advanced Features

#### What You Built

**1. Data Visualization**
- **`ChartRenderer.jsx`** — Universal chart component (276 lines) using **Recharts**:
  - **7 chart types**: Bar, Line, Pie, Scatter, Histogram, Heatmap, Data Table
  - **Anomaly highlighting** — Red reference dots on anomalous data points
  - Custom histogram binning algorithm (15 bins)
  - Custom heatmap with blue→purple→red gradient color mapping
  - Responsive containers that adapt to screen size
  - Dark-themed tooltips matching platform design
  - Chart type icons and auto-generated titles with reasoning

**2. Interactive Components**
- **`ChatSidebar.jsx`** — Conversational AI chat panel:
  - Slide-in sidebar accessible from any page
  - Message history with user/AI bubbles
  - Context-aware follow-up questions
  - Session management (new chat, clear history)
- **`VoiceRecorder.jsx`** — Voice input component:
  - **Primary**: Browser's Web Speech API (instant, no server round-trip)
  - **Fallback**: MediaRecorder → backend STT endpoint
  - Live recording indicator with pulsing animation
  - Real-time transcript preview
  - Error handling (no speech, mic denied, API failures)
  - Auto-cleanup on component unmount
- **`ReportBuilder.jsx`** — PDF report generator:
  - Branded cover page (dark theme, purple accents)
  - Two report types: Executive Summary vs Detailed Analysis
  - AI narration and insight highlights
  - Data table with top 30 rows
  - Uses **jsPDF** for client-side PDF generation
- **`InsightDisplay.jsx`** — Renders AI-generated insights with formatted highlights
- **`NotificationBell.jsx`** — Alert notification dropdown in navbar
- **`SaveQueryModal.jsx`** — Modal for saving queries as bookmarks
- **`ConfirmModal.jsx`** — Reusable confirmation dialog
- **`ErrorBoundary.jsx`** — React error boundary with fallback UI
- **`Navbar.jsx`** — Collapsible sidebar navigation with animated icons
- **`ProtectedRoute.jsx`** — Route guard checking auth state

**3. Advanced Feature Pages**
- **`Query.jsx`** — Main query page (the heart of the app):
  - Natural language input with voice support
  - Dataset and chart type selectors
  - Results display: chart + data table + insights + narration
  - "Pin to Dashboard" and "Save Query" actions
  - AI-generated follow-up suggestions
  - Conversation context (follow-up queries)
- **`Forecast.jsx`** — Time-series forecasting page:
  - Column selector for x-axis (time) and y-axis (metric)
  - Method selection (Linear Regression vs Moving Average)
  - Configurable forecast periods
  - Combined historical + forecast chart
  - Trend indicator and confidence score
- **`MultiQuery.jsx`** — Cross-dataset query page:
  - Select multiple datasets
  - Run same query across all
  - Side-by-side result comparison
- **`Alerts.jsx`** — Smart alerts management:
  - Create alert rules (column, condition, threshold)
  - Active/inactive toggle
  - Alert history with triggered notifications
- **`Compare.jsx`** — Dataset comparison page
- **`WhatIf.jsx`** — Scenario simulation page
- **`DataProfile.jsx`** — Rich dataset profiling dashboard:
  - Overview cards (rows, columns, memory, duplicates)
  - Missing value analysis chart
  - Data type distribution
  - Categorical column top values
  - Numeric descriptive statistics
  - Correlation matrix heatmap

**4. Styling & Design System (`frontend/src/styles/`)**
- **`variables.css`** — Complete CSS design token system:
  - Color palette (dark theme + light mode support)
  - Typography scale, spacing scale, border radii
  - Shadow system, transition presets
  - Glassmorphism variables
- **`global.css`** — 48KB of premium styling:
  - Animated mesh gradient background
  - Glassmorphism card effects
  - Staggered page entry animations
  - Skeleton loading states
  - Button hover/active micro-animations
  - Responsive breakpoints
  - Custom scrollbar styling
  - Voice recording pulse animation

**5. Utility Layer**
- **`pdfReport.js`** — PDF generation utilities
- **`helpers.js`** — Shared formatting and utility functions
- Remaining API modules: `alerts.js`, `chat.js`, `compare.js`, `multiQuery.js`, `reports.js`, `savedQueries.js`, `scenario.js`, `voice.js`

#### Key Technical Decisions You Made
- **Recharts over Chart.js** — Better React integration, declarative API, built-in responsiveness
- **Client-side PDF generation** — No server round-trip needed, works offline
- **Web Speech API primary + MediaRecorder fallback** — Instant transcription when browser supports it, server fallback for older browsers
- **Custom heatmap rendering** — HTML table with computed gradient colors instead of a charting library (more control, better dark theme integration)

#### Potential Interview Questions for You
- *"How does your chart system auto-select the right visualization?"* → Backend viz_selector analyzes column types and data shape, frontend ChartRenderer receives the recommendation and renders the appropriate Recharts component
- *"How did you implement voice input?"* → Two-layer: Web Speech API for instant browser-side transcription, MediaRecorder + backend STT as fallback
- *"How does the PDF report work?"* → jsPDF generates multi-page branded PDF client-side with cover page, insights section, and data table
- *"How do you highlight anomalies on charts?"* → Backend returns anomaly_indices per column, ChartRenderer filters data points by those indices and renders red ReferenceDot overlays

---

## 🐳 Shared / DevOps Contributions

These were done collaboratively by the team:

| Item | File | What It Does |
|------|------|-------------|
| Docker Compose | `docker-compose.yml` | Orchestrates 3 containers: PostgreSQL, FastAPI backend, React frontend |
| Backend Dockerfile | `backend/Dockerfile` | Python 3.11 slim image, installs deps, runs uvicorn |
| Frontend Dockerfile | `frontend/Dockerfile` | Node 18 image, builds Vite app, serves static files |
| Environment Config | `.env` | All secrets: DB URL, Gemini API key, JWT secret, SMTP creds |
| Git Ignore | `.gitignore` | Excludes node_modules, __pycache__, .env, datasets, logs |
| Dependencies | `requirements.txt` / `package.json` | Backend: 14 packages · Frontend: 8 packages |
| Testing | `backend/tests/` | Core unit tests + accuracy benchmarks |

---

## 💬 How to Answer "What Did You Contribute?"

### Template Answer (Backend Member 1):
> *"I built the **authentication system** with JWT-based login, registration, and token refresh. I designed the **database schema** with 8 tables using SQLAlchemy ORM, including user management, query logging, and conversational context persistence. I also set up the **core configuration** layer and the **FastAPI application** with CORS, middleware, and 11 API routers. My key security contribution was implementing bcrypt password hashing and auto-generated cryptographic secrets."*

### Template Answer (Backend Member 2):
> *"I built the **AI engine** that converts natural language to Pandas code using Google Gemini, with an intelligent keyword-based fallback. I implemented the **secure sandboxed execution** layer with AST-level safety checks, restricted namespaces, and timeout protection. I also built all the intelligence services — **anomaly detection** (Z-score + IQR), **time-series forecasting** (linear regression + moving average), **auto-visualization selection**, **insight generation**, and **conversational memory management**. I also built the voice processing pipeline (STT + TTS)."*

### Template Answer (Frontend Member 1):
> *"I built the **application shell** with React Router, protected routes, and the auth flow. I implemented **JWT state management** with auto-refresh token rotation using Axios interceptors. I built the **Dashboard** page with a Power BI-style drag/resize grid, the **Upload** page with drag-and-drop file handling, the **Data Cleaning** page, and the **Query History** page. I also set up the **API client layer** with automatic token attachment and 401 retry logic."*

### Template Answer (Frontend Member 2):
> *"I built the **visualization system** supporting 7 chart types (bar, line, pie, scatter, histogram, heatmap, table) with anomaly highlighting using Recharts. I implemented the **voice input** component with Web Speech API + MediaRecorder fallback, the **PDF report generator** using jsPDF, the **conversational chat sidebar**, and the **notification system**. I also built all the advanced feature pages — **Forecast**, **Multi-Query**, **Alerts**, **What-If**, **Compare**, and **Data Profile**. I designed the entire **CSS design system** with glassmorphism, micro-animations, and dark theme."*

---

> 📌 **Tip:** When asked follow-up questions, refer to the specific file names and function names listed above. Being specific about implementation details (e.g., "I used AST walking to block dunder attribute traversal") demonstrates deep ownership of the code.
