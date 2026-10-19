# HirePath

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript-61DAFB.svg)](https://react.dev/)
[![Compliance](https://img.shields.io/badge/DPDPA%202023-Section%206%20Compliant-success.svg)](https://www.meity.gov.in/)

HirePath is an autonomous, consent-first AI recruiting intelligence platform engineered for live talent discovery, objective evaluation, human-in-the-loop engagement, and strict legal compliance.

Unlike traditional recruitment tools that rely on pre-canned dummy records or scrape unverified data, HirePath **sources 100% live verified developer profiles**, enforces **Section 6 Digital Personal Data Protection Act (DPDPA 2023)** consent boundaries, and provides an end-to-end, tamper-evident audit ledger for every recruiter and agentic action.

---

## 🌟 Key Features

### 1. 🔍 Autonomous Live Sourcing Agent (`SCOUT`)
- **Real-Time Live Profiling**: Queries GitHub GraphQL API v4 and StackExchange APIs directly in real-time. No static, synthetic, or pre-seeded candidate data is ever used.
- **Top Repository & Star Extraction**: Directly extracts top-starred open-source projects, stargazer metrics, and public proof links via GraphQL within a single request, eliminating slow sequential REST queries.
- **Gazetteer-Powered Location Engine**: Uses an exact gazetteer matching algorithm (`location_resolver.py`) covering Maharashtra and Tier-1/2 tech hubs across India (Pune, Mumbai, Nagpur, Nashik, Bengaluru, Hyderabad, etc.), preventing false positives (e.g., distinguishing Pune, India from foreign namesakes).
- **Adaptive Querying**: Dynamically extracts high-signal keywords from role titles (e.g., Product Management, DevOps, Full-Stack, ML) and distributes targeted queries across locations to reliably yield top candidates without hitting restrictive intersections.
- **Proof-Gated Ingestion**: Only persists candidates with verifiable public profile URLs, active repository links, and timestamped retrieval metadata.

### 2. 🧠 Multi-Criteria AI Screening Agent (`SCREEN`)
- **LLM-Powered Technical Evaluation**: Evaluates candidates against strict job requirements using Groq LLM inference (`qwen/qwen3.8-27b`) or structured deterministic scoring fallbacks.
- **Multi-Factor Scoring Matrix**:
  - **Technical Skills Alignment (40%)**: Verified language, framework, and tool usage across live repositories.
  - **Project Depth & Code Quality (30%)**: Real contribution track records, repository stars, commit frequency, and documentation.
  - **Experience & Seniority (20%)**: Public tenure, career progression, and repository maturity.
  - **Domain Alignment (10%)**: Relevance to target industry or product segment.
- **Explainable Recommendation Briefs**: Produces human-readable rationales, highlighted strengths, and potential risks for every candidate screened.

### 3. ✉️ Consent-First Outreach Agent (`ENGAGE`)
- **Mandatory Contact Consent (DPDPA Section 6)**: Strictly prevents outreach emails from firing until a recruiter explicitly toggles verified contact consent.
- **Personalized Pitch Generation**: Contextually drafts personalized outreach emails referencing the candidate's actual top open-source projects and repositories.
- **Real SMTP Delivery**: Delivers messages through secure Gmail SMTP (`smtp.gmail.com`). Failed deliveries or missing credentials preserve pipeline state without false "sent" transitions.
- **Tamper-Evident One-Click Unsubscribe & Right-to-Forget**: Generates HMAC-SHA256 signed opt-out (`/privacy/opt-out`) and deletion (`/privacy/delete`) URLs in every outgoing email, granting candidates instant self-service rights without requiring login.

### 4. 📅 Interview Coordination Agent (`COORD`)
- **Google Calendar Integration**: Automatically books interviews with recruiter/candidate calendar invites using the Google Calendar API.
- **Timezone Intelligence**: Operates natively in Indian Standard Time (`Asia/Kolkata` / IST) with slot-conflict detection and ISO timestamp formatting.
- **Automated Reminders**: Built-in cron task queues automated interview reminders 24 hours prior to scheduled meetings.

### 5. 📊 Pipeline Health & Activity Monitoring (`TRACK`)
- **Pipeline Analytics**: Real-time velocity tracking across `Sourced` → `Screened` → `Contacted` → `Interview` → `Hired` → `Rejected`.
- **Stale Candidate Detection**: Flags candidates stalled at a stage for more than 7 days and triggers recruiter action recommendations.
- **Real-Time SSE Activity Stream**: Delivers live agent thought-process logs, sourcing progress, and state transitions to the recruiter dashboard via Server-Sent Events (`/api/stream`).
- **Slack Alerting**: Optional Slack incoming webhook integration for stage transitions, critical pipeline bottlenecks, and daily digests.

### 6. 🛡️ Compliance & Audit Ledger
- **SHA-256 Tamper-Evident Log**: Every candidate update, consent action, email dispatch, and screening decision is cryptographically hashed and linked in a tamper-evident audit ledger.
- **Exportable Compliance Logs**: One-click download of compliance reports in CSV and JSON formats for audit readiness.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend Architecture** | **React 18**, **TypeScript**, **Vite**, **Tailwind CSS** |
| **UI & Visual Design** | Google Material Symbols, Lucide React, Glassmorphism, Tailwind Transitions, Custom Toasts & Modal Dialogs |
| **Backend Framework** | **FastAPI** (Async Python 3.10+), **Uvicorn** (ASGI Server), **Starlette** |
| **Database & ORM** | **SQLAlchemy 2.0 (Async)**, **SQLite** (local / testing) with **PostgreSQL** (`asyncpg`) production support, **Alembic** (Database Migrations) |
| **AI / LLM Inference** | **Groq API** (`qwen/qwen3.8-27b`), Tenacity (Exponential Backoff & Retries), Pydantic v2 validation |
| **External APIs** | **GitHub GraphQL API v4**, **GitHub REST API**, **StackExchange API**, **Google Calendar API v3**, **Gmail SMTP** |
| **Task Scheduling** | **APScheduler** (Background reminder cron jobs & stale candidate monitors) |
| **Security & Privacy** | HMAC-SHA256 signed privacy tokens, API Key authentication (`X-Api-Key`), DPDPA 2023 compliance controls |

---

## 📁 Repository Structure

```
hirepath/
├── backend/
│   ├── agents/
│   │   ├── scout.py           # Live Sourcing Agent (GitHub GraphQL & REST, StackExchange)
│   │   ├── screen.py          # LLM & Heuristic Screening Agent
│   │   ├── engage.py          # Consent-gated SMTP Email Outreach Agent
│   │   ├── coord.py           # Google Calendar Interview Coordination Agent
│   │   └── track.py           # Pipeline analytics & stale candidate detector
│   ├── data/
│   │   └── location_gazetteer.csv # Geo-resolution dataset for Indian tech hubs
│   ├── migrations/            # Alembic async migration versions
│   │   └── versions/
│   ├── tests/                 # Full pytest suite with mocks & safety flows
│   ├── utils/
│   │   ├── location_resolver.py # Fast gazetteer-based location parser
│   │   ├── privacy.py         # HMAC token signing & DPDPA validation
│   │   └── rate_limiter.py    # Per-domain outbound rate limiting
│   ├── config.py              # Central Pydantic BaseSettings configuration
│   ├── database.py            # Async SQLAlchemy engine, models, and ledger
│   ├── main.py                # FastAPI REST & SSE endpoints
│   ├── orchestrator.py        # Central event bus and pipeline state machine
│   ├── requirements.txt       # Production dependencies
│   └── schemas.py             # Pydantic v2 request/response schemas
├── frontend/                  # Production-built web dashboard assets
│   ├── index.html             # Served HTML bundle
│   └── assets/                # Minified React/Vite JavaScript & CSS bundles
├── frontend_src/              # Complete React 18 + TypeScript source code
│   ├── src/
│   │   ├── components/        # Sourcing, Outreach, Role Edit, & Interview modals
│   │   ├── context/           # AppContext state & live SSE stream consumer
│   │   ├── views/             # Pipeline, Candidates, Activity, Compliance, Settings views
│   │   ├── types.ts           # Unified TypeScript definitions
│   │   └── main.tsx           # React DOM bootstrap
│   ├── package.json           # Frontend dependency manifest
│   ├── tailwind.config.js     # Tailwind CSS theme configuration
│   └── vite.config.ts         # Vite bundler configuration
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm` (for frontend modifications)
- A **GitHub Personal Access Token** (classic `repo` or fine-grained read-only)
- A **Groq API Key** (free at [console.groq.com](https://console.groq.com))

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/kanglesoham11-code/hirepath.git
cd hirepath
```

---

### Step 2: Backend Setup
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

#### Configure `.env`
Update `backend/.env` with your API keys:
```dotenv
DATABASE_URL=sqlite+aiosqlite:///./hirepath.db
API_SECRET_KEY=your_generated_random_secret_here
GITHUB_TOKEN=ghp_your_github_token_here
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b

# Outreach & Coordination (Optional for full email/calendar automation)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
GOOGLE_CREDENTIALS_JSON=
SLACK_WEBHOOK_URL=
FRONTEND_URL=http://localhost:3000
```

#### Run Migrations & Start Server
```bash
python -m alembic upgrade head
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will run at **`http://127.0.0.1:8000`** (Swagger docs available at **`http://127.0.0.1:8000/docs`**).

---

### Step 3: Frontend Setup

#### Option A: Run the Pre-Built Dashboard (Zero Setup)
In a separate terminal, serve the production bundle:
```bash
cd frontend
python -m http.server 3000
```
Open **`http://localhost:3000`** in your browser.

#### Option B: Run the Development Server (with Live Hot-Reloading)
```bash
cd frontend_src
npm install
npm run dev
```

---

## 🔒 Security & Privacy (DPDPA 2023)

HirePath was designed with data protection as an architectural constraint rather than an afterthought:

1. **Section 6 Consent Verification**: Contact channels (email addresses) are shielded until explicit affirmative recruiter consent is logged in the database.
2. **Right to Confirmation & Correction**: Candidates can inspect their stored profile metadata via signed privacy links.
3. **Right to Erasure (Forget Me)**: When a candidate activates their deletion link:
   - All profile data, contact information, and screening notes are permanently purged from the database.
   - A tombstone record with an HMAC hash of their identity is retained in the opt-out ledger to prevent SCOUT from re-ingesting them in future searches.
4. **No Sensitive PII in Audit Logs**: Cryptographic activity logs record decisions and metadata without storing raw emails or phone numbers.

---

## 🧪 Running Automated Tests

Run the comprehensive test suite covering safety boundaries, API fallbacks, rate-limiters, and agent flows:

```bash
cd backend
pytest -v
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
