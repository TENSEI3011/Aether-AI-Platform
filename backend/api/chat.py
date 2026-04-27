"""
============================================================
Chat API — Conversational AI assistant
============================================================
Endpoints:
  POST /api/chat              → Send a chat message
  GET  /api/chat/history/{id} → Get chat history
  GET  /api/chat/datasets     → Get user's datasets for chat
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_user
from database.session import get_db
from database.models import User
from services.context_manager import add_to_context, get_context
from llm.llm_engine import llm_engine
from api.datasets import _datasets as datasets_store

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    session_id: str
    dataset_id: Optional[str] = None


@router.get("/datasets")
def get_chat_datasets(
    current_user: User = Depends(get_current_user),
):
    """Return the user's available datasets for the chat dropdown."""
    user_datasets = []
    for ds_id, ds in datasets_store.items():
        if ds.get("user_id") == current_user.id:
            user_datasets.append({
                "dataset_id": ds_id,
                "filename": ds.get("filename", "Unknown"),
                "schema_summary": ds.get("schema_summary", ""),
            })
    return {"datasets": user_datasets}


@router.post("")
def send_chat_message(
    req: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process a chat message from the AI assistant.
    Uses LLM to generate a conversational response about data.
    Auto-detects user's datasets if none specified.
    """
    # Build context from chat history
    history = get_context(req.session_id, dataset_id=req.dataset_id or "", db=db)

    # ── Collect ALL user datasets for context ──────────────
    user_datasets = {}
    for ds_id, ds in datasets_store.items():
        if ds.get("user_id") == current_user.id:
            user_datasets[ds_id] = ds

    # If a specific dataset is selected, use its schema
    schema_context = ""
    dataset_info = ""
    active_dataset = None

    if req.dataset_id and req.dataset_id in user_datasets:
        active_dataset = user_datasets[req.dataset_id]
        schema_context = active_dataset.get("schema_summary", "")
        dataset_info = active_dataset.get("filename", "Unknown")
    elif user_datasets:
        # Auto-pick the first dataset if none selected
        first_id = list(user_datasets.keys())[0]
        active_dataset = user_datasets[first_id]
        schema_context = active_dataset.get("schema_summary", "")
        dataset_info = active_dataset.get("filename", "Unknown")

    # Build a summary of ALL user datasets
    all_datasets_summary = ""
    if user_datasets:
        lines = [f"You have {len(user_datasets)} dataset(s) uploaded:"]
        for ds_id, ds in user_datasets.items():
            lines.append(f"  • [{ds_id}] {ds.get('filename', 'Unknown')}")
        all_datasets_summary = "\n".join(lines)

    # Build conversation context
    history_text = ""
    if history:
        history_lines = []
        for h in history[-6:]:
            history_lines.append(f"User: {h['query']}")
            if h.get("explanation"):
                history_lines.append(f"Assistant: {h['explanation']}")
        history_text = "\n".join(history_lines)

    # Generate response using LLM
    if llm_engine.is_stub or not llm_engine.client:
        response_text = _generate_stub_response(
            req.message, schema_context, all_datasets_summary, dataset_info
        )
    else:
        try:
            prompt = _build_chat_prompt(
                req.message, schema_context, all_datasets_summary,
                dataset_info, history_text
            )
            response = llm_engine.client.models.generate_content(
                model=llm_engine.model_name,
                contents=prompt,
            )
            response_text = response.text.strip()
        except Exception as e:
            response_text = _generate_stub_response(
                req.message, schema_context, all_datasets_summary, dataset_info
            )

    # Save to conversation context
    add_to_context(
        session_id=req.session_id,
        query=req.message,
        code="",
        explanation=response_text,
        user_id=current_user.id,
        dataset_id=req.dataset_id or "",
        db=db,
    )

    return {
        "success": True,
        "response": response_text,
        "session_id": req.session_id,
    }


@router.get("/history/{session_id}")
def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get chat history for a session."""
    history = get_context(session_id, db=db)
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": "user",
                "content": h["query"],
                "timestamp": h.get("timestamp", 0),
            }
            for h in history
        ] + [
            {
                "role": "assistant",
                "content": h["explanation"],
                "timestamp": h.get("timestamp", 0),
            }
            for h in history
            if h.get("explanation")
        ],
    }


