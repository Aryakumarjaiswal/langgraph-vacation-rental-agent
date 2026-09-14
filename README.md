# 🏡 StayOps — AI Vacation Rental Assistant

An end-to-end **AI-powered vacation rental operations platform** that helps **guests** get instant answers about their stay and empowers **staff** to query booking data in plain language. Built with **Google Gemini**, **LangGraph**, **RAG (ChromaDB)**, and a **Twilio voice handoff** for human escalation.

The app ships with a **Streamlit** multi-page UI, a **FastAPI** auth layer, and a lean **MySQL** schema focused on users, chat sessions, and support transfers.


---



## 🛠️ Tech Stack

- 🧠 **Agent Orchestration:** LangGraph (dual state machines — Guest RAG + Ops SQL)
- ⚡ **LLM Engine:** Google Gemini (`langchain-google-genai` + official `google.genai` client)
- 🔍 **Retrieval:** ChromaDB + Hugging Face `BAAI/bge-small-en-v1.5` embeddings
- 📄 **RAG Pipeline:** Section-based chunking, HTML stripping, property-scoped collections
- 🖥️ **User Interface:** Streamlit (Guest portal + Team workspace)
- 🚀 **Backend API:** FastAPI (login, health, Twilio TwiML webhook)
- 🗄️ **Database:** MySQL + SQLAlchemy (4 core tables)
- 📞 **Voice Handoff:** Twilio Programmable Voice (contextual `<Say>` on answer)
- 🔐 **Auth:** bcrypt password hashing, role-based access (`guest` / `staff`)
- 🐳 **Containerization:** Docker (separate API + Streamlit images)
- ☸️ **Orchestration:** Kubernetes (Deployments, Services, PVC, HPA)
- 🔄 **CI/CD:** GitHub Actions (test, build, push to GHCR)

---



## 🌟 Key Engineering Highlights

- 🔄 **Dual-Agent Design:** Separate LangGraph workflows for **guest property Q&A** (RAG) and **staff operations** (guarded text-to-SQL) — same UI shell, isolated concerns.
- 🏠 **Property-Scoped RAG:** Each listing gets its own Chroma collection (`collection_{property_id}`). Guests only retrieve docs tied to their account — no cross-property leakage.
- 🔎 **Query Rewrite + Multi-Retrieve:** Guest agent expands the user question into retrieval variants, filters weak hits by cosine distance, and grounds Gemini answers in retrieved context.
- 🛡️ **Ops SQL Guardrails:** Schema-constrained planner, DDL blocked, single-statement enforcement, `bookings_info` only, mandatory `WHERE` on `UPDATE`/`DELETE`.
- 📞 **Contextual Voice Escalation:** When a guest asks for support, Twilio calls the on-call executive and speaks **property ID (digit-spaced) + reported issue** via dynamic TwiML from FastAPI.
- 💬 **Session Persistence:** Chat history and support transfers stored in MySQL (`Session_table_2`, `Chat_table`, `chat_transfer_table`).
- 🎯 **End-User UX:** Plain-language UI copy — no SQL/RAG jargon exposed to guests or staff.

---



## 📂 Repository Structure

