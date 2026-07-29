# Aether AI — Project Interview Guide
### Generative AI-Led Data Analysis Platform (Minor Project)

---

## 1. Why This Project?

### The Problem
Traditional data analysis creates a massive skill barrier. To extract insights from data, a user typically needs to know:
- **SQL** to query databases
- **Python/Pandas** to manipulate and transform data
- **Matplotlib/Tableau** to visualize results
- **Statistics** to interpret findings

Most business users — managers, analysts, marketing teams, small business owners — lack these skills. They depend on data engineers or BI teams, creating bottlenecks where a simple question like *"What were our top 5 products last quarter?"* can take days to get answered.

### Our Solution
We built **Aether AI**, a platform where users simply type or speak their questions in plain English, and the system automatically:
1. Generates the correct Pandas code using Google Gemini AI
2. Validates and sandboxes the code for safety
3. Executes it on the uploaded dataset
4. Selects the best chart type automatically
5. Generates analyst-style insights and detects anomalies
6. Narrates the results via Text-to-Speech

### Why It Matters
- **Democratizes data analysis** — anyone can query data without writing code
- **Reduces turnaround time** from days to seconds
- **Addresses a real industry need** — the low-code/no-code analytics market is projected to reach $47B by 2028
- **Combines multiple AI capabilities** (LLM code generation, anomaly detection, forecasting, voice) into a single cohesive platform

### Academic Relevance
This project explores the intersection of **Generative AI, NLP, and Data Science** — demonstrating how LLMs can be safely integrated into real-world applications with proper sandboxing, validation, and fallback mechanisms.

---

## 2. Features Explained

### Core Analysis Pipeline

| Feature | How It Works |
|---|---|
| **Natural Language Querying** | User types a question like *"Show average salary by department"* → Gemini AI generates Pandas code → Code is validated (regex + AST) → Executed in a sandboxed environment → Results returned with auto-selected chart |
| **Voice Input/Output** | Users can record voice queries (converted via Speech-to-Text using Whisper) and listen to AI-generated narration of results (via gTTS Text-to-Speech) |
| **Auto-Visualization** | The system analyzes the query result structure (number of columns, data types, cardinality) and automatically selects the best chart: Bar, Line, Pie, Scatter, Histogram, Heatmap, or Table |
| **AI Insights** | After every query, the system generates analyst-style textual insights — rankings, comparisons, percentage breakdowns, trend summaries — so users don't have to interpret raw numbers |
| **Anomaly Detection** | Uses Z-score and IQR (Interquartile Range) methods to automatically detect outliers in query results, flagging unusual data points with contextual explanations |
| **Smart Suggestions** | After each query, Gemini generates 3–4 relevant follow-up questions so users can continue exploring without thinking of what to ask next |

### Data Management

