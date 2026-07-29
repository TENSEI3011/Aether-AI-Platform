# 🎤 Panel Presentation Script
> **Your 3 Slides:** Architecture → Data Sources → Platform Modules
> **Estimated Time:** 5–7 minutes total
> **Tip:** Speak slowly, point at the slide, and pause after key points.

---

## SLIDE 1 — Proposed System: Architecture
*⏱ ~2 minutes*

---

**Start by saying:**

> "Now let me walk you through how our platform is structured. We have a **three-layer architecture** — Frontend, Backend, and Data Layer."

**Point to the Frontend column:**

> "On the **Frontend**, we used **React with Vite** as our single-page application. Vite gives us fast build times compared to traditional tools like Create React App. This is where all the user-facing pages live — the Upload page where users drag-and-drop their CSV files, the Query page where they type natural language questions, the Forecast page for predictions, the Alerts page for setting up automated notifications, and the History page where they can see and re-run all their past queries."

**Point to the Backend column:**

> "The **Backend** is built with **FastAPI in Python**. FastAPI was chosen because it's one of the fastest Python web frameworks and has built-in support for automatic API documentation. The core part here is our **Natural Language Query Pipeline** — this is where the user's plain English question gets converted into actual Pandas code using Google's **Gemini AI model**. We also have our **authentication system** using JWT tokens and bcrypt for password hashing, **anomaly detection** using Z-score and IQR methods, and a **forecasting service** using linear regression."

**Point to the Data Layer column:**

> "For the **Data Layer**, we use **PostgreSQL** in production and **SQLite** for local development. We designed **8 database tables** using SQLAlchemy ORM — for users, datasets, query logs, conversation history, saved queries, alerts, and notifications. The uploaded datasets are stored on the filesystem, and their metadata is tracked in the database so they survive server restarts."

**Pause, then wrap up:**

> "So in short — React handles the interface, FastAPI handles the logic and AI, and PostgreSQL stores everything persistently."

---

## SLIDE 2 — Data Sources & Evaluation Dataset
*⏱ ~1.5 minutes*

---

**Start by saying:**

> "To make sure our platform works with real-world data, we tested it with **three different types of datasets**."

**Point to the dataset list:**

> "First, **Healthcare data** — hospital records with patient diagnoses, treatment codes, and admission records. This was important because medical data has very specific terminology, and we wanted to test if our AI can understand queries like *'show average treatment cost by department'* even with domain-specific column names."

> "Second, **Retail data** — store transactions with sales volumes, product categories, and regional performance. This helped us test aggregation queries like *'total sales by region'* and trend detection like *'show monthly revenue trend'*."

> "Third, **Finance data** — revenue figures, profit margins, and time-series stock prices. This was specifically chosen to test our **forecasting module** and **anomaly detection**, because financial data naturally has outliers and trends."

**Point to the pie chart:**

> "For evaluation, we created a **test set of 80 queries** divided into three difficulty levels. **37% were simple** — basic filters and aggregations like *'show total sales'*. **38% were medium complexity** — involving group-by operations and multi-condition filters like *'show average price by category where stock is greater than 100'*. And **25% were complex queries** — involving time-series analysis, nested operations, and cross-column comparisons."

> "This mix was deliberate — it helped us measure how well our AI handles easy questions versus difficult analytical ones."

---

## SLIDE 3 — Proposed System: Platform Modules
*⏱ ~2.5 minutes*

---

**Start by saying:**

> "Our platform has **10 core modules**. Let me quickly explain what each one does."

**Go through them — keep each one to 2-3 sentences:**

> "**Module 1 — Data Ingestion and Upload.** Users upload CSV or Excel files through a drag-and-drop interface. The file goes through format validation, the system automatically detects column names and data types, and then registers it in the database."

> "**Module 2 — Automated Data Profiling.** Once a dataset is uploaded, the system automatically generates a profile — it calculates mean, median, standard deviation for every numeric column, finds missing values, counts duplicates, and generates a correlation matrix. This gives users an instant understanding of their data quality."

> "**Module 3 — Interactive Data Cleaning.** Users can type cleaning instructions in plain English like *'remove duplicate rows'* or *'fill missing values with the mean'*. The AI generates the appropriate Pandas code, validates it, and applies it to the dataset."

> "**Module 4 — Natural Language Query.** This is the **heart of our platform**. The user types a question like *'show average sales by region'*. It goes to Google Gemini, which generates Pandas code. That code passes through our **4-layer security pipeline** — regex filter, AST walker, schema validator, and sandboxed execution. The result is then auto-visualized as the most appropriate chart — bar, line, pie, scatter, histogram, or heatmap."

**Slow down here — this is the most important module:**

> "**Module 5 — Multi-Dataset Querying.** Users can run the same query across multiple uploaded datasets and see results side-by-side. This is useful for comparing, say, sales data from different years."

> "**Module 6 — Forecasting.** The system uses **linear regression** to predict future values. It shows historical data plus the forecast on a combined chart, with a confidence score based on R-squared value and a trend indicator — rising, falling, or stable."

> "**Module 7 — What-If Scenario Analysis.** Users can ask hypothetical questions like *'What if prices drop by 15%?'*. The AI generates transformation code, applies it to a copy of the data, and shows side-by-side comparison charts — original versus modified."

> "**Module 8 — Anomaly Detection and Alerts.** We use two statistical methods — **Z-score** which flags values more than 3 standard deviations from the mean, and **IQR** which uses the interquartile range. Users can also set custom alert rules like *'notify me when revenue drops below 10,000'*, and the system sends email notifications."

> "**Module 9 — Voice Interface.** Users can speak their queries instead of typing. The frontend uses the browser's **Web Speech API** for instant transcription. If that's not available, it falls back to our backend speech-to-text service. We also have text-to-speech — the AI narration can be read aloud using **Google TTS**."

> "**Module 10 — Query History and Chat.** Every query is logged with its timestamp, generated code, and result. Users can go back and re-run any past query. We also have a conversational chat sidebar where users can ask follow-up questions — the system remembers the last 6 turns of conversation."

**Wrap up the slide:**

> "So these 10 modules together make our platform a complete data analysis solution — from upload to insight to prediction, all powered by natural language."

---

## 🛡️ Bonus: If Panel Asks About Edge Cases

Keep these 2 ready:

**Q: "What happens if someone tries to inject malicious code?"**
> "We have 4 layers of protection. First, a regex filter blocks dangerous keywords like import, exec, and eval. Second, we walk the Abstract Syntax Tree to block dunder attribute access like `__class__.__mro__` which is a known sandbox escape technique. Third, the code runs in a restricted namespace where only the dataframe and pandas are available — no built-in functions, no file access. And fourth, there's a 10-second timeout to prevent infinite loops."

**Q: "What if the Gemini API is down or quota is exceeded?"**
> "We built an intelligent keyword-based fallback engine. If the API fails, the system uses keyword matching — it detects words like 'average', 'total', 'group by' in the query and maps them to the correct Pandas operations. It also reads the actual column names from the dataset schema to generate valid code. So the core functionality works even without the API."

---

## 💡 General Tips

1. **Don't memorize word-for-word** — understand the flow and speak naturally
2. **Point at the slide** while explaining each section
3. **Pause after key terms** like "4-layer security", "AST walker", "sandboxed execution"
4. **If you don't know an answer**, say: *"That's a good question. From my understanding of the module..."*
5. **Keep your voice confident** — you built this, you know this
