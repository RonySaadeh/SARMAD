# What SARMAD can do right now (v0)

This is a living snapshot of what actually works today, not the long-term
vision. Update it whenever a capability is added or a limitation is lifted.

## You can

- **Wake it by voice.** Say "SARMAD" or "SARMAD, Daddy's home" near your
  laptop's mic and it starts listening — no touching the keyboard.
- **Have a spoken conversation.** It transcribes what you say, replies out
  loud — short and to the point, no preamble — and remembers the conversation
  and any facts it's told to remember (`remember: I prefer window seats`)
  across sessions.
- **Switch models by voice.** Everyday questions run on a fast/cheap model
  automatically. Say "use Opus" or "use your smartest model" before (or as
  part of) a hard request and it switches for real reasoning work; say "use
  your fast model" or "go back to normal" to switch back. It stays on
  whichever you last picked until you change it again.
- **Say "create a project for X"** and get a real scaffolded folder on disk
  (files + `git init`) under your configured `Projects/` folder — SARMAD picks
  a reasonable stack and writes starter code from your description.
- **Say "fix X in [project]"** and it delegates to the actual Claude Code CLI,
  scoped to that project's folder, to read/edit files and run commands until
  it's done — real fixes, not just scaffolding. Requires `claude` installed
  and logged in on this machine, and `ENABLE_CODING_AGENT=true` (off by
  default — see limitation below).
- **Say "check my email"** and it reads recent inbox messages (sender,
  subject, snippet) over IMAP. Say "reply to X and say Y" and it composes the
  reply — opened as a draft in your mail client by default, or sent directly
  via SMTP if you've set `ENABLE_EMAIL_SEND=true`.
- **Open apps, URLs, or scripts you've pre-registered.** "Open VS Code" /
  "open Chrome" works for anything listed in `apps.json`; "run
  backup.bat" works for anything you've placed in `./scripts`.
- **Start a restaurant reservation.** "Book a table at [restaurant] for 4 at
  7pm on Friday" opens a pre-filled OpenTable search in your browser — you
  still click to confirm (see limitation below).
- **See what it's doing.** A small always-on-top HUD window shows a glowing
  status core (idle / listening / thinking / speaking) plus the last thing
  you said and its reply, as captions.
- **Ask it to look at something through your webcam.** "SARMAD, look at this
  and tell me if the wiring is right" — it captures one frame and inspects it
  with Claude's vision. Only fires when you explicitly ask (see limitation
  below), and the frame is never saved to disk.
- **Optionally, shut down / restart / sleep / lock your laptop by voice** —
  but only if you've explicitly set `ENABLE_POWER_ACTIONS=true` in `.env`
  (off by default).

## You cannot yet

- **It doesn't actually book the reservation.** No restaurant has a public
  booking API and SARMAD doesn't have your OpenTable login or a payment
  method — it gets you one click away, you finish it. True automated booking
  is a deliberately separate, later milestone (browser automation with saved
  credentials).
- **No calendar, messaging, or general web search.** SARMAD can't check your
  schedule, use messaging apps, or look things up online yet — it only acts
  through the specific tools listed above (email is now covered, see "You can").
- **`fix_project` trusts the model with a real shell, scoped only by working
  directory.** It's off by default. Once enabled, a command it runs isn't
  sandboxed against absolute paths — the trust boundary is the model itself,
  same as running any coding agent yourself, not an OS-level sandbox.
- **Email autonomy is opt-in.** By default SARMAD only drafts replies for you
  to review and send; enabling `ENABLE_EMAIL_SEND` means a misheard word could
  send something you didn't intend, with no confirmation step.
- **No arbitrary system control.** It can only open apps/scripts you've
  explicitly whitelisted — it will refuse to open or run anything not listed
  in `apps.json` / `./scripts`, and refuses power actions unless you opt in.
  This is intentional, not a bug to work around.
- **Windows + one machine only.** It's built for a single Windows laptop with
  a local mic/speakers; there's no phone app, no remote access, and no
  multi-device sync.
- **Not truly "always on."** SARMAD only runs while the terminal process /
  background task is alive. It restarts if the process crashes only if you've
  set up Task Scheduler to relaunch it — there's no watchdog yet.
- **No barge-in.** You can't interrupt it mid-sentence by talking over it —
  it finishes speaking, then listens again.
- **Wake word is basic.** It's a small offline model tuned to a short
  vocabulary; expect occasional false triggers or misses, especially in a
  noisy room or with background music/TV.
- **Single user, no permissions model.** Anyone within earshot who says the
  wake phrase can issue commands — there's no voice ID or PIN.
- **Local STT is slower than cloud.** Using `faster-whisper` locally (chosen
  to avoid needing an OpenAI key) adds a few seconds of latency per request,
  more on an older/weaker CPU.
- **Model switching is keyword-based, not automatic.** SARMAD doesn't judge
  whether a task is actually hard — it only switches models when you say a
  recognized phrase ("use Opus", "use your smartest model", etc.). It won't
  notice on its own that a question deserved the smarter model.
- **Camera is a single still frame, not live video.** It can't watch
  continuously or track motion — each "look at this" captures one snapshot.
  The image is sent to Anthropic's API as part of that request (like any
  Claude vision use), and there's no on-screen indicator besides the HUD
  showing "thinking" — so treat the wake phrase itself as the on/off switch.

## Where this is going

See the "What's next" section in `README.md` for the current shortlist
(calendar, a persistent background service, real reservation automation).
Capabilities move from "cannot yet" to "you can" here as they ship — this
file should always describe the current `main` branch, not the plan.
