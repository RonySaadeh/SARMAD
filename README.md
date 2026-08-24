# SARMAD

A personal voice agent that lives on your Windows laptop. Say its wake phrase,
it listens, thinks with Claude, and talks back — and can actually act for you:
build and fix real coding projects, check and reply to email, open apps, and
start restaurant reservations. It's built to decide and act on routine things
rather than just describe what it would do — see "You have real autonomy" in
`sarmad/brain.py`'s system prompt.

This is **v0**: local-only, one user, running in a terminal (or as a background
process at login). It's the first step toward a fuller "handles my daily life"
agent — more capabilities get added incrementally from here.

**See [CAPABILITIES.md](CAPABILITIES.md) for exactly what SARMAD can do today
and its current limitations.**

## How it works

1. **Wake word** (`sarmad/wake_word.py`) — a small offline speech model
   ([Vosk](https://alphacephei.com/vosk/models)) listens continuously on your
   mic for "SARMAD" / "SARMAD, Daddy's home". This runs fully offline, so it's
   free and private to leave running all the time.
2. **Listen** (`sarmad/voice.py`) — once woken, SARMAD greets you out loud and
   records your spoken request, then transcribes it locally with
   [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (no API key,
   runs on your CPU). Whisper auto-detects the spoken language, so English,
   Arabic, and mixed English/Arabic all work without switching a setting.
3. **Think** (`sarmad/brain.py`) — your request (plus recent conversation
   history and remembered facts about you) goes to Claude, which can call
   tools to actually do things instead of just talking. Everyday questions
   run on `FAST_MODEL` (cheap and quick); say "use Opus" / "use your smartest
   model" for a hard task and it switches to `SMART_MODEL`, staying there
   until you say "use your fast model" / "go back to normal".
4. **Act** (`sarmad/tools/`) — Claude can:
   - `create_project` — scaffold a new project folder (files + `git init`) from
     a spoken description, under `PROJECTS_DIR`.
   - `fix_project` — fix a bug or add something to a project SARMAD already
     created, by delegating to the **Claude Code CLI** itself (`claude`)
     scoped to that project's folder — real file editing and command
     execution, not a smaller reimplementation. Off by default — see
     **Safety** below.
   - `check_inbox` / `reply_email` — read recent email over IMAP and reply.
     Replying opens a pre-filled draft in your mail client by default; see
     **Safety** below for the fully-automated option.
   - `check_calendar` / `add_calendar_event` — read upcoming events from a
     live calendar feed; adding an event opens an add-to-calendar dialog for
     you to confirm (see **Safety** below).
   - `open_app` / `open_url` / `run_script` — `open_app` finds and opens
     anything in your Start Menu by name (`apps.json` is only needed for
     custom aliases/paths); `run_script` stays whitelist-only — see
     **Safety** below.
   - `draft_reservation` — open a pre-filled OpenTable search for a restaurant
     so you're one click from confirming (see limitation below).
   - `look_at_camera` — capture one webcam frame and hand it to Claude's
     vision to inspect (e.g. "look at this circuit board and tell me if
     anything looks wrong"). Only fires when you explicitly ask — see
     **Safety** below.
   - `remember` — save a fact/preference so future conversations know it.
5. **Speak** (`sarmad/voice.py`) — the reply is synthesized with
   [edge-tts](https://github.com/rany2/edge-tts) (free Microsoft Edge voices,
   no API key) and played back through Windows. It automatically switches to
   an Arabic voice (`ARABIC_TTS_VOICE`) when the reply contains Arabic script,
   so a bilingual conversation sounds right in both languages.
6. **Show** (`sarmad/hud.py`, `sarmad/assets/hud.html`) — a small always-on-top,
   frameless HUD window with a glowing JARVIS-style arc-reactor core. It
   pulses faster and brightens while listening/thinking/speaking, and shows
   the last thing you said and SARMAD's reply as on-screen captions.

Nothing but Claude (the "brain") costs money — speech-to-text and
text-to-speech are both free and local/no-key.

## Setup (Windows)

1. **Python**: install Python 3.11+, then:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **API key**: copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY`
   from https://console.anthropic.com. Speech-to-text and text-to-speech are
   free/local, so no other key is needed.
3. **Wake word model**: download a small Vosk English model (e.g.
   `vosk-model-small-en-us-0.15`) from https://alphacephei.com/vosk/models,
   unzip it into the project folder, and point `VOSK_MODEL_PATH` in `.env` at
   the unzipped folder.
4. **Apps** (optional): `open_app` already searches your Start Menu
   automatically, so most installed apps work with no setup. Only copy
   `apps.json.example` to `apps.json` if you want a custom alias or an app
   that isn't in your Start Menu.
5. **Calendar** (optional): set `CALENDAR_ICS_URL` in `.env` to your
   calendar's ICS feed URL (for Google Calendar: Settings > your calendar >
   "Secret address in iCal format") to enable `check_calendar`.
6. **Fixing/extending projects** (optional): install the
   [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) on this
   machine and run `claude login` (this is a separate login from any other
   Claude Code session you use elsewhere — including for GitHub access, if
   you want `fix_project` able to push/open PRs). Then set
   `ENABLE_CODING_AGENT=true` in `.env`.
7. **Email** (optional): set `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD` in
   `.env` (an app password, not your real password — see the comments in
   `.env.example` for Gmail/Outlook/Yahoo specifics) to enable `check_inbox`
   and `reply_email`.
8. **HUD window**: the visual HUD uses the Microsoft Edge WebView2 runtime,
   which ships pre-installed on current Windows 10/11 — nothing to install in
   most cases. If the HUD window fails to open, install it from
   https://developer.microsoft.com/microsoft-edge/webview2, or set
   `ENABLE_HUD=false` in `.env` to run terminal-only.
9. **Run it**: (the first run downloads the local whisper model from Hugging
   Face automatically — needs internet once, then it's cached and works
   offline)
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

- `open_app` can open **anything findable in your Start Menu**, not just a
  whitelist — opening an app is low-risk, so this trades the extra safety of
  a manual list for not having to register every app yourself. `run_script`
  and power actions are a different risk category and stay gated: scripts
  must be explicitly registered under `./scripts`, and shutdown/restart/
  sleep/lock are **off by default** (`ENABLE_POWER_ACTIONS=true` to allow
  them).
- `add_calendar_event` never writes to your calendar directly — it opens a
  real `.ics` file, which launches your default calendar app's own "add
  event" dialog for you to confirm, the same prepare-then-confirm pattern
  used for reservations and email.
- `fix_project` is **off by default** (`ENABLE_CODING_AGENT=false`) because it
  runs the Claude Code CLI with permission prompts bypassed so it can work
  unattended. It's scoped to one project's folder via its working directory,
  but a shell command it runs isn't sandboxed against absolute paths — the
  trust boundary here is the model, the same as running any coding agent
  yourself. Turn it on once you're comfortable with that.
- Emailing defaults to **drafting, not sending**: `reply_email` opens a
  pre-filled draft in your mail client and you hit send. Set
  `ENABLE_EMAIL_SEND=true` in `.env` to let SARMAD send via SMTP directly with
  no confirmation step — the system prompt restricts it to cases where you
  explicitly asked for a reply/send, but a misheard transcription could still
  send something you didn't mean, so only enable this once you trust it.
- Reservations aren't fully automated yet: SARMAD opens a pre-filled OpenTable
  search rather than logging in and paying on your behalf — that needs
  credential handling and is a deliberately separate, later milestone.
- Conversation history and remembered facts are stored locally in
  `sarmad_memory.db` (SQLite) — nothing is synced anywhere.
- The camera is only opened when Claude calls `look_at_camera`, which the
  system prompt restricts to cases where you explicitly asked to look at,
  check, or inspect something — it's never triggered proactively. The
  captured frame is sent to Anthropic's API as part of that one request (like
  any Claude vision use) and is not saved to disk or kept in memory storage.

## What's next

Natural candidates for v1: real calendar write access (not just an ICS-based
add-event draft), recurring-event support, a persistent background service
(instead of a visible terminal window), and real reservation automation via
browser automation with your saved logins.
