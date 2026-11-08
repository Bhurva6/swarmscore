"""Transcript ingestion.

Canonical event schema (JSONL, one event per line):
  {
    "ts":        float,           # epoch seconds (or any monotonically increasing number)
    "agent":     str,             # the agent's claimed identity for THIS event
    "agent_id":  str | null,      # stable underlying identity if the platform provides one
    "kind":      "message" | "tool_call" | "file_write" | "log_edit" | "join" | "rename",
    "to":        str | null,      # recipient agent / channel / tool name
    "channel":   str | null,      # logical channel (e.g. "shared-dir", "dm", "tasks")
    "text":      str,             # message or payload text
    "tags":      [str]            # optional free-form labels from the source
  }

Adapters convert a source dump into this schema. Anything that can produce
this schema can be scored; SwarmScore never touches the network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Iterable, Iterator, Optional


@dataclass
class Event:
    ts: float
    agent: str
    kind: str
    agent_id: Optional[str] = None
    to: Optional[str] = None
    channel: Optional[str] = None
    text: str = ""
    tags: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_dict(d: dict) -> "Event":
        return Event(
            ts=float(d.get("ts", 0.0)),
            agent=str(d.get("agent", "unknown")),
            kind=str(d.get("kind", "message")),
            agent_id=d.get("agent_id"),
            to=d.get("to"),
            channel=d.get("channel"),
            text=str(d.get("text", "")),
            tags=list(d.get("tags", [])),
        )


def read_jsonl(path: str) -> Iterator[Event]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield Event.from_dict(json.loads(line))


def write_jsonl(path: str, events: Iterable[Event]) -> int:
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for ev in events:
            fh.write(ev.to_json() + "\n")
            n += 1
    return n


def adapt_ai_village(records: Iterable[dict]) -> Iterator[Event]:
    """Best-effort adapter for AI Digest AI Village message dumps.

    The HuggingFace dataset is gated; once access is granted, point this at the
    dump and adjust the key guesses here to the real column names. Unknown keys
    are tolerated; nothing crashes on a missing field.
    """
    for r in records:
        yield Event(
            ts=float(r.get("ts") or r.get("timestamp") or r.get("created_at") or 0.0),
            agent=str(r.get("agent") or r.get("agent_name") or r.get("author") or "unknown"),
            kind=str(r.get("kind") or r.get("type") or "message"),
            agent_id=r.get("agent_id") or r.get("run_id") or r.get("author_id"),
            to=r.get("to") or r.get("recipient") or r.get("channel"),
            channel=r.get("channel") or r.get("room"),
            text=str(r.get("text") or r.get("content") or r.get("body") or ""),
            tags=list(r.get("tags") or []),
        )
