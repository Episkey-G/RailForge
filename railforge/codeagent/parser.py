from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from railforge.codeagent.models import ParsedOutput


SESSION_ID_PATTERNS = [
    r"SESSION_ID:\s*([A-Za-z0-9._-]+)",
    r"Session-ID:\s*([A-Za-z0-9._-]+)",
]


def extract_session_id(text: str) -> str | None:
    for pattern in SESSION_ID_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _parse_json_object(text: str) -> Dict[str, Any]:
    payload = json.loads(text)
    return payload if isinstance(payload, dict) else {}


def _parse_json_prefix(stdout: str) -> Dict[str, Any]:
    decoder = json.JSONDecoder()
    try:
        payload, _ = decoder.raw_decode(stdout.strip())
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_fenced_json(stdout: str) -> tuple[Dict[str, Any], str]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", stdout, re.S)
    if not match:
        return {}, ""
    raw = match.group(1).strip()
    try:
        return _parse_json_object(raw), raw
    except Exception:
        return {}, raw


def _parse_json_lines(stdout: str) -> Dict[str, Any]:
    events: List[Dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = _parse_json_object(line)
        except Exception:
            continue
        if payload:
            events.append(payload)
    if not events:
        return {}
    if len(events) == 1:
        return events[0]
    return {"events": events}


def _session_id_from_structured(structured: Dict[str, Any]) -> str | None:
    if "session_id" in structured:
        return structured.get("session_id")
    events = structured.get("events")
    if isinstance(events, list):
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get("type") == "thread.started" and event.get("thread_id"):
                return event["thread_id"]
    return None


def _summary_from_structured(structured: Dict[str, Any], default: str) -> str:
    for key in ("summary", "result", "response", "message"):
        value = structured.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    events = structured.get("events")
    if isinstance(events, list):
        for event in reversed(events):
            if not isinstance(event, dict):
                continue
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()
    return default


def parse_agent_output(stdout: str, stderr: str) -> ParsedOutput:
    combined = f"{stdout}\n{stderr}"
    structured: Dict[str, Any] = {}
    summary = stdout.strip() or stderr.strip() or "empty output"
    preserve_summary = False

    stripped = stdout.strip()
    if stripped:
        try:
            structured = _parse_json_object(stripped)
        except Exception:
            structured = {}

    if not structured:
        structured, fenced_summary = _parse_fenced_json(stdout)
        if fenced_summary:
            summary = fenced_summary
            preserve_summary = True

    if not structured:
        structured = _parse_json_lines(stdout)

    if not structured:
        structured = _parse_json_prefix(stdout)

    session_id = extract_session_id(combined)
    if not session_id:
        session_id = _session_id_from_structured(structured)

    if not preserve_summary:
        summary = _summary_from_structured(structured, summary)
    return ParsedOutput(summary=summary, structured=structured, session_id=session_id)
