# [OVERVIEW] Generative AI Analysis Platform — Full Project Overview

## What Is This Project?

A **full-stack AI-powered data analysis web application** (Minor Project). It allows non-technical users to upload a CSV or Excel dataset and ask questions in **plain English** (e.g., *"Show average sales by region"*). The app converts the question into Pandas code using an LLM engine, runs it safely, and returns a **chart + textual insights**. It also supports **voice input** via the microphone.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              FRONTEND  (React + Vite)                │
│  Login → Register → Upload → Query → Dashboard      │
└──────────────────────┬───────────────────────────────┘
                       │  REST API  +  JWT Auth
┌──────────────────────▼───────────────────────────────┐
│              BACKEND  (Python + FastAPI)              │
│  Auth → Upload → LLM → Validate → Execute → Chart   │
└──────────────────────┬───────────────────────────────┘
                       │
              SQLite  (database.db)
              datasets/  (uploaded files)
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend Framework | React 18 + Vite |
| Routing | React Router v6 |
| Charts | Recharts |
| Backend Framework | FastAPI (Python) |
| Database | SQLite via SQLAlchemy ORM |
| Authentication | JWT — python-jose + bcrypt |
| Data Processing | Pandas |
| Voice STT | Web Speech API (primary) / SpeechRecognition (fallback) |
| Deployment | Docker Compose |

---

## The Full Query Pipeline (Most Important Flow)

```
User types:  "show average profit by region"
                      ↓
         POST /api/queries/ask
                      ↓
  Step 1 → Load dataset file from memory
  Step 2 → LLM Engine generates Pandas code:
            df.groupby('Region')['Profit'].mean().reset_index()
  Step 3 → Validator: syntax check + blocked pattern scan (no exec/drop/import etc.)
  Step 4 → Executor: run code in a SANDBOXED namespace on a DataFrame COPY
  Step 5 → Viz Selector: pick chart type (bar / line / pie / table)
  Step 6 → Insight Generator: auto-generate max/min/trend text
  Step 7 → Log query to SQLite DB
                      ↓
      Return: chart data + insights + code to frontend
```

---

## Project File Structure

```
minor new project/
├── .env                        ← Secrets & config (JWT key, model path, etc.)
├── docker-compose.yml          ← Runs backend + frontend as Docker services
├── README.md                   ← (Original readme)
├── datasets/                   ← Uploaded CSV/Excel files stored here
├── logs/                       ← Application logs
│
├── backend/                    ← Python FastAPI server
│   ├── main.py
│   ├── requirements.txt
│   ├── database.db
│   ├── core/
│   │   └── config.py
│   ├── database/
│   │   ├── models.py
│   │   └── session.py
│   ├── auth/
│   │   ├── jwt_handler.py
│   │   └── router.py
│   ├── api/
│   │   ├── datasets.py
│   │   ├── queries.py
│   │   └── voice.py
│   ├── llm/
│   │   ├── llm_engine.py
│   │   └── prompt_templates.py
│   ├── services/
│   │   ├── data_validator.py
│   │   ├── schema_extractor.py
│   │   ├── query_validator.py
│   │   ├── query_executor.py
│   │   ├── viz_selector.py
│   │   ├── insight_generator.py
│   │   └── query_logger.py
│   ├── voice/
│   │   ├── stt.py
│   │   └── tts.py
│   └── utils/
│       └── helpers.py
│
└── frontend/                   ← React + Vite client
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/
        │   ├── axiosClient.js
        │   ├── auth.js
        │   ├── datasets.js
        │   ├── queries.js
        │   └── voice.js
        ├── context/
        │   ├── AuthContext.jsx
        │   └── DashboardContext.jsx
        ├── hooks/
        │   ├── useAuth.js
        │   └── useDashboard.js
        ├── components/
        │   ├── ChartRenderer.jsx
        │   ├── InsightDisplay.jsx
        │   ├── Navbar.jsx
        │   ├── ProtectedRoute.jsx
        │   └── VoiceRecorder.jsx
        ├── pages/
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   ├── Upload.jsx
        │   ├── Query.jsx
        │   ├── Dashboard.jsx
        │   └── History.jsx
        ├── styles/
        │   ├── global.css
        │   └── variables.css
        └── utils/
            └── helpers.js
```

---

