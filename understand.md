Guest: "connect me to support"
    → wants_human_support() = True
    → place_voice_call(reason, property_id)
         → Twilio rings +919892017303
         → On answer, fetches handoff_call_url → handoff_twiml()
         → You hear: "Guest at property 9 3 0... issue is..."
    → handoff_message() → shown in chat
    → log_transfer() in session_service (MySQL)

# StayOps v2 — Interview-ready [understand.md](http://understand.md)

Yeh file **stay-assistant-v2** ko Hinglish mein explain karti hai — project kya hai, har folder/file kya karti hai, Guest vs Ops flow, aur interview talking points.

Secrets (API keys, DB password, Twilio token) yahan nahi hain. Unke naam `.env.example` mein dekho, values sirf local `.env` mein rakho.

---

## Project kya hai

**StayOps v2** ek local vacation-rental (stay) assistant hai.

Do users, do jobs:

1. **Guest** — property ke notes se sawaal (wifi, parking, check-in). Answers **RAG** se aate hain, sirf us guest ke `property_id` ke liye.
2. **Ops / staff** — Airbnb / HomeAway `bookings_info` table par SQL agent. Read + controlled write (WHERE mandatory on UPDATE/DELETE).

Pehle wala app `hotel-management-app` alag copy hai. Naya kaam **yahan** hai. Stripe checkout / SMTP credential email **remove** ho chuke hain. Login **local MySQL** `registered_users` se hota hai.

Stack short mein:

- UI: **Streamlit** (`streamlit_app.py` + `app_pages/`)
- Auth API: **FastAPI** (`api/main.py`)
- Guest brain: **LangGraph** RAG (`agents/guest_graph.py`)
- Ops brain: **LangGraph** SQL (`agents/ops_graph.py`)
- Vectors: **Chroma** (`chroma_db/`)
- LLM: **Gemini** (`services/llm.py`)
- Human handoff: **Twilio** voice call (`services/executive_service.py`) — `tel:` / Outlook nahi

---



## Folder structure

```
stay-assistant-v2/
  streamlit_app.py      # app entry, navigation, session_state
  Database.py           # SQLAlchemy + load_dotenv for DB_*
  .env                  # secrets (local only)
  requirements.txt
  README.md
  .env / .env.example
  .streamlit/           # theme
  app_pages/            # Home, Guest, Ops UI
  agents/               # LangGraph graphs
  api/                  # FastAPI login
  notebooks/            # Chunk_Create.ipynb (Jupyter chunk demo)
  rag/                  # chunking + retriever
  services/             # auth, sessions, LLM, Twilio, KPIs
  scripts/              # seed users, rebuild Chroma
  data/                 # Excel / CSV source for properties
  chroma_db/            # persistent vector index
```

`hotel-management-app` is project ke bahar hai — usko touch mat karo.

---



## Important files — role



### Entry + config


| File                     | Role                                                                                                                                         |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `streamlit_app.py`       | `st.navigation` se Home / Guest / Ops. Guest+Ops login, chat history, handoff flags `session_state` mein.                                    |
| `Database.py` / each module | Jo file ko env chahiye, wahan `load_dotenv` + `os.getenv` — alag `config.py` nahi. |
| `rag/embeddings.py`          | Gemini embedding (`gemini-embedding-001` by default). |
| `.env`                   | Real keys (gitignored). Interview mein sirf **names** bolo: `DB_PASSWORD`, `GEMINI_API_KEY`, `TWILIO_`*, `EXECUTIVE_PHONE`.                  |
| `.env.example`           | Template without secrets.                                                                                                                    |
| `.streamlit/config.toml` | Light theme, green primary, minimal toolbar.                                                                                                 |
| `requirements.txt`       | Streamlit, FastAPI, LangGraph, Chroma, Gemini, SQLAlchemy, bcrypt, httpx. Stripe **nahi**.                                                   |




### Streamlit pages (`app_pages/`)


| File       | Role                                                                                                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `home.py`  | Landing. Guest vs Team cards — plain end-user copy.                                                                                                                                   |
| `guest.py` | Email+password only. `property_id` DB se aata hai. Soft UI. Support call card.                                                                                                        |
| `ops.py`   | Staff login. KPI row. Chat `ask_ops()` — UI mein SQL / jargon nahi, sirf plain answers.                                                                                               |




### LangGraph agents (`agents/`)

