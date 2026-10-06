"""Append-only audit trail of the agent loop: output/audit_trail.json.

One JSON array of step entries. Each append rewrites the file through a temp
file + os.replace, so it is valid JSON even if the server dies mid-write, and
existing entries are never dropped (an unreadable file is set aside, not wiped).
"""

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

import db

AUDIT_PATH = db.ROOT_DIR / "output" / "audit_trail.json"
SUMMARY_CHARS = 240
_lock = threading.Lock()


def truncate(value, limit: int = SUMMARY_CHARS) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def append_entry(entry: dict) -> None:
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries: list = []
        if AUDIT_PATH.exists():
            try:
                entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                AUDIT_PATH.replace(AUDIT_PATH.with_suffix(f".corrupt-{int(time.time())}.json"))
        entries.append(entry)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, AUDIT_PATH)


class AuditRun:
    """Logs one chat turn's agent loop. The user is recorded by id only (no email/name)."""

    def __init__(self, user: dict | None, page_path: str):
        self.run_id = uuid.uuid4().hex[:12]
        self.user = f"user:{user['id']}" if user else "guest"
        self.page = page_path
        self.step_no = 0

    def log(self, step: str, **fields) -> None:
        self.step_no += 1
        append_entry({
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.run_id,
            "user": self.user,
            "page": self.page,
            "step_no": self.step_no,
            "step": step,
            "tool_name": fields.get("tool_name"),
            "args": fields.get("args"),
            "result": fields.get("result"),
            "stop_reason": fields.get("stop_reason"),
        })

    def log_request(self, request: ModelRequest) -> None:
        for part in request.parts:
            if isinstance(part, UserPromptPart):
                self.log("user_message", result=truncate(part.content))
            elif isinstance(part, ToolReturnPart):
                self.log("tool_result", tool_name=part.tool_name, result=truncate(part.model_response_str()))
            elif isinstance(part, RetryPromptPart):
                self.log("retry", tool_name=part.tool_name, result=truncate(part.model_response()))

    def log_response(self, response: ModelResponse) -> None:
        for part in response.parts:
            if isinstance(part, ToolCallPart):
                if part.tool_name.startswith("final_result"):
                    self.log("final_answer_proposed", tool_name=part.tool_name, args=truncate(part.args_as_json_str()))
                else:
                    self.log("tool_call", tool_name=part.tool_name, args=part.args_as_dict())
            elif isinstance(part, TextPart) and part.content.strip():
                self.log("model_text", result=truncate(part.content))