## [BACKEND] Backend — File-by-File Explanation

### `main.py` — App Entry Point
- Creates the **FastAPI** application instance
- Adds **CORS middleware** so the React frontend (port 5173) can communicate with the backend (port 8000)
- Registers all 4 API routers: `auth`, `datasets`, `queries`, `voice`
- On startup, calls `Base.metadata.create_all()` to auto-create SQLite tables
- Exposes `GET /` as a health-check endpoint

---

### `requirements.txt` — Python Dependencies
| Package | Purpose |
|---|---|
| `fastapi`, `uvicorn` | Web server |
| `sqlalchemy`, `aiosqlite` | Database ORM |
| `python-jose`, `bcrypt`, `passlib` | JWT auth + password hashing |
| `pandas`, `openpyxl` | Data processing |
| `python-multipart` | File upload support |
| `pydantic-settings` | Config from `.env` |
| `transformers`, `torch` *(commented)* | Real LLM model (not loaded yet) |
| `openai-whisper`, `pyttsx3` *(commented)* | Real voice features (not loaded yet) |

---

### `core/config.py` — Central Configuration
Uses `pydantic-settings` (`BaseSettings`) to read all values from `.env`.
Exports a singleton `settings` object used across the entire backend.

| Setting | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | "change-me-in-production" | JWT signing key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Token lifetime |
| `DATABASE_URL` | sqlite:///./database.db | DB connection |
| `LLM_MODEL_PATH` | microsoft/Phi-3-mini-4k-instruct | AI model to load |
| `WHISPER_MODEL` | base | Whisper STT model |
| `UPLOAD_DIR` | ../datasets | Where files are saved |
| `MAX_FILE_SIZE_MB` | 50 | Upload size limit |
| `FRONTEND_URL` | http://localhost:5173 | CORS allowed origin |

---

### `database/models.py` — ORM Tables
Defines 2 SQLAlchemy database tables:

**`User`**
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment ID |
| `username` | String(50) unique | Login name |
| `email` | String(100) unique | Email address |
| `hashed_password` | String(255) | bcrypt hash |
| `created_at` | DateTime | Registration time |

**`QueryLog`**
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment ID |
| `user_id` | FK → users.id | Who ran the query |
| `natural_query` | Text | Original NL question |
| `generated_code` | Text | Pandas code from LLM |
| `is_valid` | Integer | 1 = passed, 0 = failed |
| `result_summary` | Text | JSON string of result |
| `created_at` | DateTime | When it ran |

---

### `database/session.py` — DB Connection & Session
- Creates the SQLAlchemy `engine` connecting to SQLite
- Creates `SessionLocal` (session factory)
- Defines `Base` — all models inherit from this
- Provides `get_db()` — a FastAPI dependency that opens a DB session per request and closes it when done

---

### `auth/jwt_handler.py` — JWT Token Utilities
| Function | What it does |
|---|---|
| `create_access_token(data)` | Signs a JWT with an expiry time |
| `get_current_user(token, db)` | FastAPI dependency — decodes JWT from `Authorization: Bearer` header, looks up user in DB, returns `User` object. Raises `401` if invalid. |

---

### `auth/router.py` — Auth API Endpoints
Mounted at `/api/auth/`

| Endpoint | Method | What it does |
|---|---|---|
| `/register` | POST | Creates a new user with bcrypt-hashed password, returns JWT |
| `/login` | POST | Verifies credentials, returns JWT |
| `/me` | GET | Returns current user's profile (requires JWT) |

---

### `api/datasets.py` — Dataset Endpoints
Mounted at `/api/datasets/`

| Endpoint | Method | What it does |
|---|---|---|
| `/upload` | POST | Accepts CSV/Excel; validates format; saves file to disk; creates data profile + schema; stores in in-memory `_datasets` dict; returns `dataset_id` |
| `/{id}/schema` | GET | Returns column schema for a dataset |
| `/{id}/profile` | GET | Returns data profile (rows, nulls, duplicates, stats) |

> [IMPORTANT] **Important:** Datasets are stored in a Python dict in memory. The `dataset_id` resets to 1 every time the server restarts.

---

### `api/queries.py` — Query Pipeline Endpoints
Mounted at `/api/queries/`  — **The most important file in the backend.**

