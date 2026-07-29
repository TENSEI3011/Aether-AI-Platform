<style>
  h1, h2, h3 { page-break-after: avoid; }
  ul, li, blockquote { page-break-inside: avoid; }
  .viva-section { margin-bottom: 2rem; }
  p { margin-bottom: 1rem; }
</style>

# [GUIDE] Presentation Preparation Guide: Generative AI Analysis Platform

This guide covers the most likely questions your professor will ask during your viva/presentation, along with professional answers and deep-dive counter-answers.

---

## [1] Architecture & Tech Stack

**Q: Why did you choose FastAPI over Flask or Django?**
*   **Answer:** "I chose FastAPI primarily for its high performance and native support for asynchronous programming (async/await). It also provides automatic interactive API documentation (Swagger/OpenAPI), and uses Pydantic for strict data validation, which is crucial when handling complex query data and LLM outputs."
*   **Counter-Q: Isn't Django more 'complete'?**
    *   **Counter-A:** "Django is great for monoliths, but for an AI analytical tool, I wanted a lightweight, high-performance microservice-ready backend. FastAPI allows me to build the analytical pipeline without the overhead of Django's heavy ORM and template engine."

**Q: Why use React + Vite instead of a traditional HTML/JS approach?**
*   **Answer:** "React allows for a component-based architecture which makes the UI (like our dynamic charts and dashboards) easier to manage and reusable. Vite provides an extremely fast development environment with hot-module replacement and optimized builds for production."

---

## [2] LLM & Data Logic (The Core)

**Q: How does your 'LLM Engine' actually convert text to code?**
*   **Answer:** "Currently, the engine uses a keyword-matching and schema-aware semantic extraction logic. It scans the user's question for column names found in the dataset and keywords like 'average', 'top 10', or 'sum'. It then selects the appropriate Pandas template to generate a safe code execution string."
*   **Note:** If you're asked about the 'real' LLM, mention: "The architecture is designed to load a local transformer model like Microsoft Phi-3 Mini using the Hugging Face library. This would allow for more complex natural language understanding by processing the schema as a prompt context."

**Q: How do you handle 'LLM Hallucinations' (the AI generating wrong code)?**
*   **Answer:** "We have a strictly defined **Validation Layer**. Before any code is executed, it passes through `query_validator.py`. This checks the Python syntax using `ast.parse()` and verifies that the generated code only calls allowed Pandas methods and uses valid column names from the current dataset."

---

## [3] Security & Safety

**Q: Running AI-generated code on a server is dangerous. How is your app secured?**
*   **Answer:** "The execution is sandboxed using three layers of security:
    1. **Pre-Execution Check:** Blocks dangerous keywords like `import`, `os`, `eval`, or `DROP TABLE`.
    2. **Restricted Namespace:** The `exec()` function runs in a local dictionary containing *only* the DataFrame (`df`) and `pd`. It has no access to global variables, file systems, or built-in Python functions.
    3. **Read-Only Enforcement:** The code is executed on a deep copy of the data, ensuring the original dataset on the server is never modified or deleted."

---

## [4] Data Processing & Visualization

**Q: How does the system automatically decide which chart to show (Bar vs. Pie vs. Line)?**
*   **Answer:** "The `viz_selector.py` service looks at the 'shape' of the data result.
    - If there is a Date column, it defaults to a **Line Chart**.
    - If it's categorical with few values (like 5 regions), it picks a **Pie Chart**.
    - For comparing multiple numeric values or many categories, it picks a **Bar Chart**.
    - If the data is too complex, it defaults to a **Data Table**."

**Q: What happens if the uploaded file is dirty (missing values/duplicates)?**
*   **Answer:** "On upload, the `data_validator.py` service runs a full profile. It detects missing values and duplicates and alerts the user in the UI. For query execution, we handle this by using Pandas' robust aggregation methods which ignore nulls by default, or the user can specifically ask the system to 'show missing values'."

---

## [5] Voice Input & Transcription

**Q: How did you implement voice commands without a heavy cloud dependency?**
*   **Answer:** "The frontend uses the **Web Speech API** first, which is built into modern browsers. It's fast and processes transcription on the client's machine. As a fallback, we have a backend STT service using the **SpeechRecognition** library and the Google Web Speech API for browsers that don't support the native API."

