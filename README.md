# GradMatch — UK Graduate Job Search Automation

Pulls UK graduate/entry-level tech & QA jobs daily from official APIs (Adzuna, Reed),
deduplicates them, and sends new matches to Telegram. Runs at £0/month via GitHub Actions.

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then fill in your real keys
```

You need four free credentials:
1. **Adzuna** — register at developer.adzuna.com → App ID + App Key
2. **Reed** — register at reed.co.uk/developers → API key
3. **Telegram bot token** — message @BotFather on Telegram, `/newbot`
4. **Telegram chat ID** — message your new bot anything, then visit
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and read the chat id out of the JSON

Put all four in `.env`.

## Run it

```bash
python main.py
```

First run: fetches jobs, saves new ones to `data/jobs.db`, sends up to 10 to Telegram.
Second run: should find far fewer (ideally 0) *new* jobs — proof deduplication works.

## Run the tests

```bash
pytest tests/ -v
```

## Daily automation

`.github/workflows/daily-job-run.yml` runs this automatically every day at 07:00 UTC via
GitHub Actions — free, no server needed. To enable it:
1. Push this repo to GitHub
2. Go to Settings → Secrets and variables → Actions
3. Add the same 5 values from your `.env` as repository secrets (same names)
4. The workflow will run automatically on schedule, or trigger it manually from the Actions tab

## What's not built yet

- AI/embedding-based match scoring (currently every new job is sent, unscored)
- Excel export
- Company career-page (Greenhouse/Lever) sources
