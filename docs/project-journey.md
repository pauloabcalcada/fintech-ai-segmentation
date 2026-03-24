## Fintech AI Segmentation – Project Journey

This file is a concise, storytelling log of how we are building the Fintech AI Segmentation project. It is written as if explaining the project to a curious data/ML practitioner or hiring manager and can be reused directly for LinkedIn posts or portfolio write-ups.

SynaptiqPay is a Brazilian fintech with 8,000 digital wallet customers, but their commercial manager still treats everyone the same — identical offers, communication, and retention tactics. This one-size-fits-all approach wastes time and money because some customers are highly engaged and profitable, while others are dormant or close to churning. Our goal with this project is to replace weekly spreadsheet firefighting with a segmentation- and AI-driven workflow that surfaces who the customers are, how they behave, how valuable they are, who is at risk, and which concrete action the manager should take next.

---

### 2026-03-18 — Kicking off the project journey log

Today we created a dedicated `project-journey` log to track the main steps in building the Fintech AI Segmentation project. Instead of burying decisions inside notebooks or long chats, this file will capture the narrative: problem framing, modeling choices, data design, engineering decisions, and what we learned along the way. The goal is to keep each update short and “LinkedIn-ready”, so that any entry can be turned into a post with minimal editing. This also forces us to explain our work in plain language, as if we were teaching a colleague who understands data but has not seen the code.

### 2026-03-18 — Designing the first ELT step with synthetic data

Today we took the first practical step of the ELT pipeline by designing synthetic “faker” datasets that mirror the four planted behavioral segments (`high_value_active`, `mid_value_regular`, `low_value_dormant`, and `at_risk_churner`) and the business questions we care about. Instead of randomly generating noise, we shaped fields, distributions, and event patterns so that high-balance, very engaged customers look meaningfully different from low-balance, dormant, and at-risk churners, making it possible to recover these ground-truth segments later through EDA, RFM, clustering, and churn modeling. We are saving each dataset as a CSV file so it can act as the extraction layer of a realistic ELT workflow, decoupled from any one warehouse or BI tool. The next step will be setting up Supabase as our analytical database so we can load these CSVs, enforce a clean base schema, and run the segmentation and churn analysis with SQL and Python on top of a more production-like environment.

### 2026-03-20 — Importing `transactions_raw` with size-aware chunking

Today we moved from the “synthetic data” stage to the database loading stage by creating the raw tables in Supabase and then focusing on the hardest dataset in `data/raw`: `transactions_raw.csv`. We first explored loading everything through Supabase MCP (create tables via `apply_migration`, then insert data via SQL), but ran into practical obstacles once the payload got large—batching required generating big `INSERT` statements, and even after iterating on batch sizes the tool-side transmission/payload caps made it unreliable to send batches at scale. We also attempted the “Option A” approach (`psql` + `\copy`) as a cleaner bulk-load alternative, but our environment hit a DNS issue resolving the Supabase DB host, so that path wasn’t usable immediately. To keep progress unblocked while staying within Supabase’s dashboard constraints, we switched strategies: we sliced `transactions_raw.csv` into three CSV files (each under ~100MB) and verified row counts/headers for each slice. This choice turned the problem from “how do we push 1.8M+ rows through a chat-style SQL channel” into “how do we use a purpose-built import UI with predictable chunk sizes,” which is exactly what the rest of the ELT pipeline needs.

After creating the four raw tables (`customers_raw`, `products_raw`, `transactions_raw`, and `customer_products_raw`) and loading the CSV data, we validated that the database schema matches our intended data model (primary keys, foreign keys, and the expected column types). The screenshot below is our reference point for what “done” looks like in Supabase’s table view: it confirms that the raw ingestion layer is structurally correct and ready for the next SQL-based segmentation steps.

![Raw schema after table creation and CSV loads](./images/Tables_Loaded.png)

### 2026-03-23 — Improving synthetic data realism and freezing EDA outputs

Today we focused on making the synthetic customer base more believable before moving into the next analysis cycle. We updated generation assumptions to better reflect Brazilian market concentration by state (with stronger weight in the Southeast), improved identity quality by generating unique customer names and name-linked emails, and intentionally resized the dataset while preserving the planted segment mix. This matters because many downstream business questions (especially channel and geography decisions) are only as credible as the realism of the raw inputs.

In parallel, we strengthened the EDA narrative so it explicitly connects observed plots to generator assumptions. We added diagnostics for skewness/kurtosis, state distribution caveats, segment and channel proportion checks versus intended design, and segment-level acquisition-cost comparisons. The key lesson is that synthetic projects become much more interview- and production-ready when assumptions are transparent and testable in the notebook, instead of being hidden in generation code.

Finally, we introduced a “freeze” workflow for reproducibility by creating a dated snapshot of the EDA notebook and exporting it to HTML. This gives us a stable historical report we can reference after regenerating/loading new data versions, without losing today’s baseline results or narrative context.