| Endpoint | Method | What it does |
|---|---|---|
| `/ask` | POST | Runs the full NL → code → execute → visualize → insights pipeline |
| `/history` | GET | Returns the user's past 50 queries from DB |

The `/ask` request body:
```json
{
  "dataset_id": "1",
  "query": "show average profit by region",
  "graph_type": "auto"
}
```

Each step in the pipeline is completely independent — no global state or caching between requests.

---

### `api/voice.py` — Voice Endpoints
Mounted at `/api/voice/`

| Endpoint | Method | What it does |
|---|---|---|
| `/transcribe` | POST | Receives audio file → saves to temp file → calls `stt.transcribe_audio()` → returns transcript text |
| `/synthesize` | POST | Receives text → calls `tts.synthesize_speech()` → returns audio path (currently a stub) |

---

### `llm/llm_engine.py` — AI Code Generator
This is the **brain** of the platform. In production it loads **Microsoft Phi-3 Mini** (transformer model) to convert natural language to Pandas code.

**Current state:** Uses **keyword matching + schema-aware column extraction** as a stub.

How the stub works:
1. Extracts column names (numeric, categorical, datetime) from the schema summary string
2. Detects keywords in the query: `average`, `sum`, `count`, `max`, `min`, `trend`, `correlation`, `distribution`, `compare`, `missing`, `unique`, etc.
3. Checks if any column name is mentioned in the query
4. Generates the appropriate Pandas expression

Example outputs by keyword:
| Query keyword | Generated Pandas code |
|---|---|
| "average … by region" | `df.groupby('region')['sales'].mean().reset_index()` |
| "total sum" | `df['sales'].sum()` |
| "count by category" | `df['category'].value_counts().reset_index()` |
| "top 10" | `df.nlargest(10, 'sales')` |
| "correlation" | `df.corr(numeric_only=True)` |
| "missing values" | `df.isnull().sum().reset_index()` |
| "show all" | `df.head(50)` |

The real transformer model loading is commented out in `__init__` — just needs to be uncommented and the model path configured.

---

### `llm/prompt_templates.py` — LLM Prompt Templates
Two prompt-building functions ready for when the real model is connected:
- `build_analysis_prompt(query, schema_summary)` — instructs the LLM to generate a single, safe, read-only Pandas expression
- `build_explanation_prompt(code, result_summary)` — instructs the LLM to explain the result in plain English (2–3 sentences)

---

### `services/data_validator.py` — Dataset Validation
Called immediately when a file is uploaded.

| Function | What it does |
|---|---|
| `validate_file_format(filename)` | Checks extension is `.csv`, `.xlsx`, or `.xls` |
| `load_dataframe(filepath)` | Reads file into a Pandas DataFrame |
| `detect_missing_values(df)` | Returns `{column: null_count}` dict |
| `detect_duplicates(df)` | Returns count of duplicate rows |
| `detect_invalid_types(df)` | Flags columns that look numeric but have string errors |
| `create_data_profile(df)` | Combines all checks into one profile dict (rows, columns, missing, duplicates, numeric stats) |

---

### `services/schema_extractor.py` — Schema Analysis
Called on upload to understand the dataset's structure.

| Function | What it does |
|---|---|
| `classify_column_type(series)` | Classifies a column as `numeric`, `categorical`, `datetime`, or `boolean` |
| `extract_column_metadata(df)` | For every column: name, dtype, semantic type, null count, unique count, 5 sample values |
| `extract_schema(df)` | Returns the full schema dict |
| `generate_schema_summary(schema)` | Converts schema to a human-readable string injected into the LLM prompt |

Example schema summary output:
```
Dataset has 1000 rows and 5 columns.
Columns:
  - Region (categorical): 0 nulls, 12 unique values. Sample: ['East', 'West', 'North']
  - Sales (numeric): 0 nulls, 987 unique values. Sample: [5400, 3200, 7800]
```

---

### `services/query_validator.py` — Code Safety Validator [SECURITY]
Runs on EVERY LLM-generated code string **before** execution. This is a critical security layer.

**3 checks:**

