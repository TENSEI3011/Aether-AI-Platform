# 🔍 Complete Project Working — Page-by-Page Deep Dive

## What This Project IS (One-Liner)

> A platform where a non-technical person uploads a CSV/Excel file, asks questions in plain English (or voice), and the AI automatically writes Python code, runs it safely, picks the best chart, generates insights, detects anomalies, and narrates the result.

---

## THE BIG PICTURE — How Everything Connects

```
USER (Browser)
  │
  ├── 1. Register/Login ──→ auth/router.py ──→ users table ──→ JWT tokens returned
  │
  ├── 2. Upload CSV ──→ api/datasets.py ──→ saves file to datasets/ folder
  │                                       ──→ extracts schema (schema_extractor.py)
  │                                       ──→ creates profile (data_validator.py)
  │                                       ──→ stores metadata in dataset_records table
  │                                       ──→ keeps DataFrame in memory (_datasets dict)
  │
  ├── 3. Ask Question ──→ api/queries.py ──→ PIPELINE:
  │       "avg sales         │
  │        by city"          ├─→ Step 1: Load dataset from memory
  │                          ├─→ Step 2: Send to LLM (llm_engine.py → Gemini API)
  │                          │           LLM returns: df.groupby('city')['sales'].mean()
  │                          ├─→ Step 3: Validate code (query_validator.py)
  │                          │           Regex scan + AST check → safe? proceed
  │                          ├─→ Step 4: Execute code (query_executor.py)
  │                          │           Runs on df.copy() in sandboxed namespace
  │                          ├─→ Step 5: Pick chart (viz_selector.py)
  │                          │           Category + Numeric → Bar chart
  │                          ├─→ Step 6: Generate insights (insight_generator.py)
  │                          │           "📈 Highest: Mumbai at 75,000"
  │                          ├─→ Step 7: Detect anomalies (anomaly_detector.py)
  │                          │           Z-score + IQR → flag outliers
  │                          ├─→ Step 8: AI narration (llm_engine.py)
  │                          │           "Mumbai leads with 75K in sales..."
  │                          ├─→ Step 9: Suggest follow-ups (llm_engine.py)
  │                          │           "What about profit by city?"
  │                          ├─→ Step 10: Log query (query_logger.py → query_logs table)
  │                          └─→ Step 11: Save context (context_manager.py)
  │
  │                          ──→ Returns JSON with: data, chart config, insights,
  │                              anomalies, narration, suggestions
  │
  │                          ──→ React renders: ChartRenderer + InsightDisplay
  │
  ├── 4. Voice Input ──→ api/voice.py ──→ voice/stt.py (audio → text)
  │                                    ──→ text becomes the query (goes to pipeline above)
  │
  ├── 5. Voice Output ──→ api/voice.py ──→ voice/tts.py (narration text → MP3 audio)
  │                                     ──→ base64 MP3 sent to browser → plays
  │
  └── 6. All other pages use subsets of this same pipeline
```

---

## PAGE-BY-PAGE DETAILED EXPLANATION

---

### 📄 Page 1: Register (`/register`)

**What the user sees:** A form with username, email, password fields.

**What happens behind the scenes:**

1. User fills form → clicks Register
2. Frontend (`Login.jsx` / `Register.jsx`) calls `POST /api/auth/register`
3. Backend (`auth/router.py`) receives the request
4. **Pydantic validation** runs automatically:
   - Username: must be 3-30 chars, only letters/numbers/underscores (regex: `^[a-zA-Z0-9_]{3,30}$`)
   - Email: must match email pattern
   - Password: must be ≥ 6 characters
5. Checks if username already exists in `users` table → if yes, returns 400 error
6. Checks if email already exists → if yes, returns 400 error
7. **Hashes the password** using bcrypt: `bcrypt.hashpw(password, bcrypt.gensalt())`
   - This adds a random salt + runs 12 rounds of hashing
   - Even if the database is leaked, passwords can't be reversed
8. Creates a `User` row in the database
9. Generates **two JWT tokens**:
   - Access token (2 hours): `jwt.encode({sub: username, exp: ..., type: "access"}, SECRET_KEY, HS256)`
   - Refresh token (7 days): same but `type: "refresh"` and longer expiry
10. Returns both tokens → frontend stores in localStorage
11. User is redirected to `/dashboard`

