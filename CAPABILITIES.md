# What SARMAD Can Do (v0)

Living snapshot of `main` — update this whenever a capability changes.

## Capabilities

| Say | What happens | Needs |
|---|---|---|
| "SARMAD, Daddy's home" | Wakes it up | — |
| Just talk | Chat, remembers what you tell it to remember | — |
| "Use Opus" / "use your fast model" | Switch model for hard vs. simple tasks | — |
| "Create a project for X" | Scaffolds a new project folder + `git init` | — |
| "Fix X in [project]" | Edits/fixes an existing project via the Claude Code CLI | `ENABLE_CODING_AGENT=true`, `claude` CLI installed |
| "Check my email" / "reply to X" | Reads inbox; drafts or sends a reply | `EMAIL_ADDRESS` + `EMAIL_APP_PASSWORD` |
| "Check my calendar" / "add a meeting" | Reads upcoming events; drafts new ones | `CALENDAR_ICS_URL` |
| "Search for X" / "what's the best..." | Live web search — research, products, prices, news | — |
| "Find/play a video/song" / "open X" | Searches, then opens the result (YouTube, a product page, etc.) | — |
| "Message X on WhatsApp: ..." | Opens WhatsApp with the message pre-filled to send | Logged into WhatsApp Web/Desktop |
| "Open Chrome" / "open [app]" | Opens almost any installed app | — |
| "Book a table at X" | Opens a pre-filled OpenTable search | — |
| "Look at this" | Inspects one webcam frame | — |
| "Shut down" / "lock" / etc. | Power actions | `ENABLE_POWER_ACTIONS=true` |
| Speak Arabic or English | Understood and answered in kind | — |

A small HUD window shows idle/listening/thinking/speaking and the last
exchange as captions.

## Limits

- **Reservations** — opens a search, doesn't book (no login/payment).
- **Calendar** — read + "confirm to add," not real write access; one calendar
  only; recurring events may not expand.
- **Coding agent** — real shell access inside the project folder, not
  sandboxed against absolute paths; trust it like any coding agent.
- **Email auto-send** — off by default; once on, no confirmation step.
- **Apps** — fuzzy-matched by name, could occasionally open the wrong one.
- **WhatsApp only, and drafts rather than sends** — you still hit send;
  other messaging apps aren't wired up yet.
- **"Play music" opens search results, doesn't queue playback** — you still
  click play; no Spotify/YouTube account integration yet.
- **Windows + one laptop only** — no phone app, no sync.
- **Not always-on** — needs the process running (Task Scheduler helps).
- **No barge-in** — can't interrupt it mid-sentence.
- **Wake word is English-only** ("SARMAD" itself); the conversation after
  that is bilingual.
- **Arabic voice is picked by script, not real language detection** —
  Arabizi (Arabic in Latin letters) gets mispronounced.
- **Single user, no voice ID** — anyone in earshot can give commands.
- **Local speech-to-text** is a few seconds slower than cloud.
- **Model switching is manual** — SARMAD won't upgrade itself for a hard
  question unless you say so.
- **Camera is one still frame per request**, not continuous video.

## Next

Real calendar write access, recurring events, a background service, real
reservation booking.