**Guest (**`guest_graph.py`**)** — property-scoped Q&A + handoff.

Graph: `rewrite` → `retrieve` → `generate`.

- **rewrite:** question ko do retrieval queries mein (standalone + expanded).
- **retrieve:** `rag.retriever.retrieve_context` — original + rewritten queries, distance filter.
- **generate:** Gemini + tool `transfer_to_customer_service`. Support maange to Twilio `place_voice_call`, DB transfer log, optional Telegram.

Shortcut: phrase match `wants_human_support()` pe graph skip karke seedha handoff.

**Ops (**`ops_graph.py`**)** — text-to-SQL on `bookings_info` only.

Graph: `plan_sql` → `execute_sql` → `explain`.

Safety (interview favourite):

- Sirf `SELECT/INSERT/UPDATE/DELETE`
- No DDL (`DROP/ALTER/...`)
- Table must be `bookings_info`
- UPDATE/DELETE ke liye `WHERE` zaroori
- Ek statement, no `;` stacking
- Result plain-language answer mein — koi audit log table nahi



### RAG (`rag/`)


| File                        | Role                                                                                                                                                                                               |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `chunking.py`               | Excel row se `summary` **code se rebuild** (empty/NaN drop, HTML strip). Chunks **section** se: identity, location, access, amenities, pricing — blind 100-word cut nahi. Profile chunk + overlap. |
| `retriever.py`              | Persistent Chroma. Collection = `collection_{property_id}`. Multi-query, weak hits drop (`max_distance`), compact context.                                                                         |
| `scripts/rebuild_chroma.py` | `data/final_data.xlsx` padho → chunk → Chroma write. CLI indexer.                                                                                                                                    |
| `notebooks/Chunk_Create.ipynb` | Same chunk pipeline step-by-step Jupyter mein — interview demo ke liye.                                                                                                                          |




### FastAPI + Database


| File                       | Role                                                                                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api/main.py`              | `POST /api/v1/auth/login` (email+password). `GET /health`. Stripe/checkout routes nahi.                                                                                               |
| `services/auth_service.py` | bcrypt verify. `status == active` required. `upsert_user` seed script ke liye.                                                                                                        |
| `Database.py`              | Engine + **sirf 4 tables**: `registered_users`, `Session_table_2`, `Chat_table`, `chat_transfer_table`. Import pe `init_db()`. |


Property access **payment se nahi** — `registered_users.property_id` se.

### Services (active)


| File                   | Role                                                                                                                                                                                |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `executive_service.py` | Twilio REST se **real PSTN call** to `EXECUTIVE_PHONE`. Trial: verified To-number + `Url` (inline TwiML nahi). `tel:` empty rakha taaki Outlook na khule. Optional Telegram notify. |
| `session_service.py`   | Chat session start, messages MySQL mein, handoff `ChatTransfer`.                                                                                                                    |
| `llm.py`               | Gemini via official client (`x-goog-api-key`) wrapped in LangChain chat model.                                                                                                      |
| `ops_metrics.py`       | Ops page KPIs: bookings count, commission sum, platforms, guests.                                                                                                                   |


Deleted leftovers (ab import nahi hote): `payment_service.py`, `email_service.py`.

### Scripts + data


| File                                        | Role                                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------------------- |
| `scripts/seed_users.py`                     | Demo guest + staff MySQL mein. Guest ko `DEMO_GUEST_PROPERTY_ID` (default `910`) map. |
| `scripts/rebuild_chroma.py`                 | Vector index rebuild.                                                                 |
| `data/final_data.xlsx`                      | Chunking source.                                                                      |
| `data/units_info.csv`, `data/bookings.json` | Raw/export copies; live RAG path Excel + Chroma hai.                                  |
| `chroma_db/UNITS_INFO_CHUNCK/`              | Persistent embeddings. Guest login pe collection check yahi se.                       |


---



## Guest vs Ops flow

```
                    ┌─────────────┐
                    │  Home page  │
                    └──────┬──────┘
              ┌────────────┴────────────┐
              ▼                         ▼
        Guest portal              Operations
              │                         │
     FastAPI login               FastAPI login
     (guest/staff +              (staff only)
      property_id)
              │                         │
     LangGraph guest             LangGraph ops
     rewrite→retrieve            plan→execute→explain
     →generate                   bookings_info SQL
              │                         │
     Chroma (that                MySQL bookings_info
     property only)
              │
     Support phrase / tool
              ▼
     Twilio rings executive
     (+ optional Telegram)
