"""SARMAD's reasoning core: a Claude tool-calling loop over memory + local tools."""

import re

import anthropic

from sarmad import config, memory
from sarmad.tools import coding_agent, email_tool, project_scaffold, reservations, system_control, vision

# Which model handles a request: FAST_MODEL by default for everyday chat, or
# whichever model the user last explicitly named ("use Opus", "use your
# smartest model", "go back to your fast model"). The choice persists across
# turns until the user names a different one.
_MODEL_ALIASES = {
    "fast": config.FAST_MODEL,
    "quick": config.FAST_MODEL,
    "simple": config.FAST_MODEL,
    "haiku": config.FAST_MODEL,
    "default": config.FAST_MODEL,
    "normal": config.FAST_MODEL,
    "sonnet": "claude-sonnet-5",
    "opus": config.SMART_MODEL,
    "smart": config.SMART_MODEL,
    "smartest": config.SMART_MODEL,
    "best": config.SMART_MODEL,
    "harder": config.SMART_MODEL,
    "hardest": config.SMART_MODEL,
    "complex": config.SMART_MODEL,
    "fable": "claude-fable-5",
}

_MODEL_HINT_PATTERN = re.compile(
    r"\b(?:use|switch to|switch back to|go back to)\s+(?:your\s+|the\s+)?"
    r"(fast|quick|simple|haiku|sonnet|opus|smart(?:est)?|best|harder|hardest|complex|fable|default|normal)"
    r"(?:\s+model)?\b",
    re.IGNORECASE,
)


def _resolve_model(user_text: str) -> str:
    match = _MODEL_HINT_PATTERN.search(user_text)
    if match:
        model = _MODEL_ALIASES[match.group(1).lower()]
        memory.remember_fact("active_model", model)
        return model
    return memory.recall_fact("active_model") or config.FAST_MODEL


SYSTEM_PROMPT = """You are SARMAD, a personal voice assistant running locally on your
user's Windows laptop. This gets read aloud by text-to-speech, so be short and
direct — one to three sentences, almost never more:
- No introductions or preamble ("Sure, I can help with that", "Great question").
- No summarizing what you're about to say or what you just did — just say it.
- No markdown, no bullet points, no lists of options unless asked to enumerate.
- Answer the question or report the result. Nothing else.
- If you did something with a tool, say what happened in one short sentence,
  not a walkthrough of the steps you took.

You have real autonomy. For routine, reversible things — scaffolding or fixing
a project, opening an app, checking email, drafting a reply, looking at
something with the camera — decide and act instead of asking permission. Only
ask a short clarifying question when a required detail is genuinely missing
(which restaurant, what to name a project, which project to fix) or the action
is hard to reverse and it's unclear the user meant to go all the way (actually
sending an email, spending money, shutting the machine down).

Only call look_at_camera when the user explicitly asks you to look at, check,
inspect, or see something through the camera — never turn it on unprompted.

Only call reply_email when the user has actually asked you to reply or send
something — never send or draft a message unprompted.

Known facts about your user (from memory):
{facts}
"""

