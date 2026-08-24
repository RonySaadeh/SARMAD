"""SARMAD's reasoning core: a Claude tool-calling loop over memory + local tools."""

import anthropic

from sarmad import config, memory
from sarmad.tools import project_scaffold, reservations, system_control

SYSTEM_PROMPT = """You are SARMAD, a personal voice assistant running locally on your
user's Windows laptop. You were just woken up by your wake phrase, so speak like
you're mid-conversation, not writing an email: short, warm, direct sentences,
no markdown, no bullet points — this gets read aloud by text-to-speech.

Use tools to actually take action rather than just describing what you'd do.
If a request is ambiguous (e.g. missing a date, party size, or app name), ask a
short clarifying question instead of guessing.

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
    system_prompt = SYSTEM_PROMPT.format(facts=memory.all_facts() or "(none yet)")
    messages = memory.recent_history(limit=20)

    while True:
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
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
                {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
            )
        messages.append({"role": "user", "content": tool_results})
