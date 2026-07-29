# 🎯 Infosys Interview Prep — Part 2: Core Pipeline & Security

---

## Q8. Walk me through the complete query pipeline — what happens when a user asks a question?

**Answer (step by step):**

**Step 1 — User types:** "Show average sales by region"

**Step 2 — Frontend** sends POST to `/api/queries/ask` with `{ dataset_id, query, graph_type, session_id }` and JWT in header.

**Step 3 — Authentication**: `get_current_user` dependency decodes the JWT, extracts the username, queries the DB for the User object. If invalid → 401.

**Step 4 — Dataset Ownership Check**: Verifies the dataset belongs to this user (prevents accessing other users' data).

**Step 5 — Load DataFrame**: Reads the CSV/Excel file from disk into a Pandas DataFrame.

**Step 6 — Schema Extraction**: Extracts column names, types (numeric/categorical/datetime), sample values, null counts → builds a schema summary string.

**Step 7 — LLM Code Generation**: The schema summary + user query are injected into a **prompt template** and sent to Google Gemini. The LLM returns Pandas code like:
```python
df.groupby('region')['sales'].mean().reset_index().sort_values('sales', ascending=False)
```

**Step 8 — Validation (3 layers)**:
- **Syntax check**: `ast.parse(code)` — is it valid Python?
- **Blocked patterns**: Regex scan for `import`, `exec`, `eval`, `os.`, `sys.`, `__dunder__`, `.drop()`, `to_csv`, `DELETE`, `DROP`, etc.
- **Schema consistency**: String literals in code are checked against actual column names

**Step 9 — AST Safety Check**: Walks the Abstract Syntax Tree to block:
- Dunder attribute access (`__class__`, `__mro__`, `__subclasses__`)
- Import statements
- Dangerous function calls (`exec`, `eval`, `compile`, `open`, `getattr`)

**Step 10 — Execution**: Code runs in a **sandboxed namespace**:
```python
exec(code, {"__builtins__": {}}, {"df": df.copy(), "pd": pd})
```
- DataFrame is a **copy** (original never mutated)
- `__builtins__` is empty (no `print`, `open`, `import`)
- 10-second **timeout** via threading

**Step 11 — Visualization Selection**: Analyses result shape:
- Category + Numeric → Bar chart
- Datetime + Numeric → Line chart
- ≤6 categories → Pie chart
- 2 numeric, many rows → Scatter
- Square numeric matrix → Heatmap
- User can override with `graph_type`

**Step 12 — Insight Generation**: Produces analyst-style highlights:
- "📈 Highest SALES: **North** at 45,230 — 3.2× higher than South (14,134)"
- Compares top vs bottom, calculates above-average count, detects trends

**Step 13 — Anomaly Detection**: Z-score (|z| > 3) and IQR (Q1-1.5×IQR to Q3+1.5×IQR) methods flag outliers

**Step 14 — AI Narration**: Gemini writes a 2-3 sentence prose summary for text-to-speech

**Step 15 — Follow-up Suggestions**: Gemini suggests 3 smart next questions

**Step 16 — Query Logging**: Saves to `query_logs` table (user_id, query, code, validity, result_summary)

**Step 17 — Context Storage**: Saves to `conversation_ctx` for follow-up question support

**Step 18 — Response**: JSON with data, columns, chart config, insights, anomalies, narration, suggestions → rendered by React

---

## Q9. How does the LLM Engine work? Explain the Gemini integration.

**Answer:**
The `LLMEngine` class is a **singleton** initialised at module level. On startup:
1. Reads `GEMINI_API_KEY` from settings
2. Creates a `genai.Client(api_key=...)` using the `google-genai` SDK
3. If no key or init fails → sets `is_stub = True` (fallback mode)

**When generating code:**
- Builds a structured prompt using `prompt_templates.py` that includes RULES (read-only, no imports, case-sensitive columns) + DATASET SCHEMA + USER QUESTION
- Calls `client.models.generate_content(model="gemini-2.0-flash", contents=prompt)`
- Parses the response: extracts code from ` ```python ``` ` blocks using regex
- Returns `{ code, confidence, explanation }`

**Fallback (Stub Engine):**
If Gemini is unavailable (no API key, quota exhausted, network error), the stub engine uses **keyword matching**:
- Detects keywords: "average"→ `.mean()`, "sum"→ `.sum()`, "count"→ `.value_counts()`, "trend"→ `.groupby(date)`, "outlier"→ IQR formula
- Extracts actual column names from schema to build correct code
- Returns confidence 0.85 (vs 0.90 for Gemini)

This ensures the app **never fully breaks** even without internet.

---

## Q10. How do you ensure LLM-generated code is safe to execute?

**Answer:**
I implemented **Defence in Depth** — 4 independent security layers:

### Layer 1: Regex Pattern Blocking (`query_validator.py`)
Scans code against 20+ blocked patterns:
- `import`, `from X import`, `__dunder__`, `exec`, `eval`, `compile`
- `globals`, `locals`, `open`, `os.`, `sys.`, `subprocess`, `shutil`
- `.drop()`, `to_csv`, `to_excel`, `to_sql` (write operations)
- `DELETE`, `UPDATE`, `DROP`, `INSERT`, `ALTER` (SQL injection)

### Layer 2: Syntax Validation
```python
ast.parse(code)  # Ensures it's valid Python before execution
```

### Layer 3: AST-Level Deep Inspection (`query_executor.py`)
Walks the entire Abstract Syntax Tree node by node:
- **Blocks dunder traversal**: `().__class__.__mro__[1].__subclasses__()` — this is a known Python sandbox escape technique
- **Blocks import nodes**: `ast.Import`, `ast.ImportFrom`
- **Blocks dangerous calls**: `exec()`, `eval()`, `compile()`, `open()`, `getattr()`, `setattr()`, `__import__()`

### Layer 4: Restricted Execution Namespace
```python
exec(code, {"__builtins__": {}}, {"df": df_copy, "pd": pd})
```
- `__builtins__` is set to empty dict — no `print()`, `open()`, `input()`, `import` available
- Only `df` (a copy) and `pd` (pandas) are in scope
- Original DataFrame is **never** passed — always `.copy()`
- 10-second **timeout** prevents infinite loops

---

## Q11. What is AST and why did you use it for security?

**Answer:**
**AST** stands for **Abstract Syntax Tree**. When Python code is compiled, it's first parsed into a tree structure where each node represents a syntactic element (function call, attribute access, import, variable, etc.).

I use `ast.parse(code)` to build this tree, then `ast.walk(tree)` to visit every node. This is more secure than regex because:

- **Regex can be fooled**: `ev` + `al` concatenation bypasses regex for `eval`
- **AST cannot be fooled**: The AST always correctly identifies `eval` as a function call node, regardless of string tricks
- It catches **object traversal attacks** like `().__class__.__mro__[1].__subclasses__()` which is a known way to escape Python sandboxes

Example of what I block:
```python
# This would normally let you access any class in Python:
().__class__.__mro__[1].__subclasses__()[132].__init__.__globals__['system']('rm -rf /')
# My AST walker catches __class__, __mro__, __subclasses__, __init__, __globals__
```

---

## Q12. What is the difference between access token and refresh token?

**Answer:**

| Aspect | Access Token | Refresh Token |
|--------|-------------|---------------|
| Purpose | Authenticate API requests | Get new access tokens |
| Lifespan | Short (2 hours in my app) | Long (7 days in my app) |
| Sent with | Every API request in `Authorization` header | Only to `/api/auth/refresh` endpoint |
| Contains | `{sub: username, exp: timestamp, type: "access"}` | `{sub: username, exp: timestamp, type: "refresh"}` |
| If stolen | Attacker has 2-hour window | Attacker can generate new access tokens |

**Flow:**
1. Login → server returns both access + refresh tokens
2. Frontend stores both in localStorage
3. Every request → access token in header
4. Access token expires → Axios interceptor catches 401 → sends refresh token to `/api/auth/refresh` → gets new pair → retries original request
5. User never sees interruption

**Why both?** If we only had one long-lived token, a stolen token gives permanent access. With short-lived access tokens, the damage window is limited. The refresh token is only sent to one specific endpoint, reducing exposure.

---

## Q13. How does JWT authentication work in your project?

**Answer:**
1. **Registration**: User submits username + email + password → password is hashed with **bcrypt** (salt + hash) → stored in DB → JWT pair issued
2. **Login**: User submits username + password → bcrypt verifies against stored hash → if valid, JWT pair issued
3. **Token Creation**: `jwt.encode({sub: username, exp: timestamp, type: "access"}, SECRET_KEY, algorithm="HS256")`
4. **Token Verification**: On every protected endpoint, `get_current_user` dependency:
   - Extracts token from `Authorization: Bearer <token>` header
   - `jwt.decode(token, SECRET_KEY, algorithms=["HS256"])` — verifies signature + expiry
   - Extracts `sub` (username) → queries DB → returns User object
   - If invalid → raises `401 Unauthorized`
5. **Password never stored in plain text** — only the bcrypt hash

**HS256** means HMAC-SHA256 — a symmetric algorithm where the same secret key signs and verifies the token.

---

## Q14. What is CORS and why do you need it?

**Answer:**
**CORS** = Cross-Origin Resource Sharing. Browsers block requests from one origin (e.g., `localhost:5173`) to a different origin (e.g., `localhost:8000`) by default — this is the **Same-Origin Policy**.

Since my frontend (port 5173) and backend (port 8000) are on different ports, the browser treats them as different origins. Without CORS, all API calls would be blocked.

I configure CORS middleware in FastAPI:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend URL
    allow_credentials=True,     # allow cookies/auth headers
    allow_methods=["*"],        # GET, POST, PUT, DELETE
    allow_headers=["*"],        # Authorization, Content-Type, etc.
)
```

This tells the browser: "Requests from localhost:5173 are trusted."