```text
vacation-property/
├── .streamlit/
│   └── config.toml              # Streamlit theme
├── api/
│   └── main.py                  # FastAPI — auth, health, /twilio/handoff TwiML
├── agents/
│   ├── guest_graph.py           # LangGraph: rewrite → retrieve → generate + handoff
│   └── ops_graph.py             # LangGraph: plan_sql → execute → explain
├── app_pages/
│   ├── home.py                  # Landing — Guest vs Team
│   ├── guest.py                 # Guest sign-in + chat
│   └── ops.py                   # Staff sign-in + ops chat + KPIs
├── rag/
│   ├── chunking.py              # Section chunks, summary rebuild, HTML clean
│   ├── embeddings.py            # Sentence Transformer embedding function
│   └── retriever.py             # Property-scoped Chroma retrieval
├── services/
│   ├── auth_service.py          # bcrypt authenticate + upsert
│   ├── executive_service.py     # Twilio outbound call + TwiML builder
│   ├── llm.py                   # Gemini chat client
│   ├── ops_metrics.py           # Staff dashboard KPIs
│   └── session_service.py       # MySQL session + chat + transfer logging
├── scripts/
│   ├── rebuild_chroma.py        # Index final_data.xlsx → Chroma
│   └── seed_users.py            # Seed guest + staff accounts
├── data/
│   ├── final_data.xlsx          # Property source data (for RAG indexing)
│   ├── units_info.csv           # Reference export
│   └── bookings.json            # Sample booking data
├── chroma_db/                   # Persistent vector store (generated)
├── chunck_creation.ipynb        # Jupyter walkthrough for chunking pipeline
├── docker/
│   ├── Dockerfile.api           # FastAPI container
│   └── Dockerfile.streamlit     # Streamlit container (+ pre-cached embeddings)
├── k8s/
│   ├── configmap.yaml           # Non-secret env vars
│   ├── secret.example.yaml      # Template for secrets (copy → secret.yaml)
│   ├── api-deployment.yaml      # FastAPI Deployment
│   ├── api-service.yaml         # ClusterIP for API
│   ├── streamlit-deployment.yaml
│   ├── streamlit-service.yaml   # LoadBalancer for UI
│   ├── pvc.yaml                 # Chroma persistent volume
│   └── hpa.yaml                 # API autoscaler (2–6 pods, CPU 70%)
├── .github/workflows/
│   └── cicd.yml                 # Test + build + push images
├── Database.py                  # SQLAlchemy models (4 tables)
├── streamlit_app.py             # App entry + navigation
├── .env.example                 # Environment template
├── requirements.txt
└── README.md
```

---



## ⚙️ Environment Setup

Copy `.env.example` to `.env` in the project root and fill in your values:

```bash
# Database
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=Conversations

# Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.8-flash
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# RAG paths
CHROMA_PATH=chroma_db/UNITS_INFO_CHUNCK
FINAL_DATA_PATH=data/final_data.xlsx


API_BASE_URL=http://127.0.0.1:8000

# Twilio voice escalation
EXECUTIVE_PHONE=+91XXXXXXXXXX
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=+1XXXXXXXXXX

```


---



## 💻 Local Installation



### 1. 📥 Clone the repository

```bash
git clone https://github.com/Aryakumarjaiswal/vacation-property.git
cd vacation-property
```



### 2. 🐍 Set up Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```



### 3. 🗄️ Prepare MySQL

Create database `Conversations` (or match `DB_NAME`). Tables are auto-created on first import of `Database.py`.

### 4. 📊 Build vector index + seed users (first time)

```bash
python scripts/rebuild_chroma.py
python scripts/seed_users.py
```

> Run from the **project root** (`vacation-property/`), not inside `scripts/`.



### 5. ⚡ Start FastAPI (Terminal 1)

```bash
uvicorn api.main:app --reload --port 8000
```



### 6. 🎈 Start Streamlit (Terminal 2)

```bash
streamlit run streamlit_app.py
```

