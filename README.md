# HirePath

HirePath is a local recruitment workflow dashboard for sourcing public developer profiles in Maharashtra, screening them, recording recruiter decisions, coordinating interviews, and monitoring the pipeline. It creates no sample roles or candidate records.

## What it does

- **SCOUT** retrieves public GitHub and Stack Overflow profiles live, verifies each profile's declared location with whole-word Maharashtra matching, includes automatic 401 fallback to unauthenticated public API, and rejects any record that has no safe public profile or repository link.
- **SCREEN** performs one authoritative AI assessment per candidate using Groq (`qwen/qwen3.8-27b`) and stores the score, prompt version, model, scoring timestamp, and source-linked claims with the decision.
- **ENGAGE** sends outreach only after a recruiter records contact consent. It updates a candidate only after Gmail SMTP accepts the message. Includes signed one-click opt-out & profile deletion links in every email.
- **COORD** creates a real Google Calendar event before marking an interview as scheduled. Interview slots use `Asia/Kolkata` (IST) and reminders run once per interview.
- **TRACK** summarizes pipeline health, detects stale candidates, and exposes an explicit action for marking a candidate stale with Slack integration.

Each outreach email includes signed links to opt out of future outreach or delete the candidate profile. The privacy page asks for confirmation before submitting either request.

## Live source evidence

Candidate records can only be created by SCOUT. Direct candidate creation is intentionally unavailable, and the initializer creates no demonstration roles or candidates.

For every visible candidate, HirePath stores the public GitHub profile, GitHub repository, or Stack Overflow profile URLs returned by the live source API, plus the capture time. The dashboard shows a **Verify source** link on each candidate row and a **Verified Public Evidence** list in the screening brief. Screening, outreach, interview scheduling, reminders, pipeline analytics, and candidate-stage changes all reject records without this evidence.

Existing records from before this version are hidden until SCOUT captures fresh evidence for them. A source link proves where a public fact was retrieved; recruiters should still review it before making a hiring or outreach decision.

## Requirements

- Python 3.10 or later
- A GitHub personal access token. SCOUT requires it and will stop with a clear configuration error when it is absent.
- A Groq API key for AI screening and generated outreach.
- An API secret for dashboard write actions and privacy-link signatures.
- Gmail app credentials to send outreach.
- Google Calendar OAuth credentials to create interview events.

## Quick start

```bash
git clone https://github.com/kanglesoham11-code/hirepath.git
cd hirepath/backend

python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows PowerShell
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```

Set these values in `backend/.env` before starting the application:

```dotenv
GROQ_API_KEY=
GITHUB_TOKEN=
API_SECRET_KEY=
GROQ_MODEL=qwen/qwen3.8-27b
```

Generate an API secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The provided scripts validate those required values and apply database migrations:

```bash
# Linux/macOS
./start.sh

# Windows Command Prompt
start.bat
```

Or start services manually:

```bash
python -m alembic upgrade head
python seed.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Serve the dashboard in another terminal:

```bash
cd ../frontend
python -m http.server 3000
```

Open <http://localhost:3000>. The dashboard asks for `API_SECRET_KEY` before its first write action and keeps it only for the current browser session.

Create an actual role in the dashboard. `python seed.py` only initializes the schema and never adds a sample role or candidate.

## Configuration

| Variable | Purpose | Required for |
| --- | --- | --- |
| `DATABASE_URL` | SQLite by default; PostgreSQL with `postgresql+asyncpg://...` | Database |
| `GROQ_API_KEY` | Groq API authentication | Screening and generated messages |
| `GROQ_MODEL` | Groq model | Defaults to `qwen/qwen3.8-27b` |
| `GITHUB_TOKEN` | Authenticated GitHub API access | SCOUT |
| `API_SECRET_KEY` | Write-endpoint authentication and privacy-link signing | Dashboard writes and outreach |
| `GMAIL_USER` / `GMAIL_APP_PASSWORD` | Gmail SMTP credentials | ENGAGE |
| `GOOGLE_CREDENTIALS_JSON` | Google Calendar OAuth credentials file | COORD |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook | TRACK alerts |
| `FRONTEND_URL` | Dashboard origin used in privacy links | Defaults to `http://localhost:3000` |
| `PRIVACY_TOKEN_TTL_DAYS` | Signed privacy-link lifetime | Defaults to 30 days |

## Candidate data and outreach

SCOUT stores only contact emails published by a GitHub profile API response. Every candidate also requires a live, recruiter-verifiable public source link. A recruiter must record the candidate's contact consent in the dashboard before any outreach can be sent. Failed or unconfigured SMTP leaves the candidate's stage, contact count, and activity timestamp unchanged.

The activity log stores the decision metadata needed for review: screening model, prompt version, score, recommendation, and recruiter consent action. It avoids logging contact email addresses.

`POST /api/privacy/opt-out` and `POST /api/privacy/delete` intentionally accept signed privacy tokens rather than the dashboard API key. All dashboard-controlled `POST`, `PATCH`, and `DELETE` routes require `X-Api-Key`.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/roles` | List roles |
| `POST` | `/api/roles` | Create a role |
| `GET` | `/api/roles/{id}/candidates` | List a role's candidates, optionally by stage |
| `POST` | `/api/scout` | Start SCOUT in the background |
| `POST` | `/api/screen/role/{id}` | Screen sourced candidates |
| `POST` | `/api/candidates/{id}/contact-consent` | Record recruiter-approved outreach consent |
| `POST` | `/api/engage` | Send approved outreach to selected candidates |
| `POST` | `/api/coord/schedule` | Create a Google Calendar interview event |
| `POST` | `/api/track/mark-stale` | Mark selected candidate IDs as stale |
| `GET` | `/api/track/health/{id}` | Read pipeline health |
| `POST` | `/api/privacy/opt-out` | Process a signed opt-out request |
| `POST` | `/api/privacy/delete` | Process a signed data-deletion request |

## Database migrations

Alembic reads `DATABASE_URL` from `backend/.env`. Migration `0002_align_enums_and_privacy` aligns PostgreSQL enum labels with the SQLAlchemy models, converts legacy interview values to timezone-aware timestamps, and adds consent and reminder fields. Migration `0003_live_source_evidence` adds the source-verification flag, capture timestamp, and public evidence list. It works with fresh SQLite and PostgreSQL deployments as well as existing installations.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Tests use an isolated SQLite database and mock external services. They cover Maharashtra and keyword matching, safe source-evidence links, de-duplication, source and consent-gated outreach, SMTP failure handling, scheduling, privacy tokens, empty-pipeline handling, and write-route authentication.

## Current scope

The dashboard has no resume-upload endpoint or direct candidate-import endpoint. Candidate evidence comes from SCOUT's live public-source retrieval. ChromaDB, vector search, and local-resume parsing have been removed because no active feature uses them.

## License

MIT. See [LICENSE](LICENSE).
