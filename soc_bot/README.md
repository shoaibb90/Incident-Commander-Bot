# 🛡️ SOC Cyber Defense Commander — Telegram Bot

A multi-user, role-based Telegram bot for running a mini Security Operations
Center: log incidents, run a rule-based detection engine over pasted logs,
investigate, assign, and generate downloadable incident reports.

## Features

- **Multi-user role system**: Admin / Analyst / Viewer / Pending, enforced
  on every action (not just hidden buttons — the backend checks too).
- **First user auto-bootstrap**: the first person to `/start` the bot
  becomes Admin automatically. Everyone after that starts as `pending`
  until an Admin approves them.
- **Incident management**: create, list (filter by status), view detail,
  investigate, add notes, assign to self, mark resolved, delete (admin only).
- **Detection engine**: paste raw log text and it's scanned against rules for
  brute force logins, port scans, SQL injection, download-and-execute
  payloads, base64-encoded payloads, privilege escalation, and known scanner
  tools (sqlmap, nikto, etc). Findings can become an incident with one tap.
- **Reports & dashboard**: live stats by status/severity, and a downloadable
  `.txt` incident report with full investigation timeline.
- **Audit log**: every sensitive action (role changes, approvals, deletes)
  is recorded and viewable by admins.
- **All-button UI**: every action is a tappable inline button — no need to
  remember commands.

## Setup

1. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram.
2. Copy `.env.example` to `.env` and paste your token in:
   ```
   cp .env.example .env
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run it:
   ```
   python main.py
   ```
5. Open your bot in Telegram and send `/start`. You'll automatically become
   Admin. Anyone else who starts the bot afterward will be `pending` until
   you approve them from the Admin Panel.

## Project structure

```
soc_bot/
├── main.py            # entry point, starts polling
├── config.py           # settings, role levels, emoji maps
├── database.py          # SQLite schema + all data access
├── detection.py         # rule-based log analysis engine
├── roles.py            # role-check decorator
├── states.py            # FSM states for multi-step flows
├── keyboards.py          # every inline keyboard/button
└── handlers/
    ├── start.py         # onboarding, main menu, profile
    ├── incidents.py       # create/view/investigate/resolve/delete
    ├── scan.py           # detection scan flow
    ├── admin.py          # approvals, role management, audit log
    └── reports.py         # dashboard stats + report file generation
```

## Extending it

The detection rules live in `detection.py` as a plain list of dicts —
add a new dict with a regex pattern, severity, and threshold to add a new
detection rule with zero other changes needed.

To add a real log *source* instead of pasting logs manually, the natural
next step is a small webhook/ingestion endpoint (e.g. FastAPI) that receives
logs from a real system and calls `detection.analyze_logs()` directly,
then pushes a Telegram message to relevant analysts when something fires —
turning this from "manual paste" into a real always-on pipeline.

## Notes

- Database is a single SQLite file (`soc_commander.db`), created
  automatically on first run — easy to inspect, back up, or reset (just
  delete the file to start fresh).
- This is a defensive/detection tool: the rule engine flags patterns, it
  never generates or executes attack payloads.
