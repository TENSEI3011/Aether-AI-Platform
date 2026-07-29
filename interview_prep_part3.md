# 🎯 Infosys Interview Prep — Part 3: Advanced Features

---

## Q15. How does the Voice feature work (STT and TTS)?

**Answer:**

### Speech-to-Text (STT):
1. User clicks the microphone button in the frontend → browser's `MediaRecorder` API records audio as WebM
2. Audio blob is sent to `/api/voice/transcribe` as a file upload
3. Backend saves the file temporarily, then uses `speech_recognition` library
4. If the file is non-WAV (WebM/MP3), **pydub** converts it to WAV first
5. `recognizer.recognize_google(audio)` calls Google's free speech recognition API
6. Returns `{ transcript, confidence, language }`
7. The transcript is then used as the natural language query

### Text-to-Speech (TTS):
1. After query execution, the AI generates a narration string
2. Frontend sends narration text to `/api/voice/speak`
3. Backend uses **gTTS** (Google Text-to-Speech) to convert text → MP3
4. The MP3 is stored in a `BytesIO` buffer (in-memory, no disk write)
5. Converted to **base64** string and returned in JSON
6. Frontend decodes base64 → creates an `Audio` object → plays it

**Key design choice:** No API key needed for either STT or TTS — both use Google's free public endpoints.

---

## Q16. How does the Forecasting feature work?

**Answer:**
I implemented two forecasting methods using **only NumPy** (no scikit-learn needed):

### Linear Regression:
1. Takes historical data points (x, y values)
2. Fits a line `y = mx + b` using `np.polyfit(x, y, 1)` (least squares method)
3. Calculates **R² score** (coefficient of determination) = `1 - (SS_res / SS_tot)` for confidence
4. Extrapolates the line for N future periods
5. Determines trend: `rising` if slope > 1% of mean, `falling` if < -1%, else `stable`

### Moving Average:
1. Takes the last `window` data points (default window = 3)
2. Averages them to predict the next value
3. Slides the window forward (adds prediction, drops oldest) for subsequent predictions
4. Uses data smoothness as a proxy for confidence

**Output:** Historical points + forecast points + trend + confidence + human-readable summary

---

## Q17. How does Anomaly Detection work?

**Answer:**
I use two statistical methods that complement each other:

### Z-Score Method:
- Calculates `z = (value - mean) / std_deviation` for each data point
- Flags values where `|z| > 3` (more than 3 standard deviations from mean)
- Best for: normally distributed data
- Tells you: "This value is statistically extreme"