| Feature | How It Works |
|---|---|
| **Dataset Upload** | Supports CSV and Excel (.xlsx) files. On upload, the system auto-extracts schema (column names, types, sample values) and stores metadata in the database |
| **Data Profiling** | Generates a comprehensive statistical profile: mean, median, std, distributions, correlation matrix, missing value counts, unique value counts per column |
| **Power BI-Style Data Cleaning** | A dedicated cleaning page with 10+ quick actions: Remove Duplicates, Fill Nulls (mean/median/mode), Drop Columns, Trim Whitespace, Rename Columns, Type Conversion, and Natural Language cleaning instructions |
| **Applied Steps Log** | Every cleaning action is logged with before/after row counts, creating a full audit trail (inspired by Power BI's Applied Steps) |

### Advanced Analytics

| Feature | How It Works |
|---|---|
| **Predictive Forecasting** | Uses Linear Regression and Moving Average models to forecast future values. Shows confidence intervals and R² scores so users know how reliable the prediction is |
| **Multi-Dataset JOIN** | Upload multiple datasets and join them on common keys (like SQL JOINs). The system auto-detects potential join keys based on matching column names |
| **What-If Scenario Analysis** | Users adjust input variables (e.g., "What if marketing budget increases by 20%?") and see predicted impact on target metrics |
| **Dataset Comparison** | Side-by-side statistical comparison of two datasets — highlights differences in distributions, means, missing values |
| **Smart Alerts** | Users set threshold-based alerts (e.g., "Alert me if AQI > 300") that are evaluated against their data |

### Enterprise Features

| Feature | How It Works |
|---|---|
| **Dashboard Builder** | Pin any query result (chart + insights) to a Power BI-style drag-and-drop dashboard. Layout is persistent across sessions using React Grid Layout |
| **PDF Report Export** | Generate branded PDF reports containing selected charts, insights, and AI narration using jsPDF + html2canvas |
| **Query History** | Full searchable history of past queries with ability to re-run, save/bookmark, and view past results |
| **Conversational Chat** | Multi-turn contextual chat sidebar where the AI remembers previous questions for follow-up analysis |
| **Notification System** | Real-time alert notifications with a bell icon in the navbar |

### Security Features

| Feature | How It Works |
|---|---|
| **JWT + Refresh Tokens** | Secure authentication — access tokens expire in 60 minutes, refresh tokens allow seamless re-authentication without re-login |
| **AST-Level Sandboxing** | LLM-generated code goes through 4 validation layers: Regex checks → AST tree walking → Schema validation → Sandboxed execution with empty `__builtins__` |
| **Read-Only Execution** | All queries run on in-memory DataFrame copies — the original uploaded data is never modified |
| **Dataset Ownership** | Users can only access datasets they uploaded — enforced at the API level via JWT user ID |

---

## 3. Tech Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **React** | 19 | UI framework — component-based architecture with hooks |
| **Vite** | 7 | Build tool — extremely fast HMR (Hot Module Replacement) during development |
| **React Router** | 7 | Client-side routing for SPA navigation (14 pages) |
| **Recharts** | Latest | Chart library for Bar, Line, Pie, Scatter, Histogram, Heatmap |
| **React Grid Layout** | Latest | Drag-and-drop dashboard grid (Power BI-style) |
| **jsPDF + html2canvas** | Latest | Client-side PDF report generation |
| **Axios** | Latest | HTTP client with JWT interceptor for automatic token attachment |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.104+ | Python web framework — async support, automatic OpenAPI docs, Pydantic validation |
| **SQLAlchemy** | 2.0 | ORM for database operations (models: users, datasets, query_logs, saved_queries, alerts) |
| **Pandas** | 2.2+ | Core data manipulation engine — all NL queries translate to Pandas code |
| **NumPy** | Latest | Numerical computations for forecasting and anomaly detection |
| **Pydantic** | 2.5+ | Request/response validation and settings management |

### AI & ML
| Technology | Purpose |
|---|---|
| **Google Gemini 2.0 Flash** | LLM for code generation, insight narration, follow-up suggestions, and NL cleaning instructions |
| **Keyword-Based Stub Engine** | Fallback engine when Gemini API quota is exhausted — handles 15+ common query patterns |
| **Linear Regression** | Forecasting model (from NumPy polyfit) |
| **Moving Average** | Secondary forecasting model |
| **Z-Score + IQR** | Statistical methods for anomaly/outlier detection |

### Authentication & Security
| Technology | Purpose |
|---|---|
| **python-jose** | JWT token creation and verification |
| **bcrypt** | Password hashing (one-way, salted) |
| **AST module** | Python's Abstract Syntax Tree module for code safety validation |

### Voice
| Technology | Purpose |
|---|---|
| **Whisper (OpenAI)** | Speech-to-Text transcription |
| **gTTS** | Google Text-to-Speech — converts AI narration to audio (free, no API key needed) |

### Database
| Technology | Purpose |
|---|---|
| **PostgreSQL (Neon Serverless)** | Production database — serverless, auto-scaling, free tier |
| **SQLite** | Local development fallback — zero configuration needed |

### DevOps & Deployment
| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Containerized deployment — one-command setup for entire stack |
| **Render.com** | Cloud deployment (free tier: 750 hrs/month backend + unlimited static frontend) |
| **Git + GitHub** | Version control and CI/CD |

### Design System
| Technology | Purpose |
|---|---|
| **Aether Flow** | Custom design system — dark glassmorphism theme, animated mesh gradient backgrounds, 1900+ lines of CSS |

---

## 4. Team and My Role

### Team Composition
This was a **minor project** built by a team of students as part of our academic curriculum.

### My Role
I was the **Full-Stack Developer and Project Lead**, responsible for:

**Architecture & Design:**
- Designed the overall system architecture (React frontend ↔ FastAPI backend ↔ PostgreSQL database)
- Designed the multi-layer security pipeline for safe LLM code execution
- Created the "Aether Flow" design system with glassmorphism aesthetics

**Backend Development:**
- Built the entire FastAPI backend with 11 API routers and 15 service modules
- Implemented the NL-to-Pandas query pipeline: prompt engineering → Gemini code generation → AST validation → sandboxed execution
- Built the forecasting engine (Linear Regression + Moving Average)
- Implemented anomaly detection (Z-score + IQR)
- Designed the JWT authentication system with refresh token rotation
- Integrated Voice (STT + TTS) pipeline

**Frontend Development:**
- Built 14 React pages and 11 reusable components
- Implemented the Power BI-style drag-and-drop dashboard
- Built the data cleaning interface with applied steps log
- Designed responsive layouts with the Aether Flow dark theme

**DevOps:**
- Dockerized the entire application (multi-stage builds for frontend + backend)
- Deployed to Render.com (backend as Docker web service + frontend as static site)
- Configured Neon PostgreSQL for serverless production database

---

## 5. Why This Particular Tech Stack?

### Why React (not Angular/Vue)?
- **Component reusability** — 11 components shared across 14 pages (ChartRenderer alone is used on 5 pages)
- **Ecosystem maturity** — largest community, most libraries (Recharts, React Grid Layout, etc.)
- **Hooks + Context API** — eliminated need for Redux; AuthContext and DashboardContext handle all shared state
- **React 19** provides improved performance with automatic batching

### Why FastAPI (not Flask/Django)?
- **Async support** — critical for concurrent AI API calls (Gemini responses take 2–5 seconds)
- **Automatic OpenAPI docs** — Swagger UI at `/docs` for free, no manual API documentation needed
- **Pydantic validation** — request/response models validated automatically, reducing boilerplate
- **Performance** — FastAPI is 3–10x faster than Flask for I/O-bound workloads (our exact use case: API calls + DB queries)
- **Type safety** — Python type hints enforced at runtime

### Why Google Gemini (not GPT-4/Claude)?
- **Free tier** — 1,500 requests/day at zero cost (GPT-4 costs $0.03/1K tokens)
- **Gemini 2.0 Flash** — optimized for speed (1–3 second responses vs. 5–10 seconds for GPT-4)
- **Code generation quality** — in our 67-test benchmark, Gemini achieved 100% code generation accuracy for Pandas queries
- **Easy integration** — Google's `google-genai` Python SDK is straightforward

### Why Pandas (not SQL-based querying)?
- **Flexibility** — Pandas can handle complex aggregations, pivots, and transformations that would require verbose SQL
- **In-memory processing** — no need to load data into a database first; users upload CSV/Excel and query immediately
- **Rich output** — Pandas DataFrames easily convert to JSON for charting, unlike raw SQL result sets

### Why PostgreSQL + Neon (not MongoDB/Firebase)?
- **Relational data** — our data model (users → datasets → queries → alerts) is inherently relational
- **SQLAlchemy ORM** — mature, well-documented, handles migrations
- **Neon Serverless** — auto-scales, free tier (0.5 GB), no server management, auto-sleep on inactivity
- **SQLite fallback** — same SQL interface for local dev, zero configuration

### Why Docker?
- **Reproducibility** — "works on my machine" eliminated; same environment everywhere
- **One-command deployment** — `docker compose up` starts backend + frontend + database
- **Render.com compatibility** — Render natively supports Dockerfiles for deployment

### Why Custom CSS (Aether Flow) and not Tailwind/Material UI?
- **Full design control** — glassmorphism effects (backdrop-filter, blur, transparency) require precise CSS control
- **Performance** — no framework overhead; 1900 lines of purpose-built CSS
- **Unique identity** — branded design system that doesn't look like every other Material UI app

---

## 6. Difficulties Faced While Building This Project

### 1. LLM Code Safety (Critical Challenge)
**Problem:** Gemini generates arbitrary Python code from user input. A malicious user could ask *"Delete all files on the server"* and the LLM might generate `os.system('rm -rf /')`.

**Solution:** Built a 4-layer security pipeline:
1. **Regex filter** — blocks `import`, `exec`, `eval`, `open`, `os.*`, `subprocess`, `to_csv`, `.drop()`, etc.
2. **AST walker** — traverses the Abstract Syntax Tree to block dunder access (`__class__`, `__globals__`), import nodes, and dangerous function calls
3. **Schema validator** — ensures generated code only references columns that exist in the actual dataset
4. **Sandboxed execution** — runs with `__builtins__ = {}` (no built-in functions available), only `df` and `pd` in namespace, 10-second timeout

**Difficulty level:** This was the hardest part of the project. Balancing safety with functionality required weeks of testing and edge-case hunting.

### 2. Gemini API Rate Limiting
**Problem:** Free tier allows only 15 requests/minute and 1,500/day. Each query makes ~3 API calls (code gen + narration + suggestions), so heavy testing burned through the quota quickly.

**Solution:**
- Built a **keyword-based stub fallback engine** that handles 15+ common query patterns (e.g., "show top N", "average of X by Y") without touching the API
- Implemented **response caching** for identical queries
- Optimized prompts to reduce token count

### 3. CORS Issues During Deployment
**Problem:** Frontend on Vercel/Render's CDN couldn't communicate with backend on a different Render domain due to Cross-Origin Resource Sharing restrictions.

**Solution:**
- Configured FastAPI's `CORSMiddleware` with explicit `allow_origins` matching the frontend URL
- Added proper `allow_credentials=True` for JWT cookie handling
- Learned to differentiate between CORS preflight (`OPTIONS`) requests and actual requests

### 4. Data Cleaning Logic — "Fill Mean" Bug
**Problem:** The "Fill with Mean" cleaning action was accidentally dropping rows instead of filling null values, because the logic was applying a filter mask instead of `fillna()`.

**Solution:** Debugged by adding before/after row count logging to every cleaning operation, identified the off-by-one error, and refactored to use proper Pandas `fillna(df[col].mean())` calls.

### 5. Chart Type Auto-Selection Accuracy
**Problem:** The visualization selector initially picked wrong chart types — showing pie charts for 50+ categories (unreadable) or bar charts for time-series data.

**Solution:** Built a rule-based selector considering:
- Number of unique values (cardinality) — pie only for <8 categories
- Data types (datetime → line chart, categorical → bar chart)
- Number of columns (2 numeric columns → scatter plot)
- This achieved 83.3% accuracy in automated testing

### 6. Voice Pipeline Integration
**Problem:** Whisper (STT) and gTTS (TTS) have different audio format requirements. Whisper needs WAV; gTTS outputs MP3. Browser's `MediaRecorder` produces WebM.

**Solution:** Used `ffmpeg` for server-side audio format conversion (WebM → WAV for Whisper input, and served MP3 output for browser playback).

### 7. Dashboard Persistence
**Problem:** Users pin charts to the dashboard, but the layout (position, size) was lost on page refresh because React Grid Layout stores state in memory.

**Solution:** Persisted dashboard layout in React Context → `localStorage`, with serialization/deserialization of chart configs including the full query result data.

### 8. JWT Token Refresh Race Condition
**Problem:** When multiple API calls fired simultaneously and the access token expired, all of them would try to refresh the token at the same time, causing 401 errors.

**Solution:** Implemented a **request queue** in the Axios interceptor — when a refresh is in progress, subsequent requests are queued and replayed with the new token once the refresh completes.

---

## 7. Future Improvements

### Short-Term (Next Semester)
1. **Column-Level Context Menu** — Right-click on any column in data tables to rename, change type, filter, or sort directly
2. **Dataset Version History** — Track every cleaning transformation with full undo/rollback capability (like Git for data)
3. **Scheduled Reports** — Email automated reports at set intervals using SMTP integration (backend architecture is already designed for this)

### Medium-Term
4. **Multi-User Collaboration** — Shared dashboards where multiple users can view and annotate the same data in real-time
5. **Export Dashboards as Interactive HTML** — Generate standalone HTML files with embedded charts that can be shared without the platform
6. **Support for Additional LLMs** — Plug-and-play support for OpenAI GPT-4, Anthropic Claude, and Meta Llama for code generation (abstract the LLM layer behind an interface)

### Long-Term / Research
7. **Real-Time Streaming Data** — Support WebSocket connections for live data dashboards (stock prices, IoT sensor data)
8. **Fine-Tuned Model** — Train a fine-tuned Gemini/Llama model specifically on Pandas code generation to improve accuracy and reduce hallucination
9. **Natural Language to SQL** — Extend beyond Pandas to generate SQL queries for direct database connections
10. **Mobile App** — React Native companion app for on-the-go data querying
11. **Role-Based Access Control (RBAC)** — Admin, Analyst, Viewer roles with granular dataset and dashboard permissions

---

## 8. Learnings From This Project

### Technical Learnings

**1. LLM Integration is More Than Just API Calls**
- Learned that integrating LLMs into production systems requires extensive **prompt engineering** (our prompt templates are 200+ words with specific formatting rules), **output validation** (AST parsing, regex), and **fallback mechanisms** (stub engine). Simply calling the API is 10% of the work.

**2. Security is a Multi-Layer Problem**
- Learned that no single validation layer is sufficient. Regex catches obvious attacks, but AST analysis catches sophisticated ones like `getattr(getattr(df, '__class__'), '__bases__')`. Each layer compensates for the blind spots of the previous one.

**3. Full-Stack Architecture Decisions Have Cascading Effects**
- Choosing FastAPI over Flask meant we got free Swagger docs, Pydantic validation, and async support — but it also meant learning dependency injection, lifespan events, and a different middleware pattern. Every tech choice has trade-offs.

**4. State Management in React is Critical**
- Without proper state management (AuthContext for JWT, DashboardContext for pinned charts), the app would have become an unmaintainable mess of prop drilling. Context API + custom hooks kept the codebase clean.

**5. Database Schema Design Matters**
- The relationship between `users → datasets → query_logs → saved_queries` had to be designed carefully with proper foreign keys and cascade deletes. A user deleting their account should cascade-delete their datasets, which cascade-delete their query logs.

**6. Pandas is Incredibly Powerful (and Dangerous)**
- Pandas can do anything — which is exactly the problem when LLM-generated code runs unsupervised. Learning to restrict Pandas execution to safe operations was a deep dive into Python's AST module.

### Soft Skills & Process Learnings

**7. Iterative Development Beats Waterfall**
- We started with a simple NL → table output, then iteratively added charts, insights, anomaly detection, forecasting, voice, and dashboards. Each iteration was a working product. This Agile-like approach kept motivation high and bugs manageable.

**8. Testing Saves Time (Not Wastes It)**
- The 67-test accuracy benchmark caught 3 regressions that would have taken hours to debug in production. Investing in automated testing early saved us 10x the time later.

**9. Documentation is a Feature, Not an Afterthought**
- Our detailed README, Swagger API docs, and inline code comments made onboarding new team members and debugging much faster. "If it's not documented, it doesn't exist."

**10. Deployment is Its Own Skill**
- Building the app locally is half the battle. CORS, environment variables, Docker networking, SSL certificates, and serverless database cold starts are entirely different challenges that taught us real-world DevOps skills.

### Key Takeaway
> Building Aether AI taught us that a successful AI application is 20% AI and 80% engineering — the LLM generates code in seconds, but the infrastructure to validate, execute, visualize, and secure that code is where the real complexity lives.

---

## Revision History

| Date | Change | Reason for Changes |
|------|--------|-------------------|
| 12-03-2026 | Initial Draft | First version of SRS for Mid-Term submission |
| 20-03-2026 | Added System Architecture & Tech Stack | Included detailed system architecture diagram, frontend-backend-database flow, and tech stack justification as per mentor feedback |
| 28-03-2026 | Added NL Query Pipeline & Security Module | Documented the Natural Language to Pandas code generation pipeline and the 4-layer AST sandboxing security mechanism |
| 05-04-2026 | Added Data Cleaning & Profiling Features | Included Power BI-style data cleaning module, applied steps log, and dataset profiling documentation |
| 12-04-2026 | Added Advanced Analytics Module | Documented predictive forecasting (Linear Regression + Moving Average), anomaly detection (Z-Score + IQR), and What-If scenario analysis |
| 19-04-2026 | Added Voice Pipeline & Dashboard Builder | Included Speech-to-Text (Whisper) and Text-to-Speech (gTTS) integration, and Power BI-style drag-and-drop dashboard documentation |
| 25-04-2026 | Added Deployment & DevOps Section | Documented Docker containerization, Render.com deployment, Neon PostgreSQL setup, and CORS resolution |
| 30-04-2026 | Added Difficulties & Learnings Sections | Included detailed challenges faced during development (LLM safety, rate limiting, JWT race conditions) and key technical and soft-skill learnings |
| 04-05-2026 | Final Version | Incorporated all mentor remarks — added future improvements, refined feature explanations, updated diagrams, and finalized document for End-Term submission |

**Remark (Mid-Term):** Improvement needed and changes to be done in final version.

---

*Last Updated: May 2026*