**Files involved:** `Register.jsx` → `api/auth.js` → `auth/router.py` → `auth/jwt_handler.py` → `database/models.py` (User table)

---

### 📄 Page 2: Login (`/login`)

**What the user sees:** Username + password form.

**What happens:**

1. User enters credentials → clicks Login
2. Frontend calls `POST /api/auth/login`
3. Backend finds user by username in DB
4. **bcrypt.checkpw()** compares entered password with stored hash
5. If match → generates JWT pair → returns tokens
6. If no match → returns 401 "Invalid username or password"
7. Frontend stores tokens in localStorage
8. **Every future API call** now includes: `Authorization: Bearer <access_token>` in the header
9. When access token expires (2 hours), the Axios interceptor in `axiosClient.js` catches the 401 error, sends the refresh token to `/api/auth/refresh`, gets new tokens, and retries — the user never notices

**Files involved:** `Login.jsx` → `api/auth.js` → `api/axiosClient.js` (interceptors) → `auth/router.py` → `auth/jwt_handler.py`

---

### 📄 Page 3: Upload (`/upload`)

**What the user sees:** A drag-and-drop area or file picker. After upload: row count, column count, data preview, schema info.

**What happens:**

1. User selects a CSV or Excel file
2. Frontend sends the file as `multipart/form-data` to `POST /api/datasets/upload`
3. Backend (`api/datasets.py`):
   - **Validates format**: only `.csv`, `.xlsx`, `.xls` allowed
   - **Checks file size**: must be ≤ 50MB
   - **Saves to disk**: `datasets/user{id}_{uuid}_{filename}`
   - **Loads into Pandas**: `pd.read_csv()` or `pd.read_excel()`
   - **Schema extraction** (`schema_extractor.py`):
     - Loops through every column
     - Classifies each as: `numeric`, `categorical`, `datetime`, or `boolean`
     - Records: column name, dtype, null count, unique count, sample values
     - Builds a text summary like: `"- city (categorical): 0 nulls, 5 unique values. Sample: ['Delhi', 'Mumbai', 'Bangalore']"`
   - **Data profile** (`data_validator.py`):
     - Row count, column count
     - Null percentage per column
     - Basic stats (mean, min, max)
   - **Thread-safe ID generation**: uses `threading.Lock()` so two simultaneous uploads don't get the same ID
   - **Stores in memory**: `_datasets[dataset_id] = {filepath, schema, schema_summary, profile, user_id}`
   - **Persists to DB**: saves a `DatasetRecord` row with metadata
4. Returns: dataset_id, filename, row_count, column_count, profile, schema
5. The schema summary will later be injected into the LLM prompt so the AI knows what columns exist

**Why in-memory AND database?**
- In-memory: fast access during queries (no disk I/O)
- Database: survives server restarts (on startup, `restore_datasets_from_db()` reloads everything)

**Files involved:** `Upload.jsx` → `api/datasets.js` → `api/datasets.py` → `services/schema_extractor.py` → `services/data_validator.py` → `database/models.py` (DatasetRecord)

---

### 📄 Page 4: Query (`/query`) — ⭐ THE CORE PAGE

**What the user sees:** Dataset selector, text input box, voice recorder button, graph type dropdown, submit button. After query: chart, data table, generated code, insights, anomalies, narration, follow-up suggestions.

**What happens — the 11-step pipeline:**

#### Step 1: Load Dataset
- Reads `dataset_id` from request
- Checks ownership: does this dataset belong to this user? If not → 403
- Loads the CSV/Excel file into a Pandas DataFrame
- Gets the schema summary (already generated at upload time)