TOOLS = [
    {
        "name": "create_project",
        "description": "Scaffold a brand new software project on disk from a name and description.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short project name"},
                "description": {"type": "string", "description": "What the project should do"},
            },
            "required": ["name", "description"],
        },
    },
    {
        "name": "open_app",
        "description": "Open an application registered in apps.json by name.",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "open_url",
        "description": "Open a URL in the default web browser.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "run_script",
        "description": "Run a script by filename that has been registered in the local ./scripts folder.",
        "input_schema": {
            "type": "object",
            "properties": {"script_name": {"type": "string"}},
            "required": ["script_name"],
        },
    },
    {
        "name": "power_action",
        "description": "Shutdown, restart, sleep, or lock the computer. Disabled unless the user has opted in.",
        "input_schema": {
            "type": "object",
            "properties": {"action": {"type": "string", "enum": ["shutdown", "restart", "sleep", "lock"]}},
            "required": ["action"],
        },
    },
    {
        "name": "draft_reservation",
        "description": "Prepare a restaurant reservation by opening a pre-filled booking search for the user to confirm.",
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant": {"type": "string"},
                "party_size": {"type": "integer"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM, 24h"},
                "city": {"type": "string"},
            },
            "required": ["restaurant", "party_size", "date", "time"],
        },
    },
    {
        "name": "look_at_camera",
        "description": (
            "Capture a single frame from the webcam to visually inspect something the user "
            "is showing you. Only use this when the user explicitly asks you to look at, "
            "check, inspect, or see something."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus": {"type": "string", "description": "What to look for or pay attention to in the frame"}
            },
            "required": [],
        },
    },
    {
        "name": "fix_project",
        "description": (
            "Fix a bug or implement a change in an existing project SARMAD created, by delegating "
            "to the Claude Code CLI scoped to that project's folder. Can take several minutes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "The project's folder name under Projects/"},
                "instructions": {"type": "string", "description": "What to fix, add, or change"},
            },
            "required": ["project_name", "instructions"],
        },
    },
    {
        "name": "check_inbox",
        "description": "Check recent email (unread by default) and return sender, subject, and a snippet for each.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max emails to return, default 5"},
                "unread_only": {"type": "boolean", "description": "Default true"},
            },
            "required": [],
        },
    },
    {
        "name": "reply_email",
        "description": (
            "Reply to or compose an email. Only call this when the user has explicitly asked you "
            "to reply to or send something."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "remember",
        "description": "Save a durable fact or preference about the user for future conversations.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
            "required": ["key", "value"],
        },
    },
]

_DISPATCH = {
    "create_project": lambda i: project_scaffold.create_project(i["name"], i["description"]),
    "open_app": lambda i: system_control.open_app(i["app_name"]),
    "open_url": lambda i: system_control.open_url(i["url"]),
    "run_script": lambda i: system_control.run_script(i["script_name"]),
    "power_action": lambda i: system_control.power_action(i["action"]),
    "draft_reservation": lambda i: reservations.draft_reservation(
        i["restaurant"], i["party_size"], i["date"], i["time"], i.get("city", "")
    ),
    "look_at_camera": lambda i: vision.capture_and_look(),
    "fix_project": lambda i: coding_agent.fix_project(i["project_name"], i["instructions"]),
    "check_inbox": lambda i: email_tool.check_inbox(i.get("limit", 5), i.get("unread_only", True)),
    "reply_email": lambda i: email_tool.reply_email(i["to"], i["subject"], i["body"]),
}


def _remember(inputs: dict) -> dict:
    memory.remember_fact(inputs["key"], inputs["value"])
    return {"ok": True}


_DISPATCH["remember"] = _remember


def _run_tool(name: str, inputs: dict) -> dict:
    try:
        return _DISPATCH[name](inputs)
    except Exception as exc:  # noqa: BLE001 - surfaced back to the model, not swallowed
        return {"ok": False, "error": str(exc)}


def process(user_text: str) -> str:
    """Run one user turn through Claude, executing any tool calls, and return the reply text."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    memory.save_message("user", user_text)
    model = _resolve_model(user_text)
    facts = memory.all_facts()
    facts.pop("active_model", None)
    system_prompt = SYSTEM_PROMPT.format(facts=facts or "(none yet)")
    messages = memory.recent_history(limit=20)

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=300,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if block.type == "text").strip()
            memory.save_message("assistant", final_text)
            return final_text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = _run_tool(block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": _tool_result_content(block, result)}
            )
        messages.append({"role": "user", "content": tool_results})


def _tool_result_content(block, result: dict):
    """Most tools return plain text, but a camera capture needs to hand Claude
    an actual image content block rather than a stringified dict."""
    image_b64 = result.get("image_b64")
    if not image_b64:
        return str(result)

    focus = block.input.get("focus", "a general inspection")
    return [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": result["media_type"], "data": image_b64},
        },
        {"type": "text", "text": f"Captured webcam frame. Focus: {focus}"},
    ]
