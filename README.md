# Hotel Weekly AI Reporting — Python Starter

A runnable starter project for the **AI Management Trainee Assignment**: read hotel performance data, classify each hotel, use DeepSeek to draft a personalized owner email, and optionally send test emails via Gmail API.

## Architecture

`Excel or Google Sheets → pandas → deterministic classification → DeepSeek (or fallback template) → preview → Gmail API (opt-in) → SQLite dispatch log`

**Default is PREVIEW ONLY. The project never emails mock-data owners.** Even in send mode, messages go **only** to `TEST_RECIPIENT`, which must be an address you control.

## Quick start (local, no accounts or API required)

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
python main.py --source excel --period 2026-W41
pytest -q
```

Open generated `previews/*.txt` files. Each email gets a deterministic fallback if `DEEPSEEK_API_KEY` is not supplied, so the starter works offline after dependencies are installed.

## Connect DeepSeek

Set `DEEPSEEK_API_KEY` in `.env`. The starter uses DeepSeek's OpenAI-compatible endpoint at `https://api.deepseek.com` and model `deepseek-chat` by default. It includes basic checks for classification, revenue and orders. AI output should still be manually reviewed before production use.

## Send a test email from your Gmail account

1. In Google Cloud, enable Gmail API; configure OAuth consent; create a **Desktop application** OAuth client and download its JSON as `client_secret.json` (never commit it).
2. Run `python gmail_auth.py` locally. Sign in to the EXACT Gmail account you want to send from; it writes `token.json`. The sender depends on which Google account grants OAuth authorization.
3. In `.env`, set `TEST_RECIPIENT=your-real-email@example.org` and `SEND_ENABLED=true`.
4. Run `python main.py --source excel --period 2026-W41 --send`.
5. Inspect `dispatch_log.sqlite3` for `SENT`, `FAILED`, or `PREVIEW_ONLY`. Avoid using the same week twice in send mode; sent items are skipped.

**Caution:** Enabling send delivers one email per hotel to your test address (e.g. 10 messages). Never commit OAuth credentials or API keys. If your Workspace account restricts OAuth, choose an authorized account or use a permitted provider.

## Read live Google Sheets

1. Set `DATA_SOURCE=sheets`, `GOOGLE_SHEET_ID=...`, `GOOGLE_SHEET_TAB=Sheet1`.
2. Create a Google Cloud service account with Sheets read access. Share the spreadsheet with the service account's email.
3. Locally set `GOOGLE_SERVICE_ACCOUNT_FILE=private-service-account.json`. In GitHub Actions, set `GOOGLE_SERVICE_ACCOUNT_JSON` as a repository secret instead.
4. Run `python main.py --source sheets --period 2026-W41`.

## Scheduled automation

`.github/workflows/weekly.yml` is a safe **Monday 09:00 Kuala Lumpur time preview-only** example. Add repository secrets `GOOGLE_SHEET_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`, and optionally `DEEPSEEK_API_KEY`. GitHub Actions uploads preview emails as artifacts. Scheduled executions can be delayed by GitHub.

**Important production limitation:** `Sheet1` has **no date column**. Scheduled runs read the same snapshot unless the source sheet is manually refreshed with last week's rows. `REPORT_PERIOD` is a label, *not* a temporal filter. Before claiming true hands-free reporting, add a date field (or a weekly export workflow), then implement a previous-week date filter and freshness check. The supplied workbook is mock data, not a weekly time series.

**Another limitation:** SQLite stored on a GitHub-hosted runner is ephemeral. This starter's default Actions workflow only previews. Before enabling unattended sending, move the idempotency log to persistent storage (e.g., a dedicated Google Sheets dispatch-log tab or hosted database) and ensure retry/failure handling. Do not just add `--send` to the scheduled workflow.

## Threshold explanation (for assignment write-up)

**Doing Well** if a hotel's revenue **and** orders are at or above the median across hotels in the *same supplied snapshot*; otherwise **Needs Improvement**. This is a transparent relative baseline, **not** proof of attaining goals or improvement versus last week. AOV = revenue / orders, undefined for zero orders. All classifications come from Python (not DeepSeek). Since the file contains no target or previous-week data, no targets or growth trends are invented. Currency is unspecified in the workbook.

## AI prompt design

The DeepSeek prompt contains hotel name, reporting period label, computed revenue, orders, AOV, peer medians and the classification. The system prompt prohibits invented numbers/targets/causes and asks for one actionable suggestion. If the API fails or basic sanity checks fail, a deterministic template is used. For a production-grade version, validate a structured model response and restrict claims to provided data.

## Files

- `main.py`: run the workflow
- `src/source.py`: Excel/Google Sheets adapter
- `src/analytics.py`: classification rules and metrics
- `src/ai.py`: DeepSeek prompt + fallback
- `src/mailer.py`, `gmail_auth.py`: Gmail OAuth/send
- `src/logging_db.py`: local SQLite dispatch log
- `tests/`: minimal analytics tests
- `data/hotel_mock_data.xlsx`: your attached mock workbook (original copy)

## Suggested demo

Run preview and show 2–3 generated emails, point to the Python threshold calculation, explain the lack of dates/targets, then run `--send` only after testing OAuth and setting the test destination. In the interview, separate what **works now** (snapshot reporting and preview/test send) from what still needs **production hardening** (freshness, durable logs, alerting).
