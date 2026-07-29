# 🗄️ Neon + FastAPI Setup Guide
## Generative AI Analysis Platform

---

## PART 1 — Connect FastAPI Backend to Neon (Your App's Database)

### Step 1: Create Neon Account & Project

1. Go to **https://neon.tech** → Click **Sign Up** (free)
2. Click **"New Project"**
3. Set:
   - Project Name: `ai-analysis-platform`
   - Region: choose closest to you (e.g., `Asia Pacific (Singapore)`)
4. Click **Create Project**

### Step 2: Get Your Connection String

1. On the Neon dashboard → Click **"Connect"** button
2. Select:
   - **Framework:** Python
   - **Driver:** psycopg2
3. Copy the connection string. It looks like:
   ```
   postgresql://neondb_owner:AbcXyz123@ep-cool-wind-a1b2c3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

### Step 3: Update Your .env File

Open `.env` in the project root and replace the `DATABASE_URL` line:

```env
# Paste your Neon string here — add +psycopg2 after "postgresql"
DATABASE_URL=postgresql+psycopg2://neondb_owner:AbcXyz123@ep-cool-wind-a1b2c3.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> ⚠️ The ONLY change from Neon's string is adding `+psycopg2` after `postgresql`

### Step 4: Test the Connection

```bash
cd backend
uvicorn main:app --reload
```

Watch the terminal. If you see:
```
INFO:     Application startup complete.
```
✅ Tables were auto-created in Neon. Open https://console.neon.tech and you'll see `users` and `query_logs` tables appear.

---

## PART 2 — Neon MCP Server (AI Assistant Controls Your DB)

The MCP Server lets your AI coding assistant (Cursor/VS Code) manage your
Neon database using natural language from the chat panel.

### Step 1: Get Your Neon API Key

1. Go to **https://console.neon.tech/app/settings/api-keys**
2. Click **"Generate new API key"**
3. Name it: `mcp-dev-key`
4. Copy the key (starts with `napi_...`)

### Step 2A: If using Cursor

1. Open `.cursor/mcp.json` (already created in this project)
2. Replace `YOUR_NEON_API_KEY_HERE` with your actual key:
   ```json
   {
     "mcpServers": {
       "neon": {
         "command": "npx",
         "args": ["-y", "@neondatabase/mcp-server-neon", "start", "napi_your_actual_key"]
       }
     }
   }
   ```
3. Restart Cursor
4. Open the AI chat → type: **"List my Neon projects"**

### Step 2B: If using VS Code

1. Open `.vscode/mcp.json` (already created in this project)
2. Replace `YOUR_NEON_API_KEY_HERE` with your actual key
3. Restart VS Code → open Copilot/AI chat → type: **"List my Neon projects"**

### Step 2C: Quick Setup (Auto-detects your editor)

Run this in a terminal inside your project folder:
```bash
npx neonctl@latest init
```
Follows prompts → OAuth browser window opens → Authorize → Restart editor.

### Step 2D: OAuth Setup (No API key needed)

```bash
npx add-mcp https://mcp.neon.tech/mcp
```

---

## What You Can Do with MCP (Natural Language Commands)

Once connected, type these into your AI chat panel:

| Say this | What happens |
|---|---|
| `"List my Neon projects"` | Shows all your databases |
| `"Show tables in my database"` | Lists users, query_logs, etc. |
| `"SELECT * FROM users LIMIT 5"` | Runs SQL query |
| `"Create a test branch"` | Makes a safe Git-like branch for testing |
| `"Show slow queries"` | Performance analysis |
| `"Compare schema between branches"` | Schema diff |

---

## ⚠️ Security Reminders

1. **Never commit `.env` to GitHub** — it contains your Gemini API key and DB password
2. **Add to `.gitignore`:**
   ```
   .env
   *.db
   datasets/
   logs/
   __pycache__/
   ```
3. On Render deployment, add `DATABASE_URL` as an environment variable in the Render dashboard — never in code

---

## Architecture After Neon Migration

```
Local Dev:
  FastAPI (uvicorn) ──► Neon PostgreSQL (cloud)
                         (no local DB install needed!)

Production:
  React (Vercel) ──► FastAPI (Render) ──► Neon PostgreSQL
```