---

## [6] Future Scope & Scalability

**Q: How would you scale this to handle 1GB+ files?**
*   **Answer:** "Currently, the app loads data into memory. For large-scale datasets, I would:
    1. Replace Pandas with **Dask** or **Polars** for parallelized computation.
    2. Move the data from local files to a dedicated data warehouse like **PostgreSQL** or **ClickHouse**.
    3. Implement block-level processing or pagination in the execution service."

**Q: Can this handle multiple users at once?**
*   **Answer:** "Yes. The backend architecture is stateless. Each request carries its own JWT for authentication, and the query execution happens in isolated temporary namespaces. For high traffic, we could deploy multiple instances of the backend behind a load balancer (like Nginx) using the provided Docker configuration."

---

## [7] Database & Performance Optimization

**Q: How does your database schema handle large query logs over time?**
*   **Answer:** "The `QueryLog` table is designed with an index on `user_id` and `created_at`. This ensures that even as thousands of queries are logged, fetching a specific user's history remains an O(log N) operation rather than a slow full-table scan."

**Q: Why use SQLite instead of a dedicated SQL server?**
*   **Answer:** "For this phase of the project, SQLite is ideal because it's serverless and zero-configuration. It allows the entire platform to be portable (one file). However, because we use **SQLAlchemy**, the code is 'database agnostic'—we could switch to PostgreSQL by simply changing one line in the `.env` file."

---

## [8] UI/UX & Frontend Logic

**Q: How do you handle chart state during window resizing?**
*   **Answer:** "The `ChartRenderer` uses **ResponsiveContainer** from Recharts. This ensures the SVG charts dynamically recalculate their width and height based on the parent grid cell size, maintaining a premium look on both desktop and tablet screens."

**Q: Why store the Dashboard panels in `sessionStorage`?**
*   **Answer:** "We chose `sessionStorage` to give users a temporary workspace. It allows them to pin results during an active analysis session without cluttering the database. If they wanted permanent dashboards, we would implement a `Dashboard` model in the backend, but `sessionStorage` reduces server load and increases privacy."

---

## [9] Advanced Implementation Details

**Q: How do you handle cases where the LLM produces valid Python but the data doesn't fit the chart?**
*   **Answer:** "This is handled in the `viz_selector.py`. Before rendering, it checks the datatype of the columns. If the LLM generates a result that isn't compatible with a 'Line' chart (e.g., no numeric values), the service automatically catches the type-mismatch and falls back to a **Data Table** to ensure the user always sees their data."

**Q: How does the `/transcribe` endpoint handle different audio formats?**
*   **Answer:** "The backend uses **pydub** as a middleware. Since different browsers record in different formats (Chrome uses WebM, Safari uses AAC), the server automatically detects the format and converts it to a standard PCM WAV before sending it to the transcription engine."

---

## [10] Deployment & Infrastructure

**Q: What is the benefit of using Docker for this project?**
*   **Answer:** "Docker handles the 'It works on my machine' problem. It packages the exact Python environment (backend) and Node environment (frontend) together. This means our PDF generation, AI libraries, and server dependencies will work exactly the same way on your machine as they do on mine."

**Q: How do the frontend and backend communicate in the Docker container?**
*   **Answer:** "In the `docker-compose.yml`, we define a internal network bridge. The frontend is configured with the `VITE_API_URL` pointing to the backend service. This allows for a clean separation of concerns: the backend focuses on data crunching, and the frontend on user interaction."

---

## [TIPS] Top Tips for the Presentation:

1.  **Be Honest about Stubs:** If they grill you on the LLM model path, say: "The integration logic is complete, but for this demo environment, we are using a keyword-based rule engine to save on GPU/RAM resources."
2.  **Show the Validator:** Professors love security. If they ask about code safety, show them `query_validator.py` and explain the `ast` parsing.
3.  **The "Key" to Success:** If they ask why the charts look so smooth when changing queries, mention the `queryKey` state in React that forces a clean re-mount of the chart component to prevent data overlapping.
