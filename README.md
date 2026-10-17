# HIREPATH - Autonomous Recruitment Intelligence System

> **5-Agent AI Pipeline** that autonomously sources, screens, engages, schedules, and tracks candidates — all powered by live data scraping and LLM intelligence.

**Location Focus:** Maharashtra, India (Mumbai, Pune, Nagpur, Nashik, Thane, and more)

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Complete Workflow — Step by Step](#complete-workflow--step-by-step)
- [The 5 Agents in Detail](#the-5-agents-in-detail)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [API Reference](#api-reference)
- [Configuration](#configuration)

---

## System Architecture

```
                         +-------------------+
                         |   HIREPATH UI      |
                         |  (Single-Page App) |
                         +--------+----------+
                                  |
                           REST + SSE
                                  |
                         +--------v----------+
                         |   FastAPI Backend  |
                         |   (main.py)        |
                         +--------+----------+
                                  |
                    +-------------+-------------+
                    |                             |
             +------v------+              +------v------+
             | Orchestrator |              |  Scheduler  |
             | (LangGraph)  |              | (APScheduler)|
             +------+------+              +------+------+
                    |                             |
     +---------+---+---+---------+        Auto follow-ups
     |         |       |         |        Auto tracking
     v         v       v         v
  +-----+  +------+ +------+ +-----+ +-----+
  |SCOUT|  |SCREEN| |ENGAGE| |COORD| |TRACK|
  +--+--+  +--+---+ +--+---+ +--+--+ +--+--+
     |        |         |        |        |
     v        v         v        v        v
  GitHub   Groq LLM   Gmail   Google    Slack
  StackOF  (Llama 3)  SMTP    Calendar  Webhook
  (LIVE)              (LIVE)  (LIVE)    (LIVE)
```

**Key Principle:** ZERO hardcoded candidate data. Every single candidate is scraped live from real APIs.

---

## Complete Workflow — Step by Step

### Phase 0: System Initialization

1. **Database Setup** (`seed.py`)
   - Creates SQLite database with tables: `roles`, `candidates`, `agent_logs`
   - Seeds **only role definitions** (job descriptions + requirements)
   - **NO candidate data is seeded** — all candidates come from live scraping
   - Roles are tagged with Maharashtra-specific location requirements

2. **Server Startup**
   - FastAPI backend starts on `http://127.0.0.1:8000`
   - APScheduler starts background jobs (follow-up sweep every 6h, tracking every 12h)
   - SSE broadcaster initializes for real-time event streaming to the frontend
   - Frontend served on `http://localhost:3000`

---

### Phase 1: SCOUT — Live Candidate Sourcing

**Trigger:** User clicks "SCOUT" button or calls `POST /api/scout`

**What happens internally:**

```
User clicks SCOUT
       |
       v
1. Fetch Role from DB (title, requirements, description)
       |
       v
2. Extract Keywords (e.g., "python", "fastapi", "docker")
       |
       v
3. GitHub Location Search (LIVE API calls)
   |-- Query: "python+fastapi+location:Mumbai+type:user"
   |-- Query: "python+fastapi+location:Pune+type:user"
   |-- Query: "python+fastapi+location:Maharashtra+type:user"
   |-- Query: "python+fastapi+location:Nagpur+type:user"
   |-- For each result:
   |     |-- GET /users/{login} (full profile: bio, company, location, email)
   |     |-- GET /users/{login}/repos?sort=stars (top 5 repos)
   |     |-- Filter: only keep if location matches Maharashtra
   |     └-- Build candidate record with all scraped data
       |
       v
4. GitHub Contributor Search (LIVE API calls)
   |-- Map keywords to repos (e.g., "fastapi" -> "tiangolo/fastapi")
   |-- GET /repos/{owner}/{repo}/contributors
   |-- For each contributor:
   |     |-- GET /users/{login} (full profile)
   |     └-- Filter: only keep if location matches Maharashtra
       |
       v
5. StackOverflow Search (LIVE API calls)
   |-- GET api.stackexchange.com/2.3/users?inname=Mumbai
   |-- GET api.stackexchange.com/2.3/users?inname=Pune
   |-- Filter by Maharashtra locations
   |-- Extract: reputation, display_name, website (for GitHub links)
       |
       v
6. Deduplication
   |-- Check each candidate against existing DB records
   |-- Match on github_url or email
   |-- Skip already-sourced candidates
       |
       v
7. LLM Scoring (Groq API — Llama 3.3 70B)
   |-- For each new candidate:
   |     |-- Build profile text (name, bio, repos, languages, stars, etc.)
   |     |-- Send to Groq with role requirements + scoring rubric
   |     |-- Receive: score (0-100), summary, strengths, concerns
   |     |-- Validate and clamp score
   |     └-- Skip if score < 20
       |
       v
8. Save to Database
   |-- Create Candidate record with stage=SOURCED
   |-- Store: name, email, github_url, score, screen_brief, raw_data
   |-- Log event to agent_logs table
   └-- Broadcast via SSE to frontend (real-time update)
```

**Data Sources (ALL LIVE):**
- GitHub REST API v3 (users, repos, contributors)
- StackExchange API v2.3 (users by location)
- Groq LLM API (candidate scoring)

**Location Matching:**
Candidates must have a GitHub/StackOverflow location containing one of:
`maharashtra, mumbai, pune, nagpur, thane, nashik, aurangabad, solapur, kolhapur, sangli, navi mumbai, amravati, nanded, bhiwandi, jalgaon, akola, latur, dhule, ahmednagar, chandrapur, parbhani, ichalkaranji, jalna, ambernath, malegaon, mira-bhayandar, panvel, india`

---

### Phase 2: SCREEN — AI-Powered Deep Evaluation

**Trigger:** User clicks "SCREEN All" or calls `POST /api/screen/role/{role_id}`

**What happens internally:**

```
1. Fetch all SOURCED candidates for the role
       |
       v
2. For each candidate:
   |
   |-- a. Resume Parsing (if PDF uploaded)
   |     └-- PyMuPDF extracts text (up to 8000 chars)
   |
   |-- b. GitHub Profile Enrichment (LIVE API call)
   |     |-- GET /users/{login} (name, bio, company, location, hireable)
   |     |-- GET /users/{login}/repos?sort=stars&per_page=8
   |     └-- Build: repo names, stars, languages, descriptions
   |
   |-- c. Existing Scout Notes
   |     └-- Include previous scoring summary + strengths + concerns
   |
   |-- d. LLM Deep Screening (Groq API)
   |     |-- System prompt: "You are a world-class senior technical recruiter..."
   |     |-- Input: role requirements + candidate's full profile
   |     |-- Output JSON:
   |     |     - overall_score (0-100)
   |     |     - years_experience (int or null)
   |     |     - top_skills (list)
   |     |     - skill_gaps (list)
   |     |     - strengths (max 4, evidence-backed)
   |     |     - concerns (max 4, specific)
   |     |     - red_flags (list)
   |     |     - suggested_interview_questions (exactly 4, tailored)
   |     |     - one_line_verdict (max 20 words)
   |     |     - hire_recommendation ("strong_yes"|"yes"|"maybe"|"no")
   |     └-- Validation: clamp scores, ensure list types, validate enums
   |
   └-- e. Update Database
         |-- Store screen_brief JSON blob
         |-- Update score
         |-- Set stage = SCREENED
         └-- Log event
```

**Scoring Rubric:**
| Score Range | Meaning |
|------------|---------|
| 85-100 | Exceptional — deep expertise, strong evidence of impact |
| 70-84 | Strong — clear core skills, minor gaps |
| 55-69 | Moderate — some relevant skills, significant gaps |
| 40-54 | Weak — limited relevant evidence |
| 0-39 | No match — skip |

---

### Phase 3: ENGAGE — Personalized AI Outreach

**Trigger:** User clicks "Engage Top" or calls `POST /api/engage`

**What happens internally:**

```
1. Select candidates with score >= 60 and valid email
       |
       v
2. For each candidate:
   |
   |-- a. Generate Personalized Email (Groq LLM)
   |     |-- System prompt enforces:
   |     |     - Open with SPECIFIC observation about their work
   |     |     - Reference actual repos/contributions
   |     |     - Warm, conversational tone
   |     |     - Single low-friction CTA
   |     |     - 150-200 words
   |     |-- Input: candidate profile + role description
   |     └-- Output: HTML email body
   |
   |-- b. Send via Gmail SMTP
   |     |-- TLS/SSL connection to smtp.gmail.com:465
   |     |-- Authenticate with app-specific password
   |     |-- Send MIME multipart (HTML) email
   |     └-- Subject: "Quick note — {role.title} opportunity"
   |
   └-- c. Update Database
         |-- Increment outreach_count
         |-- Set last_contacted_at = now
         |-- Set stage = OUTREACH_SENT
         └-- Log event

3. Follow-up Logic (automated every 6 hours):
   |-- Find candidates where:
   |     - stage == OUTREACH_SENT
   |     - last_contacted_at > 48 hours ago
   |     - outreach_count < 3 (max 3 attempts)
   |-- Generate follow-up email (different tone, acknowledges they're busy)
   └-- Send via same SMTP pipeline
```

---

### Phase 4: COORD — Interview Scheduling

**Trigger:** User clicks "Schedule" or calls `POST /api/coord/schedule`

**What happens internally:**

```
1. Find next available business-hours slot
   |-- Skip weekends
   |-- Target: IST 9:30 AM - 3:30 PM (UTC 4:00 - 10:00)
   |-- Round to next hour
       |
       v
2. Generate Interview Prep Doc (Groq LLM)
   |-- Candidate Snapshot (3-4 bullets)
   |-- Areas to Probe (4 specific areas)
   |-- Tailored Questions (5 numbered, candidate-specific)
   |-- What Good Looks Like (per question)
   |-- Red Flags to Watch (2-3 items)
       |
       v
3. Create Google Calendar Event
   |-- Summary: "Interview: {name} - {role}"
   |-- Attendees: interviewer + candidate
   |-- Auto-add Google Meet link
   |-- Reminders: 24h email + 1h popup
   |-- Description includes prep doc
       |
       v
4. Update Database
   |-- Set stage = INTERVIEW_SCHEDULED
   |-- Store interview_time and calendar_event_id
   └-- Log event
```

---

### Phase 5: TRACK — Pipeline Intelligence

**Trigger:** User clicks "TRACK" or runs automatically every 12 hours

**What happens internally:**

```
1. Compute Pipeline Health (per role)
   |-- Count candidates per stage
   |-- Detect stale candidates (no activity in 3+ days)
   |-- Identify bottleneck stage (highest non-terminal count > 2)
   |-- Calculate health score (0-100):
   |     - Base: 50
   |     - +min(20, total_candidates)
   |     - +30 if any hired
   |     - -5 per stale candidate
   |     - -0.5 per excess active candidate (>15)
       |
       v
2. Generate Insights
   |-- "X candidates stale for 3+ days"
   |-- "Bottleneck at 'screened' stage"
   |-- "X outreach sent, 0 replies — revisit messaging"
   |-- "Large pipeline with 0 hires — move top candidates forward"
       |
       v
3. Slack Alerts (if configured)
   |-- Fire webhook on: stale candidates detected
   |-- Fire webhook on: health score < 40
       |
       v
4. Weekly Report Generation (Groq LLM)
   |-- Executive summary of hiring velocity
   |-- Per-role breakdown with metrics
   |-- Red flags and urgent issues
   |-- 3 actionable recommended next steps
   └-- Output: Formatted HTML report
```

---

### Full Pipeline Orchestration (LangGraph)

When "Run Full Pipeline" is clicked, the orchestrator chains all 5 agents:

```
SCOUT --> SCREEN --> ENGAGE --> FOLLOWUP --> TRACK
  |          |          |          |           |
  v          v          v          v           v
Source     Evaluate   Send       Follow up   Analyze
candidates profiles   outreach   stale       pipeline
from APIs  via LLM    via SMTP   candidates  health
```

**LangGraph State Machine:**
- Entry: `scout_node`
- Edge: scout -> screen (always)
- Conditional: screen -> engage (if top_candidate_ids exist) OR screen -> track
- Edge: engage -> followup (always)
- Edge: followup -> track (always)
- Terminal: track -> END

**Fallback:** If LangGraph is not installed, runs sequentially without the state graph.

---

## The 5 Agents in Detail

| Agent | File | Purpose | External APIs Used |
|-------|------|---------|-------------------|
| **SCOUT** | `agents/scout.py` | Source candidates LIVE from GitHub + StackOverflow, filtered to Maharashtra | GitHub API, StackExchange API, Groq LLM |
| **SCREEN** | `agents/screen.py` | Deep-evaluate each candidate's profile with AI | GitHub API, Groq LLM |
| **ENGAGE** | `agents/engage.py` | Generate personalized emails and send via SMTP | Groq LLM, Gmail SMTP |
| **COORD** | `agents/coord.py` | Schedule interviews with prep docs and calendar invites | Groq LLM, Google Calendar API |
| **TRACK** | `agents/track.py` | Monitor pipeline health, detect bottlenecks, generate reports | Groq LLM, Slack Webhooks |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | FastAPI (Python, async) |
| **Database** | SQLite + SQLAlchemy (async) with aiosqlite |
| **LLM** | Groq API (Llama 3.3 70B Versatile) |
| **Orchestration** | LangGraph (state machine) with sequential fallback |
| **HTTP Client** | httpx (async) |
| **Email** | Gmail SMTP (smtplib, SSL) |
| **Calendar** | Google Calendar API v3 |
| **Notifications** | Slack Incoming Webhooks |
| **Scheduling** | APScheduler (AsyncIOScheduler) |
| **Vector Store** | ChromaDB (optional, for semantic search) |
| **Frontend** | Vanilla HTML/CSS/JS (single-page app) |
| **Real-time** | Server-Sent Events (SSE) |

---

## Project Structure

```
hirepath/
|-- backend/
|   |-- main.py              # FastAPI app, all REST endpoints, SSE broadcaster
|   |-- config.py            # Pydantic settings (env vars)
|   |-- database.py          # SQLAlchemy models (Role, Candidate, AgentLog)
|   |-- schemas.py           # Pydantic request/response schemas
|   |-- orchestrator.py      # LangGraph pipeline (SCOUT->SCREEN->ENGAGE->TRACK)
|   |-- seed.py              # DB initialization (roles only, NO hardcoded candidates)
|   |-- requirements.txt     # Python dependencies
|   |-- .env                 # Environment variables (API keys)
|   |-- agents/
|   |   |-- scout.py         # LIVE sourcing from GitHub + StackOverflow (Maharashtra)
|   |   |-- screen.py        # AI-powered candidate evaluation
|   |   |-- engage.py        # Personalized email outreach
|   |   |-- coord.py         # Interview scheduling + prep doc generation
|   |   |-- track.py         # Pipeline health monitoring + Slack alerts
|   |-- utils/
|   |   |-- llm.py           # Groq API wrapper (retry logic, JSON extraction)
|   |   |-- logger.py        # Agent event logging + SSE broadcast
|   |   |-- vector_store.py  # ChromaDB integration (semantic candidate search)
|-- frontend/
|   |-- index.html           # Complete single-page app (HTML + CSS + JS)
|-- docker-compose.yml
|-- .gitignore
|-- README.md
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- GitHub Personal Access Token
- Groq API Key (free at console.groq.com)
- Gmail App Password (for outreach emails)

### Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/sohamkangle/hirepath.git
cd hirepath

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Configure environment variables
# Edit .env with your API keys (see .env.example)

# 4. Initialize the database (creates roles, NO hardcoded candidates)
python seed.py

# 5. Start the backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 6. Start the frontend (in a new terminal)
cd ../frontend
python -m http.server 3000

# 7. Open http://localhost:3000
```

---

## API Reference

### Roles
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/roles` | List all roles |
| POST | `/api/roles` | Create a new role |
| GET | `/api/roles/{id}` | Get role details |
| DELETE | `/api/roles/{id}` | Delete a role |

### Candidates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/roles/{id}/candidates` | List candidates for a role |
| POST | `/api/candidates` | Add a candidate manually |
| GET | `/api/candidates/{id}` | Get candidate details |
| PATCH | `/api/candidates/{id}/stage` | Update candidate stage |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scout` | Run SCOUT (background, live scraping) |
| POST | `/api/scout/stream` | Run SCOUT with SSE streaming |
| POST | `/api/screen/{id}` | Screen a single candidate |
| POST | `/api/screen/role/{id}` | Screen all sourced candidates |
| POST | `/api/engage` | Engage multiple candidates |
| POST | `/api/engage/{id}` | Engage a single candidate |
| POST | `/api/engage/followup-sweep` | Run follow-up on stale outreach |
| POST | `/api/coord/schedule` | Schedule an interview |
| POST | `/api/track` | Run pipeline analysis |
| GET | `/api/track/health/{id}` | Get pipeline health for a role |
| GET | `/api/track/report` | Generate weekly report |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/events` | SSE stream for real-time events |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/logs` | Agent activity logs |
| POST | `/api/pipeline/run` | Run full 5-agent pipeline |

---

## Configuration

All configuration is via environment variables (`.env` file):

| Variable | Purpose | Required |
|----------|---------|----------|
| `GROQ_API_KEY` | Groq LLM API key for AI scoring/screening | Yes |
| `GITHUB_TOKEN` | GitHub PAT for higher rate limits | Yes |
| `GMAIL_USER` | Gmail address for outreach emails | For ENGAGE |
| `GMAIL_APP_PASSWORD` | Gmail app-specific password | For ENGAGE |
| `GOOGLE_CREDENTIALS_JSON` | Google OAuth credentials for Calendar | For COORD |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | For TRACK |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |
| `GROQ_MODEL` | Groq model name | No (defaults to llama-3.3-70b-versatile) |

---

## Key Design Decisions

1. **No Hardcoded Data:** Every candidate is sourced live from real APIs. The seed file only creates job role definitions.

2. **Maharashtra-Specific:** GitHub search uses `location:Mumbai`, `location:Pune`, etc. StackOverflow searches filter by Maharashtra cities. All results are validated against a list of 25+ Maharashtra locations.

3. **Rate Limit Handling:** Built-in delays between API calls (0.3-1s), exponential backoff on 429/503 errors, max 4 retries per LLM call.

4. **Graceful Degradation:** Every external service has fallback behavior (no Groq key = default scores, no Gmail = console logging, no Google Calendar = mock events, no LangGraph = sequential execution).

5. **Real-time Updates:** SSE broadcaster pushes agent events to the frontend. The frontend auto-polls for new candidates during scouting.

---

*Built for the hackathon. Powered by Groq, GitHub, and Maharashtra talent.*
