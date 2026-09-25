"""Load an EventState from data/<event_id>/."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .models import EventState, Group, Message, Participant, Payment, Rule
from ..tools.rules import sections

from ..config import DATA_DIR


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(f"Datetime without timezone in sample data: {value}")
    return dt


def parse_rules(text: str, source: str) -> list[Rule]:
    rules = []
    for title, body in sections(text):
        rid = title.split()[0] if title.startswith("§") else title
        rules.append(Rule(id=rid, title=title, text=body, source=source))
    return rules


def load_event(event_id: str, data_dir: Path = DATA_DIR) -> EventState:
    root = data_dir / event_id
    meta = json.loads((root / "event.json").read_text(encoding="utf-8"))

    def read(name: str) -> list[dict]:
        path = root / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    participants = [
        Participant(
            id=p["id"], name=p["name"], emails=p["emails"],
            registered_at=_dt(p["registered_at"]), skills=p.get("skills", []),
            needs=p.get("needs", []), looking_for_group=p.get("looking_for_group", False),
        )
        for p in read("participants.json")
    ]
    payments = [
        Payment(
            id=x["id"], payer_name=x["payer_name"], amount_cents=x["amount_cents"],
            currency=x.get("currency", "EUR"), paid_at=_dt(x["paid_at"]),
            payer_email=x.get("payer_email"), reference=x.get("reference"),
            participant_id=x.get("participant_id"),
        )
        for x in read("payments.json")
    ]
    groups = [
        Group(
            id=g["id"], kind=g["kind"], name=g["name"], members=g["members"],
            capacity_min=g["capacity_min"], capacity_max=g["capacity_max"],
            declared_at=_dt(g.get("declared_at")),
        )
        for g in read("groups.json")
    ]
    messages = [
        Message(id=m["id"], channel=m["channel"], sender=m["sender"], text=m["text"],
                received_at=_dt(m["received_at"]))
        for m in read("messages.json")
    ]
    rules_path = root / "rules.md"
    return EventState(
        id=event_id,
        name=meta["name"],
        rules=parse_rules(rules_path.read_text(encoding="utf-8"), "rules.md") if rules_path.exists() else [],
        deadlines={k: _dt(v) for k, v in meta.get("deadlines", {}).items()},
        settings=meta.get("settings", {}),
        participants=participants,
        payments=payments,
        groups=groups,
        messages=messages,
        logistics=meta.get("logistics"),
    )
