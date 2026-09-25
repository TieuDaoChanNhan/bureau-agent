"""Keyword search over the rules / event info document, section by section."""
from __future__ import annotations

import re

import unicodedata

from ..core.models import EventState


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def sections(rules: str) -> list[tuple[str, str]]:
    parts = re.split(r"(?m)^(#{1,3} .+)$", rules)
    out: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        out.append((parts[i].lstrip("# ").strip(), parts[i + 1].strip()))
    return out


def search_rules(state: EventState, query: str, top_k: int = 3) -> list[dict]:
    terms = [t for t in re.split(r"\W+", _norm(query)) if len(t) > 2]
    scored = []
    for rule in state.rules:
        text = _norm(rule.title + " " + rule.text)
        hits = sum(text.count(t) for t in terms)
        if hits:
            scored.append((hits, rule))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"rule_id": r.id, "title": r.title, "text": r.text, "source": r.source} for _, r in scored[:top_k]]