1. **Syntax validation** — `ast.parse()` — ensures valid Python syntax
2. **Blocked pattern scan** — regex search for dangerous patterns:
   - `import`, `exec`, `eval`, `compile`, `globals`, `locals`
   - `os.`, `sys.`, `subprocess`, `shutil`, `open`
   - `drop`, `to_csv`, `to_excel`, `to_sql`, `del`
   - `DELETE`, `UPDATE`, `DROP`, `INSERT`, `ALTER`
3. **Schema consistency** — checks that string literals in the code match known column names (warns only, doesn't block)

Has an `ALLOWED_OPERATIONS` whitelist of safe Pandas methods (`groupby`, `mean`, `describe`, `value_counts`, `nlargest`, etc.)

---

### `services/query_executor.py` — Safe Code Runner [SECURITY]
Executes the validated Pandas code string.

**Safety measures:**
- Makes a **copy** of the DataFrame — the original is NEVER mutated
- **Restricted namespace** — only `df` (the copy) and `pd` are available. No builtins, no file I/O, no imports possible.
- Wraps code as `__result__ = <code>` and uses `exec()`
- Normalizes result types: DataFrame → list of dicts; Series → reset_index; Scalar → `{"value": x}`
- Caps DataFrame output at **500 rows**

---

### `services/viz_selector.py` — Automatic Chart Type Selection
After execution, this analyses the result shape and picks the best chart.

| Result shape | Chart type |
|---|---|
| Datetime column + Numeric column | Line chart |
| Categorical + Numeric (≤6 unique categories) | Pie chart |
| Categorical + Numeric (>6 categories) | Bar chart |
| Two numeric columns | Bar chart |
| Single value/distribution | Pie (≤10 rows) or Bar |
| Complex / large table | Data Table |

Supports **manual override** — if the user selected a specific graph type (e.g., "pie"), it always uses that.

---

### `services/insight_generator.py` — Automatic Text Insights
Generates short human-readable summaries from query results:
- For each **numeric column**: max value, min value, average value
- **Trend detection**: compares first-third vs last-third of values to flag "upward/downward trend"
- For each **categorical column**: most frequent value + count
- Returns `{summary, highlights[], row_count}`

---

### `services/query_logger.py` — Database Logger
| Function | What it does |
|---|---|
| `log_query(db, user_id, query, code, is_valid, summary)` | Saves a `QueryLog` entry to SQLite |
| `get_user_history(db, user_id, limit=50)` | Retrieves the last 50 queries for a user, newest first |

---

### `voice/stt.py` — Speech-to-Text
`transcribe_audio(filepath)`:
1. Checks if `speech_recognition` library is installed
2. For **.wav** files → reads directly
3. For **WebM/MP3/OGG** → converts to WAV first using `pydub`
4. Sends to **Google's free speech recognition API** (no API key needed)
5. Returns `{transcript, confidence, language}`

---

### `voice/tts.py` — Text-to-Speech (Stub)
`synthesize_speech(text)` — returns a mock response. Production implementation uses `pyttsx3` or `gTTS` to generate an actual `.wav` file.

---

### `utils/helpers.py` — Shared Utilities
| Function | What it does |
|---|---|
| `ensure_directory(path)` | Creates a directory if it doesn't exist |
| `generate_filename(original, prefix)` | Creates a unique timestamped filename e.g. `user1_20240314_120000_data.csv` |
| `truncate_text(text, max_length)` | Shortens text with `...` |

---

## [FRONTEND] Frontend — File-by-File Explanation

### `main.jsx` — React Entry Point
Mounts the React app into the `#root` div in `index.html`.

---

### `App.jsx` — Root Component & Router
- Wraps the entire app in `<AuthProvider>` and `<DashboardProvider>`
- Sets up React Router with routes:

| Path | Component | Access |
|---|---|---|
| `/login` | Login | Public |
| `/register` | Register | Public |
| `/dashboard` | Dashboard | 🔐 Protected |
| `/upload` | Upload | 🔐 Protected |
| `/query` | Query | 🔐 Protected |
| `/history` | History | 🔐 Protected |
| `/*` | → redirect to `/dashboard` | — |

---

### `pages/Login.jsx` — Login Page
Username + password form. Calls `login()` from `AuthContext`. Redirects to `/dashboard` on success.

---

### `pages/Register.jsx` — Register Page
Username + email + password form. Calls `register()` from `AuthContext`. Redirects to `/dashboard` on success.

---

### `pages/Upload.jsx` — Dataset Upload Page
- **Drag-and-drop zone** (or click-to-browse) for CSV/Excel files
- On upload → calls `POST /api/datasets/upload`
- Displays the **Dataset ID** (user must copy this to use in the Query page)
- Shows a **Data Profile** card: rows, columns, duplicates, missing values per column (highlighted in orange if > 0)
- Shows a **Schema** card: all column names, types, unique count

---

### `pages/Query.jsx` — Query Page [MAIN FEATURE]
Inputs:
- **Dataset ID** text field
- **Natural language query** text field
- **Chart Type** dropdown: Auto / Bar / Line / Pie / Table
- **[Mic Icon] Voice button** (via `VoiceRecorder`)

On submit → calls `POST /api/queries/ask`, then displays:
- Generated Pandas code + explanation
- **Chart** (`ChartRenderer`)
- **Insights** (`InsightDisplay`)
- **"Add to Dashboard"** button → pins result to Dashboard

Uses a `queryKey` counter that increments on every query to force `ChartRenderer` to fully remount (prevents stale chart bugs). This page is also optimized with a rendering fix to prevent the "blank on load" Chromium bug.

---

### `pages/Dashboard.jsx` — Analytics Dashboard
- **4 KPI cards**: total pinned charts, chart types count, avg data rows, most-used chart type
- **Quick action cards**: links to Upload, Query, History
- **Filter bar**: filter pinned charts by type (All / Bar / Line / Pie / Table)
- **2-column chart grid**: each panel shows query title, chart, insights, and a ✕ remove button
- **"Clear All"** button to wipe the entire dashboard

---

### `pages/History.jsx` — Query History
- On load → fetches `GET /api/queries/history`
- Shows each past query: the natural language question, the Pandas code generated, a [Valid] / [Invalid] badge, and the timestamp

---

### `components/ChartRenderer.jsx` — Chart Renderer
Receives `data` and `visualization` props and renders one of:
| `chart_type` | What renders |
|---|---|
| `bar` | `<BarChart>` via Recharts |
| `line` | `<LineChart>` via Recharts |
| `pie` | `<PieChart>` via Recharts |
| `table` | HTML `<table>` (up to 100 rows) |

Dark-themed with purple color palette (`#6c63ff`). Uses `useMemo` to avoid re-renders.

---

### `components/VoiceRecorder.jsx` — Voice Input
Two-layer approach:
1. **Primary: Web Speech API** — browser-native, instant, no server round-trip, shows live interim transcript
2. **Fallback: MediaRecorder + Backend** — records WebM audio blob → sends to `POST /api/voice/transcribe` → gets text back

UI: [Mic Icon] button → tap to start → shows [Recording Icon] Listening... → stops → fills the query field.

- **Dual-Layer Logic:**
    1. **Primary:** Uses the browser's native **Web Speech API** for instant, client-side transcription.
    2. **Fallback:** If the browser doesn't support the native API, it uses **MediaRecorder** to capture a WebM blob, sends it to the `/transcribe` backend endpoint, and retrieves the text.
- **Rendering Optimization:** The voice recording visual state is now correctly promote for hardware acceleration to ensure it appears instantly without needing a scroll.

---

### `components/InsightDisplay.jsx` — Insight Text
Renders the `insights` object: the summary paragraph + a bulleted list of highlights (e.g., *"'Profit': max = 50000, min = 200, average = 12345"* and *"'Profit' shows an upward trend"*).

---

### `components/Navbar.jsx` — Navigation Bar
Top navigation bar with links to Dashboard, Upload, Query, History. Shows logged-in username and a Logout button. Hidden on login/register pages.

---

### `components/ProtectedRoute.jsx` — Route Guard
Checks `AuthContext` for a valid token. If not logged in → redirects to `/login`. Wraps all 4 protected pages.

---

### `context/AuthContext.jsx` — Authentication State (Global)
React Context that manages:
- `user` — the logged-in user object (`{id, username, email}`)
- `token` — the JWT stored in **`localStorage`** (survives page refresh)
- `login(username, password)` — calls API, stores token, sets user
- `register(username, email, password)` — same flow
- `logout()` — clears token and user

On app load → verifies any existing localStorage token by calling `GET /api/auth/me`. If expired → auto-clears.

---

### `context/DashboardContext.jsx` — Dashboard State (Global)
React Context that manages the list of pinned chart panels:
- State stored in **`sessionStorage`** (survives page refresh; cleared when tab closes)
- `addPanel(panel)` — prepends a new chart panel
- `removePanel(id)` — removes by ID
- `clearPanels()` — wipes all panels

---

### `api/axiosClient.js` — Axios HTTP Client
Creates a singleton Axios instance pointing to the backend URL. Automatically attaches `Authorization: Bearer <token>` to every request by reading from `localStorage`.

### `api/auth.js` — Auth API Functions
`loginUser`, `registerUser`, `getMe` — call `/api/auth/*` endpoints.

### `api/datasets.js` — Dataset API Functions
`uploadDataset(file)` — sends a `multipart/form-data` POST to `/api/datasets/upload`.

### `api/queries.js` — Query API Functions
`askQuery(datasetId, query, graphType)` — calls `POST /api/queries/ask`.
`getQueryHistory()` — calls `GET /api/queries/history`.

### `api/voice.js` — Voice API Functions
`transcribeAudio(audioBlob)` — sends audio blob to `POST /api/voice/transcribe`.

---

### `hooks/useAuth.js`
`useContext(AuthContext)` — a convenience hook used in all components that need auth state.

### `hooks/useDashboard.js`
`useContext(DashboardContext)` — used in `Query.jsx` (`addPanel`) and `Dashboard.jsx` (`panels`, `removePanel`, `clearPanels`).

---

### `styles/variables.css` — Design Tokens
CSS custom properties defining the design system:
- Colors: `--color-bg` (dark), `--color-surface`, `--color-accent` (#6c63ff purple), error (red), success (green), warning (orange)
- Spacing: `--space-sm` (0.5rem) to `--space-xl` (3rem)
- Border radius, box shadows, font size scales

### `styles/global.css` — Global Styles
All component styles (≈500 lines): cards, buttons, inputs, alerts, navbar, etc.
- **Note:** Includes a fix for a Chromium GPU compositing bug where `backdrop-filter` on a sticky navbar caused content to appear blank until scrolled. Resolved using `will-change: transform` and `isolation: isolate`.

---

### `utils/helpers.js`
`formatDate(dateString)` — formats ISO timestamps (e.g., `"2024-03-14T18:30:00"`) into a human-readable local date/time string for the History page.

---

## Infrastructure

### `.env` — Environment Variables
```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./database.db
LLM_MODEL_PATH=microsoft/Phi-3-mini-4k-instruct
LLM_DEVICE=cpu
WHISPER_MODEL=base
FRONTEND_URL=http://localhost:5173
UPLOAD_DIR=../datasets
MAX_FILE_SIZE_MB=50
```

### `docker-compose.yml` — Container Orchestration
| Service | Port | Description |
|---|---|---|
| `backend` | 8000 | FastAPI server with datasets volume |
| `frontend` | 5173 | React/Vite server depending on backend |

---

## Current Stub Areas vs Production Plans

| Feature | Current State | Production Implementation |
|---|---|---|
| LLM Code Generation | Keyword matching stub | Load Phi-3 Mini via Hugging Face `transformers` |
| Text-to-Speech | Mock stub | Use `pyttsx3` or `gTTS` to generate `.wav` |
| Dataset Persistence | In-memory Python dict (resets on restart) | Store in database table |
| Anomaly Detection | Not implemented | Statistical outlier detection (IQR / Z-score) |
| Automated Report Export | Not implemented | PDF/XLSX export endpoint |
| Conversational Memory | Not implemented | Store conversation history per user session |

---

## How to Run

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up --build
```

Frontend: http://localhost:5173  
Backend API: http://localhost:8000  
API Docs: http://localhost:8000/docs

---

*Generated: March 2026*

---

## [TOOLS] Technical Fixes & Optimizations

### 1. Chromium Rendering Bug (Blank Screen on Load)
- **Issue:** The Query page and voice input sometimes appeared blank or white initially, with content only appearing after a scroll.
- **Cause:** `backdrop-filter: blur()` on the `position: sticky` navbar caused a GPU layer compositing error in Chromium-based browsers.
- **Fix:** Removed `backdrop-filter` from the navbar and added `will-change: transform` + `isolation: isolate` to force correct layer promotion and paint order.
