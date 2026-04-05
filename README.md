# ⬡ HIREPATH v2 — Autonomous Recruitment + Email Discovery

> 5-agent autonomous system: sources candidates, **discovers their emails**, screens, engages, schedules, and tracks — zero hardware, free APIs only.

---

## What's New in v2

| Feature | Description |
|---------|-------------|
| **Email Discovery Engine** | 7-source pipeline: GitHub profile → commit history → Hunter.io → SMTP MX verification → pattern inference → Gravatar check |
| **Email Discovery Tab** | Visual dashboard showing email coverage %, per-candidate status, one-click discovery |
| **Bulk Email Discovery** | Background job to find emails for all candidates in a role at once |
| **Domain Search** | Search all known emails at a company domain via Hunter.io |
| **Analytics Tab** | Conversion funnel, source breakdown, avg score, email coverage |
| **CSV/JSON Export** | Export full candidate list with emails, scores, briefs to CSV or JSON |
| **Email Coverage Stats** | Dashboard stat card for total emails found |

---

## Email Discovery Pipeline

For each candidate, the system tries sources in order of reliability:

```
1. GitHub public profile email        → confidence: verified
2. GitHub commit history (Events API) → confidence: high
3. Hunter.io API lookup               → confidence: high
4. SMTP MX verification               → confidence: medium
5. Email permutation inference        → confidence: low
   (john.doe@company.com, jdoe@company.com, etc.)
6. Gravatar confirmation              → upgrades confidence
7. LinkedIn company domain inference  → used to build domain
```

---

## Quick Start

```bash
# 1. Start Postgres
docker run -d --name hirepath-db \
  -e POSTGRES_USER=hirepath -e POSTGRES_PASSWORD=hirepath -e POSTGRES_DB=hirepath \
  -p 5432:5432 postgres:16-alpine

# 2. Setup backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add GROQ_API_KEY (required), GITHUB_TOKEN (recommended), HUNTER_API_KEY (optional)

# 3. Seed demo data + start
python seed.py && python main.py

# 4. Open frontend
open ../frontend/index.html
```

---

## API Keys

| Key | Required | Where | Cost |
|-----|----------|-------|------|
| `GROQ_API_KEY` | ✅ Yes | console.groq.com | Free |
| `GITHUB_TOKEN` | Recommended | github.com/settings/tokens | Free |
| `HUNTER_API_KEY` | Optional | hunter.io | Free (25/mo) |
| `GMAIL_USER` + `GMAIL_APP_PASSWORD` | Optional | myaccount.google.com/apppasswords | Free |
| `GOOGLE_CREDENTIALS_JSON` | Optional | Google Cloud Console | Free |
| `SLACK_WEBHOOK_URL` | Optional | Your Slack App | Free |

---

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/candidates/{id}/discover-email` | Find email for one candidate |
| POST | `/api/roles/{id}/discover-emails` | Bulk email discovery (background) |
| GET | `/api/roles/{id}/email-stats` | Email coverage stats |
| POST | `/api/email/domain-search` | Search all emails at a domain |
| GET | `/api/roles/{id}/export/csv` | Export candidates as CSV |
| GET | `/api/roles/{id}/export/json` | Export candidates as JSON |
| GET | `/api/analytics/funnel/{id}` | Conversion funnel analytics |
| POST | `/api/scout/stream` | Stream SCOUT results (SSE) |
| POST | `/api/screen/{candidate_id}` | AI resume screening |
| POST | `/api/engage` | Bulk outreach emails |
| POST | `/api/coord/schedule` | Schedule interview |
| GET | `/api/track/health/{id}` | Pipeline health score |
| GET | `/api/events` | SSE real-time stream |

---

## Pitch Line

> *"A recruiter typed one job description. HIREPATH found the candidates, discovered their emails, wrote personalized outreach, scheduled interviews, and flagged every drop-off — all while you slept."*
