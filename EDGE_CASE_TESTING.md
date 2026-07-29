# 🧪 Aether AI Platform — Edge Case Testing Checklist

> **Purpose:** Comprehensive page-by-page testing guide to ensure every feature handles edge cases gracefully.  
> **Legend:** ✅ = Pass | ❌ = Fail | ⚠️ = Partial

---

## 1. Registration Page (`/register`)

### Happy Path
- [ ] Register with valid username, email, password → redirects to dashboard
- [ ] Tokens (access + refresh) are saved in localStorage after registration

### Edge Cases
- [ ] **Empty fields** — Submit with all fields empty → should show validation error, not crash
- [ ] **Short password** — Use password < 6 characters (e.g., "abc") → should show "at least 6 characters" error
- [ ] **Invalid email** — Use "notanemail" or "user@" → should show "Invalid email format"
- [ ] **Short username** — Use 1-2 character username (e.g., "ab") → should show validation error
- [ ] **Special chars in username** — Use "user@#$%" → should reject (only letters, numbers, spaces, underscores allowed)
- [ ] **Very long username** — Use 50+ character username → should reject (max 30 chars)
- [ ] **Duplicate username** — Register with an already-taken username → should show "Username already taken"
- [ ] **Duplicate email** — Register with an already-used email → should show "Email already registered"
- [ ] **Spaces in username** — Try "John Doe" → should be accepted (spaces are allowed per regex)
- [ ] **SQL injection in fields** — Try `'; DROP TABLE users; --` as username → should be safely handled (parameterized queries)
- [ ] **Network offline** — Disable network and submit → should show error, not hang forever
- [ ] **Double-click submit** — Rapidly click register twice → should not create duplicate accounts
- [ ] **Password with unicode** — Use password like "pässwörd123" → should work with bcrypt

---

## 2. Login Page (`/login`)

### Happy Path
- [ ] Login with valid credentials → receives tokens, redirects to dashboard
- [ ] User object is populated in AuthContext

### Edge Cases
- [ ] **Empty fields** — Submit with no username/password → should show error
- [ ] **Wrong password** — Correct username, wrong password → "Invalid username or password"
- [ ] **Wrong username** — Non-existent username → "Invalid username or password" (same message, no info leakage)
- [ ] **Case sensitivity** — Login with "Admin" when registered as "admin" → check if it fails (usernames are case-sensitive)
- [ ] **Trailing spaces** — Login with " admin " (spaces around username) → check behavior
- [ ] **Very long input** — Paste 10,000 characters in password field → should handle gracefully
- [ ] **Network error** — Backend is down → should show error message, not blank screen
- [ ] **Already logged in** — Visit /login when already authenticated → should redirect to dashboard
- [ ] **Browser back button** — After login, press back → should not go back to login page

---

## 3. Upload Page (`/upload`)

### Happy Path
- [ ] Upload a valid CSV file → shows success, file appears in dataset list
- [ ] Upload a valid XLSX file → same behavior
- [ ] Dataset list shows filename, row count, column count, upload date

### Edge Cases
- [ ] **Empty file** — Upload a 0-byte CSV → should show meaningful error
- [ ] **Large file** — Upload file > 50MB → should show "File too large" error
- [ ] **Wrong format** — Upload .txt, .pdf, .json, .png → should reject with format error
- [ ] **CSV with no headers** — Upload CSV without header row → check how it handles (uses row 1 as headers)
- [ ] **CSV with only headers** — Upload CSV with headers but 0 data rows → should upload but show 0 rows
- [ ] **CSV with mixed encodings** — Upload UTF-8-BOM or Latin-1 encoded CSV → check if it reads correctly
- [ ] **CSV with commas in values** — Upload CSV where values contain commas (quoted) → should parse correctly
- [ ] **CSV with special characters** — Column names with spaces, unicode, emoji → check schema extraction
- [ ] **Excel with multiple sheets** — Upload .xlsx with 3 sheets → check which sheet is read (typically first)
- [ ] **Corrupted file** — Upload a .csv that is actually a renamed .jpg → should show error
- [ ] **Duplicate upload** — Upload the same file twice → should create separate dataset entries
- [ ] **Delete dataset** — Delete a dataset → should remove from list, subsequent queries on it should fail gracefully
- [ ] **Delete dataset while query is running** — Edge race condition → should not crash
- [ ] **No datasets uploaded** — Visit upload page fresh → should show empty state, not error
- [ ] **Drag and drop** — Drag file onto upload area → should work same as file picker
- [ ] **Cancel upload mid-way** — If possible, cancel during upload → should not leave partial state
- [ ] **Unauthenticated upload** — Try uploading without being logged in → should redirect to login (401)

