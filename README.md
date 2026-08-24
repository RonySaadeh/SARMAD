# SARMAD

A personal voice agent that lives on your Windows laptop. Say its wake phrase,
it listens, thinks with Claude, and talks back — and can actually act for you:
scaffold new coding projects, open apps, and start restaurant reservations.

This is **v0**: local-only, one user, running in a terminal (or as a background
process at login). It's the first step toward a fuller "handles my daily life"
agent — more capabilities get added incrementally from here.

## How it works

1. **Wake word** (`sarmad/wake_word.py`) — a small offline speech model
   ([Vosk](https://alphacephei.com/vosk/models)) listens continuously on your
   mic for "SARMAD" / "SARMAD, Daddy's home". This runs fully offline, so it's
   free and private to leave running all the time.
2. **Listen** (`sarmad/voice.py`) — once woken, SARMAD greets you out loud and
   records your spoken request, then sends it to OpenAI's Whisper API for
   accurate transcription.
3. **Think** (`sarmad/brain.py`) — your request (plus recent conversation
   history and remembered facts about you) goes to Claude, which can call
   tools to actually do things instead of just talking.
4. **Act** (`sarmad/tools/`) — Claude can:
   - `create_project` — scaffold a new project folder (files + `git init`) from
     a spoken description, under `PROJECTS_DIR`.
   - `open_app` / `open_url` / `run_script` — open whitelisted apps, URLs, or
     scripts (nothing arbitrary — see **Safety** below).
   - `draft_reservation` — open a pre-filled OpenTable search for a restaurant
     so you're one click from confirming (see limitation below).
   - `remember` — save a fact/preference so future conversations know it.
5. **Speak** (`sarmad/voice.py`) — the reply is synthesized with OpenAI TTS and
   played back through Windows.

## Setup (Windows)

1. **Python**: install Python 3.11+, then:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **API keys**: copy `.env.example` to `.env` and fill in:
   - `ANTHROPIC_API_KEY` — from https://console.anthropic.com
   - `OPENAI_API_KEY` — used for speech-to-text and text-to-speech only
3. **Wake word model**: download a small Vosk English model (e.g.
   `vosk-model-small-en-us-0.15`) from https://alphacephei.com/vosk/models,
   unzip it into the project folder, and point `VOSK_MODEL_PATH` in `.env` at
   the unzipped folder.
4. **Apps SARMAD is allowed to open**: copy `apps.json.example` to `apps.json`
   and edit the paths for apps installed on your machine.
5. **Run it**:
   ```
   python main.py
   ```
   Say "SARMAD, Daddy's home", wait for the greeting, then talk.

## Run automatically when you turn your laptop on

1. Confirm `run_sarmad.bat` works by double-clicking it.
2. Open **Task Scheduler** → *Create Task*.
3. **General**: name it "SARMAD", check "Run only when user is logged on".
4. **Triggers**: New → "At log on".
5. **Actions**: New → Program/script: full path to `run_sarmad.bat`, Start in:
   the SARMAD project folder.
6. Save. From now on, SARMAD starts listening as soon as you log in.

## Safety notes

- SARMAD can **only** open apps/scripts you explicitly list in `apps.json` /
  `./scripts` — it cannot run arbitrary commands you didn't register.
- Shutdown/restart/sleep/lock are **off by default**. Set
  `ENABLE_POWER_ACTIONS=true` in `.env` to allow them.
- Reservations aren't fully automated yet: SARMAD opens a pre-filled OpenTable
  search rather than logging in and paying on your behalf — that needs
  credential handling and is a deliberately separate, later milestone.
- Conversation history and remembered facts are stored locally in
  `sarmad_memory.db` (SQLite) — nothing is synced anywhere.

## What's next

Natural candidates for v1: calendar read/write, email drafting, a persistent
background service (instead of a visible terminal window), and real
reservation automation via browser automation with your saved logins.
