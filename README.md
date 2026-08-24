# SARMAD

Personal voice agent for Windows. Say **"SARMAD, Daddy's home"**, then talk.
Understands English and Arabic. Chats, builds/fixes code, manages email and
calendar, opens apps, and more.

v0 — local, single laptop, one user.

See **[CAPABILITIES.md](CAPABILITIES.md)** for what it can and can't do.

## Setup

**1. Install**
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2. API key** — copy `.env.example` → `.env`, set `ANTHROPIC_API_KEY`
([console.anthropic.com](https://console.anthropic.com)).

**3. Wake word model** — download a Vosk model (e.g. `vosk-model-small-en-us-0.15`)
from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models), unzip
it, set `VOSK_MODEL_PATH` in `.env` to the folder.

**4. Run**
```
python main.py
```

That's the minimum. First run downloads the speech model (~1 min, needs
internet once, then works offline).

## Optional setup

| Feature | To enable |
|---|---|
| Fix/build projects with Claude Code | Install the [Claude Code CLI](https://docs.claude.com/en/docs/claude-code), run `claude login`, set `ENABLE_CODING_AGENT=true` |
| Email (read + reply) | Set `EMAIL_ADDRESS` + `EMAIL_APP_PASSWORD` in `.env` (an app password, not your real one) |
| Calendar | Set `CALENDAR_ICS_URL` in `.env` (Google: Calendar Settings → your calendar → "Secret address in iCal format") |
| Custom app names/paths | Copy `apps.json.example` → `apps.json` and add them (most apps work without this) |
| Power actions (shutdown/lock/etc.) | Set `ENABLE_POWER_ACTIONS=true` |
| Auto-send email (skip the draft step) | Set `ENABLE_EMAIL_SEND=true` |
| Run without the HUD window | Set `ENABLE_HUD=false` |

## Run automatically at login

1. Double-click `run_sarmad.bat` to confirm it works.
2. Task Scheduler → **Create Task**.
3. General: name it "SARMAD", check "Run only when user is logged on".
4. Triggers → New → **At log on**.
5. Actions → New → Program/script: full path to `run_sarmad.bat`. Start in:
   the SARMAD folder.
6. Save.

## Safety defaults

- **Apps** — `open_app` can open anything in your Start Menu.
- **Scripts** — only files placed in `./scripts`.
- **Power actions** — off by default.
- **Email sending** — off by default; replies open as a draft instead.
- **Coding agent** — off by default; once on, it runs with permissions
  bypassed inside one project folder.
- **Camera** — only activates when you explicitly ask.
- **Calendar** — never writes directly; opens an "add event" dialog for you
  to confirm.
- **Reservations** — opens a pre-filled search; you finish booking yourself.

## What's next

Real calendar write access, recurring events, a background service (no
terminal window), and real reservation booking.