#### Step 2: LLM Code Generation (`llm/llm_engine.py`)
- Builds a **prompt** using `prompt_templates.py`:
  ```
  You are a data analysis assistant. You ONLY generate valid Python Pandas code.
  RULES: [7 rules about safety]
  DATASET SCHEMA: [column names, types, samples]
  USER QUESTION: "average sales by city"
  Return ONLY the Pandas expression inside a ```python code block.
  ```
- Sends to Google Gemini API: `client.models.generate_content(model="gemini-2.0-flash", contents=prompt)`
- Gemini responds with something like:
  ```python
  df.groupby('city')['sales'].mean().reset_index().sort_values('sales', ascending=False)
  ```
- The engine **extracts code** from the markdown code block using regex
- If Gemini fails (quota, network error) → **stub engine** activates:
  - Parses keywords: "average" → `.mean()`, "by city" → `.groupby('city')`
  - Uses schema to find the correct column names
  - Generates valid Pandas code without any AI

#### Step 3: Validation (`services/query_validator.py`)
- **Syntax check**: `ast.parse(code)` — is it valid Python?
- **Blocked patterns**: 20+ regex patterns scan for: `import`, `exec`, `eval`, `os.`, `sys.`, `.drop()`, `to_csv`, `DELETE`, etc.
- **Schema check**: verifies string literals in code match actual column names

#### Step 4: AST Safety + Execution (`services/query_executor.py`)
- **AST walker**: parses code into a tree, visits every node, blocks:
  - `__class__`, `__mro__`, `__subclasses__` (sandbox escape attacks)
  - `import` statements
  - `exec()`, `eval()`, `open()`, `getattr()` calls
- **Creates a copy**: `df_copy = df.copy()` — original data is NEVER touched
- **Restricted exec**:
  ```python
  exec(code, {"__builtins__": {}}, {"df": df_copy, "pd": pd})
  ```
  - No built-in functions available (no `print`, `open`, `import`)
  - Only `df` (copy) and `pd` (pandas) accessible
- **Timeout**: runs in a thread with 10-second limit
- **Formats result**: DataFrame → list of dicts, Series → reset_index, scalar → `{value: X}`

#### Step 5: Visualization Selection (`services/viz_selector.py`)
- Analyses the result's column types and shape:
  - Has datetime + numeric? → **Line chart**
  - Has category + numeric with ≤6 categories? → **Pie chart**
  - Has category + numeric with >6 categories? → **Bar chart**
  - Has 2 numeric columns, many rows? → **Scatter plot**
  - Square numeric matrix? → **Heatmap** (for correlation results)
  - Single numeric column? → **Histogram**
  - Everything else → **Data table**
- User can override by selecting a chart type manually

#### Step 6: Insight Generation (`services/insight_generator.py`)
- Finds the highest and lowest values and their labels
- Calculates ratios: "3.2× higher than the lowest"
- Counts how many items are above average
- Lists top 3 entries
- Detects trends (first half vs second half of data)
- For correlation results: interprets as "strong positive" / "weak negative" etc.
- Output: `{ summary, highlights: ["📈 Highest SALES: Mumbai at 75,000 — 2.1× higher than Kolkata"] }`

#### Step 7: Anomaly Detection (`services/anomaly_detector.py`)
- **Z-score**: flags values where |z| > 3 (3 standard deviations from mean)
- **IQR**: flags values outside Q1-1.5×IQR to Q3+1.5×IQR
- Returns: list of flagged data points with messages

#### Step 8: AI Narration
- Sends query + result summary + highlights to Gemini
- Gemini writes a 2-3 sentence narrative like: *"Mumbai leads in sales at 75,000, which is 2.1 times higher than Kolkata. The average across all cities is 53,000, with 2 out of 5 cities exceeding this."*
- This text can be played as audio via TTS

#### Step 9: Follow-up Suggestions
- Gemini suggests 3 smart next questions based on the current query and result
- Displayed as clickable buttons

#### Step 10: Query Logging
- Saves to `query_logs` table: user_id, natural_query, generated_code, is_valid, result_summary, timestamp

#### Step 11: Context Storage
- Saves (query, code, explanation) to both in-memory cache and `conversation_ctx` DB table
- Next query with same session_id gets this history injected into the LLM prompt
- Enables: "now filter only for Mumbai" to work as a follow-up

**Files involved:** `Query.jsx` → `api/queries.js` → `api/queries.py` → `llm/llm_engine.py` → `llm/prompt_templates.py` → `services/query_validator.py` → `services/query_executor.py` → `services/viz_selector.py` → `services/insight_generator.py` → `services/anomaly_detector.py` → `services/query_logger.py` → `services/context_manager.py`

**Frontend rendering:** `ChartRenderer.jsx` (renders the chart) + `InsightDisplay.jsx` (renders highlights)

---

### 📄 Page 5: Data Cleaning (inside Query page)

**What the user sees:** A "Clean Data" option where they type instructions like "remove duplicate rows" or "fill missing values with 0".

**What happens:**

1. User types: "remove duplicate rows"
2. Backend sends this as a cleaning instruction to the LLM
3. LLM generates: `df.drop_duplicates()`
4. Code is validated → executed on a copy
5. If `persist=True`: the cleaned DataFrame is written back to the original file on disk
6. Schema and profile are recalculated for the cleaned data
7. Returns: before/after row counts, rows removed, preview of cleaned data

**Files involved:** `api/queries.py` (the `/clean` endpoint) → same LLM + validator + executor pipeline

---

### 📄 Page 6: History (`/history`)

**What the user sees:** A table/list of all past queries with: question asked, generated code, success/failure, timestamp.

**What happens:**

1. Frontend calls `GET /api/queries/history`
2. Backend queries `query_logs` table filtered by `user_id` (from JWT)
3. Returns list of entries ordered by timestamp
4. User can click to re-run any past query

**Files involved:** `History.jsx` → `api/queries.js` → `api/queries.py` → `services/query_logger.py` → `database/models.py` (QueryLog)

---

### 📄 Page 7: Data Profile (`/profile`)

**What the user sees:** Rich statistical dashboard for a dataset — per-column stats, correlation heatmap, distributions.

**What happens:**

1. User selects a dataset
2. Frontend calls `GET /api/datasets/{id}/full-profile`
3. Backend (`services/data_profiler.py`) generates:
   - **Per-column stats**: mean, median, std, min, max, Q1, Q3, null count, unique count
   - **Correlation matrix**: `df.corr(numeric_only=True)` — shows how columns relate
   - **Top values**: `value_counts()` for categorical columns
   - **Distribution data**: for histograms
4. Returns JSON → frontend renders stats cards + heatmap + histograms

**Files involved:** `DataProfile.jsx` → `api/datasets.js` → `api/datasets.py` → `services/data_profiler.py`

---

### 📄 Page 8: Multi-Query / JOIN (`/multi-query`)

**What the user sees:** Two dataset selectors, join column picker, join type dropdown, query input.

**What happens:**

1. User selects Dataset A (e.g., products.csv) and Dataset B (e.g., sales.csv)
2. Selects the common column (e.g., `product_id`) and join type (inner/left/right/outer)
3. Types a query: "total revenue by category"
4. Backend (`api/multi_query.py`):
   - Loads both DataFrames
   - Merges them: `pd.merge(df_a, df_b, on='product_id', how='inner')`
   - Combines schemas from both datasets
   - Sends the merged schema + query through the **same LLM pipeline**
   - Returns result with chart + insights

**Files involved:** `MultiQuery.jsx` → `api/multiQuery.js` → `api/multi_query.py` → same pipeline services

---

### 📄 Page 9: Forecast (`/forecast`)

**What the user sees:** Dataset selector, x-column (time) and y-column (metric) pickers, periods slider, method selector (linear/moving average).

**What happens:**

1. User selects: x=year, y=sales, periods=5, method=linear
2. Frontend calls `POST /api/queries/forecast`
3. Backend (`services/forecaster.py`):
   - **Linear Regression**: fits `y = mx + b` using `np.polyfit(x, y, 1)`
     - Calculates slope (m) and intercept (b)
     - R² = 1 - (SS_residual / SS_total) → confidence score
     - Extrapolates the line for 5 future points
   - **Moving Average**: takes last 3 values, averages them → that's the next prediction
     - Slides window forward for each subsequent prediction
4. Determines trend: rising / falling / stable
5. Returns: historical points + forecast points + trend + confidence + summary
6. Frontend renders a line chart with two colors: blue (historical) + orange/dashed (forecast)

**Files involved:** `Forecast.jsx` → `api/queries.js` → `api/queries.py` → `services/forecaster.py`

---

### 📄 Page 10: Alerts (`/alerts`)

**What the user sees:** Form to create alert rules + list of active alerts + notification feed.

**What happens:**

1. User creates a rule: "Alert me when sales > 70000 in column 'sales'"
2. Backend saves a `SmartAlert` row: dataset_id, column_name, condition (gt/lt/eq), threshold
3. When data is checked, the `alert_engine.py` evaluates: does any value in that column match the condition?
4. If yes → creates an `AlertNotification` row with a message
5. Frontend polls for unread notifications → shows in the notification bell

**Files involved:** `Alerts.jsx` → `api/alerts.js` → `api/alerts.py` → `services/alert_engine.py` → `database/models.py` (SmartAlert, AlertNotification)

---

### 📄 Page 11: Compare (`/compare`)

**What the user sees:** Select two datasets or two query results for side-by-side comparison.

**What happens:**

1. User selects datasets/queries to compare
2. Backend (`api/compare.py`) → `services/data_differ.py`:
   - Computes differences between two result sets
   - Shows what changed, percentage differences
3. Returns comparison data → frontend renders side-by-side view

**Files involved:** `Compare.jsx` → `api/compare.js` → `api/compare.py` → `services/data_differ.py`

---

### 📄 Page 12: What-If / Scenario (`/what-if`)

**What the user sees:** Adjust parameters (e.g., "What if sales increase by 20%?") and see projected impact.

**What happens:**

1. User defines a scenario modification
2. Backend (`api/scenario.py`) applies the modification to a copy of the data
3. Runs the analysis on the modified data
4. Returns original vs modified results for comparison

**Files involved:** `WhatIf.jsx` → `api/scenario.js` → `api/scenario.py`

---

### 📄 Page 13: Dashboard (`/dashboard`)

**What the user sees:** A grid of pinned chart cards — like a mini Power BI.

**What happens:**

1. On the Query page, user clicks "Pin to Dashboard" after getting a result
2. The chart data + config + insights are saved into React's `DashboardContext`
3. Dashboard page reads from this context and renders each pinned item as a card
4. Each card shows: title, chart, key metrics
5. User can remove cards

**Files involved:** `Dashboard.jsx` → `context/DashboardContext.jsx` → `components/ChartRenderer.jsx`

---

### 💬 Chat Sidebar (floating component)

**What the user sees:** A chat icon in the corner. Click → sidebar opens with AI chat.

**What happens:**

1. User types a message
2. Frontend calls `POST /api/chat`
3. Backend (`api/chat.py`) sends the message to Gemini as a general data analysis assistant
4. Returns AI response → displayed in chat bubble

**Files involved:** `ChatSidebar.jsx` → `api/chat.js` → `api/chat.py` → `llm/llm_engine.py`

---

## SHARED COMPONENTS (Used Across Pages)

| Component | What It Does | Used By |
|-----------|-------------|---------|
| `Navbar.jsx` | Top navigation bar with links to all pages + logout button | Every page |
| `ProtectedRoute.jsx` | Checks if JWT exists; if not → redirects to `/login` | All protected pages |
| `ChartRenderer.jsx` | Renders bar/line/pie/scatter/histogram/heatmap/table based on config | Query, Dashboard, Forecast, MultiQuery |
| `InsightDisplay.jsx` | Renders insight highlights with emojis and formatting | Query, MultiQuery |
| `VoiceRecorder.jsx` | Records audio via browser mic, sends to STT API | Query |
| `ErrorBoundary.jsx` | Catches React rendering errors, shows fallback UI instead of blank page | Wraps entire app |
| `SaveQueryModal.jsx` | Modal to save a query as a template for one-click re-use | Query |
| `ReportBuilder.jsx` | Generates PDF reports with charts + insights using jsPDF + html2canvas | Query |
| `NotificationBell.jsx` | Shows unread alert notification count + dropdown | Navbar |
| `ConfirmModal.jsx` | Generic confirmation dialog ("Are you sure?") | Delete actions |

---

## DATABASE TABLES — What Each Stores

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | Registered accounts | id, username, email, hashed_password |
| `query_logs` | Every query ever executed | user_id, natural_query, generated_code, is_valid, chart_type |
| `dataset_records` | Metadata of uploaded files | user_id, dataset_id, filename, filepath, row_count, schema_summary |
| `conversation_ctx` | Chat history for follow-up questions | session_id, user_id, turn_index, query, code, explanation |
| `saved_queries` | Saved query templates for one-click re-use | user_id, name, dataset_id, natural_query, graph_type |
| `scheduled_reports` | Auto-report scheduling rules | user_id, dataset_id, query, frequency, email |
| `smart_alerts` | Alert rules (e.g., "notify when sales > X") | user_id, dataset_id, column_name, condition, threshold |
| `alert_notifications` | Triggered alert messages | alert_id, user_id, message, is_read |