Open **[http://localhost:8501](http://localhost:8501)**

---





---



## 📞 Twilio Voice Handoff (Support Escalation)

When a guest asks to **connect to support** in chat:

1. LangGraph detects escalation intent (phrase match or tool call).
2. Twilio places an **outbound call** to `EXECUTIVE_PHONE`.
3. On answer, FastAPI returns **dynamic TwiML** that speaks:
  - Property ID (digit-by-digit, e.g. *“9 3 0”*)
  - Guest’s reported issue from chat
4. Handoff is logged in `chat_transfer_table`.

**Local testing:** Twilio cannot reach `localhost`. Expose port 8000 with [ngrok](https://ngrok.com/) and set:

```bash
API_BASE_URL=https://your-subdomain.ngrok-free.app
```

---

## 🐳 Docker

Build from the project root:

```bash
docker build -f docker/Dockerfile.api -t stayops-api:latest .
docker build -f docker/Dockerfile.streamlit -t stayops-streamlit:latest .
```

Run locally (MySQL must be reachable from the container):

```bash
docker run --rm -p 8000:8000 --env-file .env stayops-api:latest

docker run --rm -p 8501:8501 --env-file .env \
  -e API_BASE_URL=http://host.docker.internal:8000 \
  stayops-streamlit:latest
```

---

## ☸️ Kubernetes Deployment

**Prerequisites:** cluster access, `kubectl`, external MySQL, `data/final_data.xlsx` in the image or mounted volume.

1. **Update image names** in `k8s/api-deployment.yaml` and `k8s/streamlit-deployment.yaml` to match your GHCR path (after CI/CD push).

2. **Create secrets** (never commit `k8s/secret.yaml`):

```bash
cp k8s/secret.example.yaml k8s/secret.yaml
# Edit secret.yaml — DB_PASSWORD, GEMINI_API_KEY, PUBLIC_API_URL, Twilio keys
kubectl apply -f k8s/secret.yaml
```

3. **Apply manifests:**

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/streamlit-deployment.yaml
kubectl apply -f k8s/streamlit-service.yaml
kubectl apply -f k8s/hpa.yaml
```

4. **Index Chroma inside the Streamlit pod** (one-time):

```bash
kubectl exec -it deploy/stayops-streamlit -- python scripts/rebuild_chroma.py
kubectl exec -it deploy/stayops-streamlit -- python scripts/seed_users.py
```

5. **Get UI URL:**

```bash
kubectl get svc stayops-streamlit
```

| Component | K8s service | Notes |
| --- | --- | --- |
| API | `stayops-api:8000` | Internal ClusterIP; expose via Ingress for Twilio |
| Streamlit | `stayops-streamlit` | LoadBalancer on port 80 |
| Chroma | PVC `stayops-chroma-pvc` | Streamlit runs 1 replica (RWO volume) |
| HPA | `stayops-api-hpa` | Scales API 2→6 pods at 70% CPU |

Set `PUBLIC_API_URL` in secrets to your **public API URL** so Twilio can fetch TwiML.

---

## 🔄 CI/CD (GitHub Actions)

Workflow: `.github/workflows/cicd.yml`

On push to `main` / `master`:

1. **Test** — install deps, `compileall` syntax check  
2. **Build & push** — Docker images to GitHub Container Registry:
   - `ghcr.io/<owner>/<repo>-api:latest`
   - `ghcr.io/<owner>/<repo>-streamlit:latest`

Enable **Packages** write permission for `GITHUB_TOKEN` (default on GitHub Actions). After first push, pull images in Kubernetes or make packages public for cluster access.

---

## 🗃️ Database Tables


| Table                 | Purpose                     |
| --------------------- | --------------------------- |
| `registered_users`    | Guest + staff accounts      |
| `Session_table_2`     | Chat sessions per visit     |
| `Chat_table`          | Conversation messages       |
| `chat_transfer_table` | Support handoff audit trail |


---



## 👤 Adding Users

Edit `GUESTS` / `STAFF` in `scripts/seed_users.py`, then:

```bash
python scripts/seed_users.py
```

Passwords are stored as **bcrypt hashes**. For guests, `property_id` must match an indexed Chroma collection.

---



## 🧪 Guest vs Ops — At a Glance


|                    | **Guest Portal**              | **Team Workspace**       |
| ------------------ | ----------------------------- | ------------------------ |
| **User**           | Vacation rental guest         | Internal staff           |
| **Agent**          | RAG over property docs        | SQL on `bookings_info`   |
| **LangGraph flow** | rewrite → retrieve → generate | plan → execute → explain |
| **Escalation**     | Twilio voice to executive     | —                        |


---