### IQR Method:
- Calculates Q1 (25th percentile), Q3 (75th percentile), IQR = Q3 - Q1
- Lower fence = `Q1 - 1.5 × IQR`, Upper fence = `Q3 + 1.5 × IQR`
- Flags values outside these fences
- Best for: skewed data (doesn't assume normal distribution)
- Tells you: "This value is outside the typical range"

**Why both?** Z-score is sensitive to outliers themselves (one extreme value shifts the mean). IQR is robust — it uses medians/quartiles which aren't affected by outliers. Using both catches more anomalies.

Both thresholds (z_threshold, iqr_multiplier) are **user-configurable** via the API request.

---

## Q18. What is the Multi-Dataset JOIN feature?

**Answer:**
This feature lets users query across **two different uploaded datasets** simultaneously. For example, if you have a "sales.csv" and "products.csv", you can ask "Show total sales by product category."

**How it works:**
1. User selects two datasets and specifies the join column (common key)
2. Backend loads both DataFrames
3. Uses `pd.merge(df1, df2, on=join_column, how=join_type)` — supports inner, left, right, outer joins
4. The merged DataFrame goes through the same query pipeline (LLM → validate → execute → visualize)
5. Schema from both datasets is combined in the LLM prompt

---

## Q19. How does the Conversational Context Manager work?

**Answer:**
The context manager enables **follow-up questions**. If you ask "Show average sales by region" and then "Now filter only for North", the system understands "Now" refers to the previous query.

**Implementation (Hybrid Memory + DB):**
1. Each query session has a unique `session_id`
2. After each successful query, the `(query, code, explanation)` is stored:
   - **In-memory dict** (fast path for current session)
   - **conversation_ctx DB table** (survives server restarts)
3. On the next query, if `session_id` is provided, the context manager builds a `PREVIOUS CONVERSATION` string
4. This string is injected into the LLM prompt template via `build_contextual_prompt()`
5. The LLM sees previous queries/code and can modify them for follow-ups

**Scoping:** Context is scoped by `(session_id, dataset_id)` — prevents cross-dataset column hallucinations.

**Limit:** Max 6 turns per session (oldest are trimmed from both memory and DB).

---

## Q20. How does the Visualization Selector automatically choose chart types?

**Answer:**
The `viz_selector.py` analyses the query result's **shape and column types**:

| Condition | Chart Type |
|-----------|-----------|
| Datetime + Numeric | Line chart |
| Category + Numeric (≤6 categories) | Pie chart |
| Category + Numeric (>6 categories) | Bar chart |
| 2 Numeric columns, many rows | Scatter plot |
| Single numeric column | Histogram |
| Square numeric matrix (like df.corr()) | Heatmap |
| Everything else | Data table |

The user can always **override** this by selecting a graph type manually (the `graph_type` parameter).

---

## Q21. Explain the Dashboard feature.

**Answer:**
The Dashboard is a **Power BI–style** pinnable dashboard:
1. After running any query, the user can click "Pin to Dashboard"
2. This saves the query result (data + chart config + insights) to a React Context (`DashboardContext`)
3. The Dashboard page displays all pinned items as **cards** in a grid layout
4. Each card shows the chart, key metrics, and a title
5. Users can remove pinned items
6. Data is persisted using React state management

---

## Q22. How does the Data Profiling feature work?

**Answer:**
When a user wants to understand their dataset before querying, the Data Profile page provides:
1. **Per-column statistics**: mean, median, std, min, max, quartiles, null count, unique count
2. **Distribution charts**: histograms for numeric columns
3. **Correlation matrix**: heatmap showing relationships between all numeric columns
4. **Top values**: Most frequent values for categorical columns
5. **Data quality score**: Percentage of non-null values

The `data_profiler.py` service generates this using Pandas' `.describe()`, `.corr()`, `.value_counts()`, and custom logic.

---

## Q23. How does Docker containerisation work in your project?

**Answer:**
The `docker-compose.yml` orchestrates **3 services**:

1. **postgres**: PostgreSQL 15 Alpine image with health check (`pg_isready`)
2. **backend**: Built from `backend/Dockerfile` — installs Python deps, runs uvicorn
3. **frontend**: Built from `frontend/Dockerfile` — installs npm deps, runs Vite dev server

**Key configurations:**
- Backend `depends_on` postgres (waits for health check to pass)
- Frontend `depends_on` backend
- `DATABASE_URL` is overridden to point to the Docker postgres service
- Datasets directory is mounted as a volume for persistence
- Named volume `postgres_data` persists database across container restarts

**Commands:**
```bash
docker compose up --build     # Start everything
docker compose down -v        # Stop and clean up
```

---

## Q24. What is SQLAlchemy and how do you use it?

**Answer:**
SQLAlchemy is a Python **ORM (Object-Relational Mapper)**. Instead of writing raw SQL, I define Python classes that map to database tables:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    hashed_password = Column(String(255))
```

Then I can do: `db.query(User).filter(User.username == "john").first()` instead of `SELECT * FROM users WHERE username='john'`.

**Benefits:**
- Database-agnostic (same code works with PostgreSQL and SQLite)
- Prevents SQL injection (parameterised queries automatically)
- Type safety and autocompletion
- Migration support

I use the **declarative base** pattern and a **session factory** (`SessionLocal`) with a `get_db()` dependency that yields a session and ensures cleanup.

---

## Q25. What is Neon DB and why did you choose it?

**Answer:**
Neon is a **serverless PostgreSQL** service. It provides:
- Full PostgreSQL compatibility
- **Auto-scaling**: scales to zero when idle (saves cost)
- **Free tier**: 500MB storage, enough for a student project
- **Branching**: can create database branches (like git)
- Works natively with Vercel for deployment

I chose it because:
1. No need to run a PostgreSQL server locally
2. Data persists even when my laptop is off
3. The connection string works in both local dev and deployed environments
4. `pool_pre_ping=True` handles connection recycling (important for serverless where connections can be dropped)