def _build_chat_prompt(
    message: str,
    schema: str,
    all_datasets: str,
    filename: str,
    history: str,
) -> str:
    """Build a rich prompt for the Gemini chat assistant."""
    prompt = (
        "You are an expert AI data analyst assistant embedded in a data analysis platform. "
        "You are friendly, smart, and proactive. Your job is to:\n"
        "1. Answer questions about the user's uploaded datasets\n"
        "2. Suggest specific, real-world queries tailored to their actual columns\n"
        "3. Explain data concepts in simple language\n"
        "4. Help users get the most out of their data\n\n"
        "RULES:\n"
        "- ALWAYS reference actual column names from the schema when suggesting queries\n"
        "- Give SPECIFIC query suggestions the user can copy-paste into the Query page\n"
        "- Vary your responses — never repeat the same suggestions twice\n"
        "- If the user asks for queries, give 3-5 diverse examples (trends, comparisons, outliers, totals)\n"
        "- Keep responses under 250 words\n"
        "- NEVER say 'upload a dataset' if they already have one — they DO\n"
        "- Use markdown formatting (bold, bullets) for readability\n\n"
    )

    if all_datasets:
        prompt += f"{all_datasets}\n\n"

    if schema:
        prompt += f"Currently active dataset: **{filename}**\nSchema:\n{schema}\n\n"

    if history:
        prompt += f"Conversation so far:\n{history}\n\n"

    prompt += f"User: {message}\n\nAssistant:"
    return prompt