---

## 4. Data Cleaning Page (`/cleaning`)

### Happy Path
- [ ] Select a dataset → shows data preview and quality metrics
- [ ] Drop null rows → row count decreases, missing values update
- [ ] Fill mean/median/mode → missing values become 0
- [ ] Remove duplicates → duplicate count becomes 0
- [ ] Drop column → column disappears from preview

### Edge Cases
- [ ] **No dataset selected** — Visit page without selecting dataset → should show prompt to select, not crash
- [ ] **Dataset with zero nulls** — Apply "drop nulls" → should do nothing, show success message
- [ ] **Dataset with zero duplicates** — Apply "remove duplicates" → should do nothing gracefully
- [ ] **All rows are null** — Apply "drop nulls" on fully-null dataset → should result in 0 rows, show warning
- [ ] **Fill mean on non-numeric column** — Apply fill mean on a categorical column → should skip or show error
- [ ] **Fill mean on column with all NaN** — No valid values to compute mean → should handle (NaN mean)
- [ ] **Drop the only column** — Drop the single remaining column → should show warning or empty dataset
- [ ] **Multiple operations in sequence** — Drop nulls → fill mean → remove duplicates → verify cumulative effect
- [ ] **Undo support** — Check if operations can be reverted (or if they're permanent)
- [ ] **Very large dataset** — Clean a 100K+ row dataset → should not time out or freeze UI
- [ ] **Dataset with mixed types** — Column has "123", "abc", "456" → fill mean should handle or skip

---

## 5. Query Page (`/query`) — ⭐ Most Critical Page

### Happy Path
- [ ] Type "show average sales by region" → generates code, shows chart, insights, narration
- [ ] Chart type matches data (bar for categorical+numeric, line for time series)
- [ ] Insights show meaningful text (not raw numbers)
- [ ] Follow-up suggestions appear and are clickable

### Edge Cases — Input
- [ ] **Empty query** — Submit with empty input → should show validation error
- [ ] **Very long query** — Paste a 5000-character query → should handle (may truncate for LLM)
- [ ] **Non-English query** — Type in Hindi/Spanish → check if Gemini handles or fallback triggers
- [ ] **Query with SQL injection** — "DROP TABLE users" → should not execute SQL (it generates Pandas, not SQL)
- [ ] **Query with code injection** — "import os; os.system('rm -rf /')" → AST checker should block
- [ ] **Ambiguous query** — "show me everything" → should fallback to df.head(10) or df.describe()
- [ ] **Query about non-existent column** — "show average of xyz_column" → should handle gracefully
- [ ] **Query with typos** — "show averge of sales" → check if Gemini still understands
- [ ] **Numeric-only query** — "12345" → should not crash
- [ ] **Special characters** — "show $ales & re%venue" → should handle without error

### Edge Cases — No Dataset
- [ ] **Query without dataset selected** — Should show "please select/upload a dataset first"
- [ ] **Query on deleted dataset** — Select dataset, delete it, then query → should show error

### Edge Cases — Results
- [ ] **Scalar result** — "what is the total revenue" → should show single value, not crash chart
- [ ] **Empty result** — Query that filters everything out → should show "no data" message
- [ ] **Huge result** — Query returning 10,000+ rows → should be truncated to 500 rows
- [ ] **All-null result** — Query on fully null column → should handle NaN values in chart
- [ ] **Negative values** — Charts with negative numbers → should render correctly (bar below axis)
- [ ] **Very large numbers** — Values in billions → should format with commas, not overflow chart
- [ ] **Very small decimals** — Values like 0.000001 → should display with proper precision

### Edge Cases — Chart Types
- [ ] **Bar chart** — Verify x-axis labels don't overlap for many categories
- [ ] **Pie chart** — Verify with 1 slice, 2 slices, and 20+ slices
- [ ] **Line chart** — Verify with 2 data points (minimum for a line)
- [ ] **Scatter plot** — Verify with identical x,y values (overlapping dots)
- [ ] **Histogram** — Verify with all same values (single bin)
- [ ] **Heatmap** — Verify with 2×2 matrix and 15×15 matrix
- [ ] **Data table** — Verify with 0 columns edge case
- [ ] **Manual chart override** — Select "pie" for 100-row result → should still render

### Edge Cases — Anomalies
- [ ] **No anomalies** — Dataset with no outliers → anomaly section should be empty/hidden
- [ ] **All anomalies** — Every value is an outlier → should not highlight everything red
- [ ] **Single data point** — Only 1 row → anomaly detection should skip (needs ≥5 points)

### Edge Cases — Conversational Context
- [ ] **Follow-up query** — "now show only for Mumbai" after a city query → should modify previous code
- [ ] **Follow-up after page refresh** — Context is DB-backed → should still work
- [ ] **Cross-dataset follow-up** — Switch dataset mid-conversation → context should reset per dataset

### Edge Cases — Voice Input
- [ ] **Click mic, say nothing** — Should show "No speech detected" after timeout
- [ ] **Deny microphone permission** — Should show "Microphone access denied" error
- [ ] **Very long speech** — Speak for 60 seconds → check if it captures or truncates
- [ ] **Background noise** — Should either transcribe poorly or show "No speech detected"
- [ ] **Click mic twice rapidly** — Should not start two recording sessions

### Edge Cases — Pin to Dashboard
- [ ] **Pin result** — Verify it appears on dashboard with correct chart
- [ ] **Pin multiple results** — Pin 10+ results → dashboard should handle layout
- [ ] **Pin with empty data** — Try pinning a failed/empty result → should prevent or handle

### Edge Cases — Save Query
- [ ] **Save with empty name** — Should show validation error
- [ ] **Save duplicate name** — Save two queries with same name → check behavior
- [ ] **Save very long name** — 200+ character name → should truncate or reject

---

## 6. Dashboard Page (`/dashboard`)

### Happy Path
- [ ] Shows pinned chart panels in a grid layout
- [ ] Panels are draggable and resizable
- [ ] Remove button works on individual panels

### Edge Cases
- [ ] **Empty dashboard** — No pinned panels → should show helpful empty state
- [ ] **Drag panel** — Drag panel to new position → position should persist after refresh
- [ ] **Resize panel** — Make very small → chart should scale or show minimum size
- [ ] **20+ panels** — Performance with many charts → should not lag significantly
- [ ] **Clear all** — Click "Clear All" → all panels removed, localStorage cleared
- [ ] **Corrupted localStorage** — Manually corrupt dashboard_panels in localStorage → should fallback to empty
- [ ] **Panel with old/invalid data** — If chart data format changed → should render without crash (ErrorBoundary)

---

## 7. Data Profile Page (`/profile`)

### Happy Path
- [ ] Select dataset → shows comprehensive profile (overview, missing values, types, stats, correlation)

### Edge Cases
- [ ] **No dataset selected** — Should show prompt to select one
- [ ] **Dataset with 1 row** — Statistics will have std=NaN → should handle
- [ ] **Dataset with 1 column** — No correlation matrix possible → section should hide
- [ ] **All-null dataset** — Every value is null → missing values should show 100%, stats should handle NaN
- [ ] **1000+ columns** — Should not crash (may be slow, should show loading)
- [ ] **Boolean columns** — Should be categorized as "boolean" type
- [ ] **Date columns** — Should be categorized as "datetime" type
- [ ] **Very long column names** — Should not break the layout

---

## 8. Forecast Page (`/forecast`)

### Happy Path
- [ ] Select x (time) column, y (metric) column → shows historical + forecast chart
- [ ] Linear regression and moving average methods both work
- [ ] Summary text shows trend, confidence, and next predicted value

### Edge Cases
- [ ] **Less than 3 data points** — Should show "Need at least 3 data points" error
- [ ] **Non-numeric y column** — Select categorical column for y → should show error
- [ ] **Constant values** — All y values are the same (e.g., all 100) → slope=0, trend="stable", should not divide by zero
- [ ] **Single outlier** — One extreme value → linear regression should still work (R² will be low)
- [ ] **Negative values** — Forecast with negative numbers → should handle correctly
- [ ] **Zero values** — All zeros → should not divide by zero in change_pct calculation
- [ ] **Very large periods** — Forecast 1000 periods ahead → should handle (may be slow)
- [ ] **Moving average with window > data** — Window auto-adjusts to data length → verify
- [ ] **Date column not parseable** — x column has "Q1 2024" format → should use as string labels

---

## 9. Multi-Query Page (`/multi-query`)

### Happy Path
- [ ] Select 2+ datasets, enter query → results shown side-by-side

### Edge Cases
- [ ] **No datasets selected** — Should show validation error
- [ ] **Single dataset selected** — Should still work (just one result)
- [ ] **Datasets with different schemas** — Query "show average salary" but only one has "salary" column → should show error for that dataset, success for the other
- [ ] **Same query, different results** — Verify each dataset gets independent results
- [ ] **Very long query** — Should handle without UI overflow
- [ ] **All datasets fail** — Query makes no sense for any dataset → should show errors for all

---

## 10. Alerts Page (`/alerts`)

### Happy Path
- [ ] Create alert rule (column > threshold) → appears in active alerts list
- [ ] Alert triggers when data meets condition → notification appears

### Edge Cases
- [ ] **Invalid threshold** — Enter "abc" as threshold → should show validation error
- [ ] **Negative threshold** — Enter -100 → should be valid (some data can be negative)
- [ ] **Column that doesn't exist** — Type a non-existent column name → should show error when checking
- [ ] **Non-numeric column** — Create alert on categorical column → should skip during check
- [ ] **Zero matching values** — Alert with very high threshold that nothing matches → should not trigger
- [ ] **All values match** — Every value triggers → should show count accurately
- [ ] **Delete alert** — Remove an alert → should no longer trigger
- [ ] **Toggle active/inactive** — Inactive alerts should not be checked
- [ ] **Empty alert label** — Should auto-generate label from column + condition + threshold
- [ ] **Duplicate alerts** — Create same rule twice → both should fire independently

---

## 11. Compare Page (`/compare`)

### Happy Path
- [ ] Select two datasets → shows side-by-side comparison

### Edge Cases
- [ ] **Same dataset twice** — Compare dataset with itself → should show identical results
- [ ] **Datasets with no common columns** — Should show that columns don't overlap
- [ ] **One dataset empty** — Compare full dataset with empty one → should handle
- [ ] **Very different sizes** — Compare 10-row vs 100K-row dataset → should handle

---

## 12. What-If / Scenario Page (`/what-if`)

### Happy Path
- [ ] Modify a column value and see how results change

### Edge Cases
- [ ] **No dataset selected** — Should show prompt
- [ ] **Modify to negative value** — Should be allowed for numeric columns
- [ ] **Modify to non-numeric** — Enter "abc" in a numeric field → should show error
- [ ] **Modify to empty** — Clear a value → should handle (treat as null?)
- [ ] **Extreme values** — Enter 999999999999 → should not crash calculations

---

## 13. History Page (`/history`)

### Happy Path
- [ ] Shows list of past queries with timestamps, code, chart type
- [ ] Can re-run a past query

### Edge Cases
- [ ] **No history** — First-time user → should show empty state
- [ ] **Re-run deleted dataset** — Re-run query for a dataset that no longer exists → should show error
- [ ] **Very long query text** — Should truncate in list view, show full on expand
- [ ] **100+ entries** — Should paginate or virtual-scroll, not render all at once
- [ ] **Invalid/failed queries** — Past queries that failed → should show "invalid" status

---

## 14. Chat Sidebar

### Happy Path
- [ ] Open sidebar → can type and get AI responses
- [ ] Follow-up questions maintain context

### Edge Cases
- [ ] **Empty message** — Submit empty → should not send
- [ ] **Very long message** — 5000+ characters → should handle
- [ ] **Rapid messages** — Send 10 messages in 2 seconds → should queue, not crash
- [ ] **Open/close rapidly** — Toggle sidebar fast → should not glitch animation
- [ ] **No dataset context** — Chat without any dataset → should still respond or ask to upload
- [ ] **New chat** — Start new session → previous context should clear

---

## 15. Navbar / Navigation

### Edge Cases
- [ ] **Collapse/expand sidebar** — All pages should remain accessible
- [ ] **Active page highlight** — Current page should be highlighted in nav
- [ ] **Mobile responsive** — Nav should collapse to hamburger on small screens
- [ ] **Notification bell** — Shows unread count, clicking shows dropdown
- [ ] **Logout** — Clears tokens, redirects to login, can't access protected pages

---

## 16. Authentication / Token Edge Cases (Global)

### Edge Cases
- [ ] **Expired access token** — Make a request after 2 hours → should auto-refresh
- [ ] **Expired refresh token** — After 7 days → should redirect to login
- [ ] **Manually delete token** — Remove token from localStorage → next request should redirect to login
- [ ] **Tampered token** — Modify JWT payload in localStorage → should get 401, redirect to login
- [ ] **Multiple tabs** — Login in tab 1, open tab 2 → should be authenticated in tab 2
- [ ] **Logout in one tab** — Logout in tab 1 → tab 2 should redirect on next action
- [ ] **Concurrent 401s** — 5 simultaneous requests all get 401 → should only refresh once (queue pattern)

---

## 17. Network / Error Edge Cases (Global)

### Edge Cases
- [ ] **Backend down** — Frontend should show error toast/message, not white screen
- [ ] **Slow network** — 5+ second response times → loading spinners should appear
- [ ] **Request timeout** — Backend takes 30+ seconds → should timeout gracefully
- [ ] **CORS error** — Check that all API calls work from the frontend origin
- [ ] **404 route** — Visit `/nonexistent` → should redirect to dashboard
- [ ] **Browser back/forward** — Navigation history should work correctly
- [ ] **Page refresh** — Refresh any page → should maintain auth state (tokens in localStorage)
- [ ] **localStorage full** — If localStorage is full → dashboard panel save should fail gracefully
- [ ] **Incognito mode** — All features should work (localStorage is available in incognito)

---

## 18. Security Edge Cases

### Backend
- [ ] **SQL injection** — Parameterized queries via SQLAlchemy ORM → should be safe
- [ ] **Code injection** — `__import__('os').system('...')` in generated code → AST checker should block
- [ ] **Dunder traversal** — `().__class__.__mro__[1].__subclasses__()` → AST checker should block
- [ ] **exec/eval injection** — `exec('malicious')` → blocked by AST checker
- [ ] **File access** — `open('/etc/passwd')` → blocked by AST checker
- [ ] **Import injection** — `import os` in generated code → blocked by AST checker
- [ ] **Infinite loop** — `while True: pass` → 10-second timeout should kill it
- [ ] **Memory bomb** — `df.explode()` on huge data → should be bounded by 500-row limit
- [ ] **Unauthenticated API access** — Call `/api/queries` without token → should return 401
- [ ] **Cross-user data access** — User A should not see User B's datasets or queries

### Frontend
- [ ] **XSS in query input** — Type `<script>alert('xss')</script>` → should be escaped in rendering
- [ ] **XSS in dataset names** — Upload file named `<img onerror=alert(1)>.csv` → should be escaped
- [ ] **Token in URL** — Tokens should never appear in URLs (only in headers)
- [ ] **Console sensitive data** — Tokens should not be logged to console in production

---

## 19. PDF Report Generation

### Happy Path
- [ ] Generate detailed PDF → downloads file with cover page, insights, data table
- [ ] Generate summary PDF → downloads file with cover page and insights only

### Edge Cases
- [ ] **No data** — Generate report with empty result → should show error or minimal PDF
- [ ] **Very long query text** — Query wraps on cover page without overflow
- [ ] **Unicode in data** — Data with Hindi/Chinese characters → should render in PDF (or show fallback)
- [ ] **100+ columns** — Data table should truncate to 6 columns
- [ ] **Very long insight text** — Should paginate properly, not overflow page
- [ ] **Rapid generation** — Click "Generate" twice → should not create duplicate downloads
- [ ] **Large dataset** — 500-row table in detailed report → should paginate across PDF pages

---

## 20. Performance Edge Cases

- [ ] **Large file upload** — 40MB CSV → upload should complete within reasonable time
- [ ] **Complex query** — Multi-group, multi-aggregate → backend should respond within 10s timeout
- [ ] **Many concurrent users** — Multiple users querying simultaneously → connection pool should handle
- [ ] **Dashboard with 20 charts** — Page should load and scroll smoothly
- [ ] **Rapid page navigation** — Switch pages quickly → no memory leaks or zombie requests
- [ ] **Long session** — Use app for 2+ hours → token refresh should keep session alive

---

## Quick Reference: Common Failure Patterns

| Pattern | Where It Breaks | Fix Check |
|---------|----------------|-----------|
| Divide by zero | Forecaster (change_pct), Insight generator (ratios) | Check with constant/zero data |
| NaN in chart | ChartRenderer with null numeric data | Check with all-null columns |
| Empty array | Insight generator with 0 rows | Check query that returns nothing |
| Token expired | Any API call after 2 hours idle | Check auto-refresh behavior |
| Race condition | Delete dataset + run query simultaneously | Check error handling |
| Timeout | Complex queries on large datasets | Check 10s timeout behavior |
| Layout overflow | Long column names, long query text, many categories | Check responsive design |
| Missing fallback | Gemini API key not set | Check keyword stub works |

---

> 💡 **Testing Tip:** Start from the **Registration page** and work through the app sequentially — register, login, upload, clean, query, forecast, alerts, dashboard. This simulates the real user flow and catches integration issues between pages.