```

**Guest isolation:** har account ka `property_id`. Retrieval us collection se. Dusri listing ke facts mix nahi hone chahiye.

**Ops guardrails:** LLM SQL generate karta hai, Python validate karta hai, phir execute. UI ko sirf plain-language answer milta hai (SQL dikhaya nahi jata).

---

## MySQL mein guest users kaise add kare

Guest UI mein sirf **email + password**. `property_id` table `registered_users` mein hota hai.

**Best way:** `scripts/seed_users.py` mein `GUESTS` list edit karo, phir:

```powershell
python scripts/seed_users.py
```

Script bcrypt hash banata hai aur `user_role='guest'` + `property_id` set karta hai.

**Manual (Workbench):** plain password mat store karo. Pehle hash lo:

```powershell
python -c "from Database import hash_password; print(hash_password('YourPasswordHere'))"
```

Phir:

```sql
INSERT INTO registered_users
  (user_id, email, password_hash, full_name, user_role, property_id, status, created_at)
VALUES
  (UUID(), 'newguest@example.com', '<bcrypt_hash>', 'New Guest', 'guest', '910', 'active', NOW());
```

`property_id` wahi hona chahiye jiska Chroma collection pehle se bana ho (`collection_910`, etc.).

---

## Kaise run kare (short)

Project root: `stay-assistant-v2`. Venv: repo ke `MYVENV01` (ya jo tum use karte ho).

1. `.env` bharo (`DB_PASSWORD`, `GEMINI_API_KEY`; Twilio if you want a real ring).
2. MySQL DB `Conversations` (ya `DB_NAME`) up.
3. Optional: `python scripts/rebuild_chroma.py` then `python scripts/seed_users.py`.
4. Terminal 1: `python -m uvicorn api.main:app --reload --port 8000`
5. Terminal 2: `python -m streamlit run streamlit_app.py`

Demo emails README mein hain. Passwords seed script / README se lo — unhe yahan repeat nahi kiya.

Twilio trial: `EXECUTIVE_PHONE` verify karo; SID, token, From number `.env` mein. Guest chat: *I want to talk to customer support*.

---



## Interview talking points (5–8)

1. **Do-agent product:** Guest = property RAG; Ops = guarded SQL on bookings. Same Streamlit shell, alag graphs.
2. **Auth without Stripe:** FastAPI + bcrypt. Property mapping DB column se, checkout se nahi.
3. **RAG quality:** Summary code se rebuild, HTML/NaN clean, **section chunks + overlap + profile chunk**, property-id collections.
4. **Retrieval:** Query rewrite (2 variants) + original, distance cutoff, compact context — hallucination reduce.
5. **SQL safety:** Schema-constrained planner, forbidden DDL, `bookings_info` only, WHERE on writes.
6. **Handoff reality:** Windows `tel:` Outlook kholta hai, ring nahi. Twilio trial + verified number + webhook `Url` (trial inline TwiML reject karta hai).
7. **Session memory:** Guest/Ops chats MySQL session tables; transfer alag row.
8. **Local ops story:** `.env` secrets, seed + chroma rebuild scripts, v1 (`hotel-management-app`) freeze, v2 iterate.

---



## MySQL tables (app uses only these)

| Table | Purpose |
| --- | --- |
| `registered_users` | Login (email, bcrypt password, role, property_id) |
| `Session_table_2` | Chat session per user visit |
| `Chat_table` | Messages for a session |
| `chat_transfer_table` | Support handoff when guest asks for a human |

Purani tables (`sql_audit_log`, `credential_delivery_log`) code se hata diye. MySQL mein ab bhi ho to optional drop:

```sql
DROP TABLE IF EXISTS sql_audit_log;
DROP TABLE IF EXISTS credential_delivery_log;
```

Ops agent `bookings_info` read karta hai — woh alag business table hai, ORM model nahi.

## Jo delete / ignore kar sakte ho (mental model)

- Stripe / SMTP / audit log modules — gone.
- Chunk indexer: `rag/chunking.py` + `scripts/rebuild_chroma.py`; interview walkthrough: `notebooks/chunk_creation.ipynb`.
- `__pycache__` — generated, ignore.
- `hotel-management-app` — original, v2 se alag.