def _generate_stub_response(
    message: str,
    schema: str,
    all_datasets: str,
    filename: str,
) -> str:
    """Smart keyword-based response when LLM is unavailable."""
    msg = message.lower()

    # ── Parse columns from schema ─────────────────────────
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []
    if schema:
        for line in schema.split("\n"):
            line = line.strip()
            if not line.startswith("- "):
                continue
            content = line[2:]
            paren_idx = content.find("(")
            if paren_idx == -1:
                continue
            col_name = content[:paren_idx].strip()
            rest = content[paren_idx + 1:]
            close = rest.find(")")
            if close == -1:
                continue
            col_type = rest[:close].strip().lower()
            if col_type == "numeric":
                numeric_cols.append(col_name)
            elif col_type == "categorical":
                categorical_cols.append(col_name)
            elif col_type == "datetime":
                datetime_cols.append(col_name)

    has_data = bool(schema)
    num = numeric_cols[0] if numeric_cols else "value"
    cat = categorical_cols[0] if categorical_cols else "category"
    num2 = numeric_cols[1] if len(numeric_cols) > 1 else num

    # ── Greetings ─────────────────────────────────────────
    if any(w in msg for w in ["hello", "hi", "hey", "good"]):
        if has_data:
            return (
                f"Hello! 👋 I can see you have **{filename}** loaded with "
                f"{len(numeric_cols)} numeric and {len(categorical_cols)} categorical columns.\n\n"
                f"Here are some things you can try on the **Query page**:\n"
                f"• \"Show average {num} by {cat}\"\n"
                f"• \"What is the total {num}?\"\n"
                f"• \"Are there any outliers in {num}?\"\n\n"
                f"What would you like to explore?"
            )
        return "Hello! 👋 I'm your AI data analyst. Upload a dataset first, then I can suggest tailored queries!"

    # ── Column/schema questions ───────────────────────────
    if any(w in msg for w in ["column", "schema", "field", "variable", "what data", "what's in"]):
        if has_data:
            col_list = ""
            if numeric_cols:
                col_list += f"**Numeric:** {', '.join(numeric_cols)}\n"
            if categorical_cols:
                col_list += f"**Categorical:** {', '.join(categorical_cols)}\n"
            if datetime_cols:
                col_list += f"**Date/Time:** {', '.join(datetime_cols)}\n"
            return (
                f"Your dataset **{filename}** has these columns:\n\n"
                f"{col_list}\n"
                f"Would you like me to suggest some queries based on these?"
            )
        return "Select a dataset first and I'll tell you all about its columns!"

    # ── Query suggestions ─────────────────────────────────
    if any(w in msg for w in ["suggest", "recommend", "idea", "query", "queries",
                               "what should", "what can", "example", "try",
                               "analysis", "analyze", "analyse", "give me"]):
        if has_data:
            suggestions = []
            if categorical_cols and numeric_cols:
                suggestions.append(f"• \"Show average {num} by {cat}\"")
                suggestions.append(f"• \"Compare total {num} across each {cat}\"")
                suggestions.append(f"• \"Which {cat} has the highest {num}?\"")
            if len(numeric_cols) >= 2:
                suggestions.append(f"• \"What is the correlation between {num} and {num2}?\"")
            if numeric_cols:
                suggestions.append(f"• \"Are there any outliers in {num}?\"")
                suggestions.append(f"• \"Show the distribution of {num}\"")
                suggestions.append(f"• \"What are the top 5 rows by {num}?\"")
            if datetime_cols:
                dt = datetime_cols[0]
                suggestions.append(f"• \"Show the trend of {num} over {dt}\"")
            if categorical_cols:
                suggestions.append(f"• \"How many records are there per {cat}?\"")

            # Pick 5 varied suggestions
            selected = suggestions[:5]
            return (
                f"Here are some queries you can try on the **Query page** with **{filename}**:\n\n"
                + "\n".join(selected) + "\n\n"
                "Just copy any of these and paste into the Query page! 🚀"
            )
        return (
            "I'd love to suggest queries! Upload a dataset first, and I'll give you "
            "specific suggestions based on your actual columns."
        )

    # ── Trend / time-series questions ─────────────────────
    if any(w in msg for w in ["trend", "time", "growth", "change", "over time"]):
        if has_data:
            if datetime_cols:
                dt = datetime_cols[0]
                return (
                    f"For trend analysis, try these on the **Query page**:\n\n"
                    f"• \"Show trend of {num} over {dt}\"\n"
                    f"• \"What is the monthly average {num}?\"\n"
                    f"• \"Is {num} increasing or decreasing over time?\"\n\n"
                    f"You can also use the **Forecast page** to predict future values!"
                )
            return (
                f"Your dataset doesn't have a date column, but you can still compare "
                f"{num} across {cat} on the **Query page**:\n\n"
                f"• \"Show {num} by {cat}\"\n"
                f"• \"Rank all {cat} by {num}\""
            )

    # ── Outlier / anomaly questions ───────────────────────
    if any(w in msg for w in ["outlier", "anomaly", "unusual", "extreme", "weird"]):
        if has_data:
            return (
                f"To find outliers in **{filename}**, try on the **Query page**:\n\n"
                f"• \"Are there any outliers in {num}?\"\n"
                f"• \"Detect anomalies in {num} by {cat}\"\n\n"
                f"The platform uses both **Z-score** (|z| > 3) and **IQR** methods automatically!"
            )

    # ── Comparison questions ──────────────────────────────
    if any(w in msg for w in ["compare", "versus", "vs", "difference", "which is"]):
        if has_data and categorical_cols and numeric_cols:
            return (
                f"For comparisons, try these on the **Query page**:\n\n"
                f"• \"Compare average {num} across {cat}\"\n"
                f"• \"Which {cat} has the highest {num}?\"\n"
                f"• \"Top 5 {cat} by total {num}\"\n\n"
                f"Or use the **Compare page** to compare two datasets side by side!"
            )

    # ── Forecast questions ────────────────────────────────
    if any(w in msg for w in ["predict", "forecast", "future", "next"]):
        if has_data:
            return (
                f"Head to the **Forecast page** and:\n\n"
                f"1. Select **{filename}**\n"
                f"2. Pick X-axis (e.g., {cat}) and Y-axis (e.g., {num})\n"
                f"3. Choose **Linear Regression** or **Moving Average**\n"
                f"4. Set how many periods to predict\n\n"
                f"It will show you historical data with future predictions!"
            )

    # ── How to / help ─────────────────────────────────────
    if any(w in msg for w in ["help", "how to", "how do", "what can", "guide"]):
        if has_data:
            return (
                f"Here's what you can do with **{filename}**:\n\n"
                f"📊 **Query page** — Ask questions in plain English\n"
                f"📈 **Forecast page** — Predict future trends\n"
                f"🔗 **Multi-Query page** — Join two datasets\n"
                f"🔔 **Alerts page** — Set alerts for threshold breaches\n"
                f"📋 **Data Profile page** — See full stats & correlations\n"
                f"📜 **History page** — Review past queries\n\n"
                f"Try asking me: \"suggest some queries\" for specific examples!"
            )
        return (
            "Here's how to get started:\n\n"
            "1. Go to the **Upload page** and upload a CSV or Excel file\n"
            "2. Then visit the **Query page** to ask questions\n"
            "3. Ask me for query suggestions anytime!\n\n"
            "The platform supports text and voice queries!"
        )

    # ── Thank you ─────────────────────────────────────────
    if any(w in msg for w in ["thank", "thanks", "great", "awesome", "perfect", "cool"]):
        return "You're welcome! 😊 Let me know if you need more analysis ideas or help with anything else!"

    # ── Default: provide dataset-aware response ───────────
    if has_data:
        return (
            f"Great question! With your **{filename}** dataset, you can explore a lot.\n\n"
            f"Here are some ideas for the **Query page**:\n"
            f"• \"Show average {num} by {cat}\"\n"
            f"• \"What are the top 10 rows by {num}?\"\n"
            f"• \"Count of records per {cat}\"\n\n"
            f"Or ask me to **\"suggest queries\"** for more tailored ideas!"
        )

    if all_datasets:
        return (
            f"I can see you have datasets uploaded! Select one in the dropdown above "
            f"and I can give you specific analysis suggestions.\n\n"
            f"{all_datasets}"
        )

    return (
        "I'd love to help! To get started:\n\n"
        "1. **Upload** a CSV/Excel file on the Upload page\n"
        "2. Come back here and I'll suggest tailored queries\n"
        "3. Or go to the **Query page** to ask questions directly\n\n"
        "What kind of data are you working with?"
    )
