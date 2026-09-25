"""Core data model: event state, issues and proposed actions.

Every capability of Bureau Agent (answering questions, reconciling payments,
fixing teams, planning a trip) reads an EventState, resolves an Issue and
produces a ProposedAction. Nothing is executed without human approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Literal, Optional

IssueStatus = Literal["open", "proposed", "needs_human", "resolved", "dismissed"]
Channel = Literal["email", "discord", "form"]
GroupKind = Literal["team", "room"]


@dataclass
class Participant:
    id: str
    name: str
    emails: list[str]
    registered_at: datetime
    skills: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    looking_for_group: bool = False


@dataclass
class Payment:
    id: str
    payer_name: str
    amount_cents: int  # money is never a float
    paid_at: datetime
    currency: str = "EUR"
    payer_email: Optional[str] = None
    reference: Optional[str] = None
    participant_id: Optional[str] = None  # None = not linked to anyone yet


@dataclass
class Group:
    id: str
    kind: GroupKind
    name: str
    members: list[str]  # participant ids
    capacity_min: int
    capacity_max: int
    declared_at: Optional[datetime] = None


@dataclass
class Message:
    id: str
    channel: Channel
    sender: str
    text: str
    received_at: datetime


@dataclass
class Rule:
    id: str       # e.g. "§3"
    title: str
    text: str
    source: str   # e.g. "rules.md"


@dataclass
class Evidence:
    source_type: str   # participant | payment | group | message | rule | travel_option | tool
    source_id: str
    description: str


@dataclass
class Issue:
    # `id` is a deterministic fingerprint (kind + subject), so re-running detection
    # maps to the same logical issue instead of creating duplicates.
    id: str
    kind: str
    blocking: bool
    title: str
    subject_ids: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    status: IssueStatus = "open"
    depends_on: list[str] = field(default_factory=list)
    resolved_by_action_id: Optional[str] = None


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""
    verified: bool = True  # False when the data source cannot confirm it (a human must check)


@dataclass
class ProposedAction:
    id: str
    event_id: str
    issue_id: str
    action_type: str  # SEND_MESSAGE | LINK_PAYMENT | MOVE_MEMBER | UPDATE_GROUPS | SELECT_TRAVEL_PLAN | ESCALATE
    title: str
    description: str
    evidence: list[Evidence] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    # Only for inferences (identity, intent, rule interpretation). Deterministic
    # facts are expressed as passed/failed checks, not as a probability.
    confidence: Optional[float] = None
    requires_approval: bool = True
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EventState:
    id: str
    name: str
    rules: list[Rule]
    deadlines: dict[str, datetime]
    settings: dict[str, Any]  # e.g. membership fee, group size limits
    participants: list[Participant]
    payments: list[Payment]
    groups: list[Group]
    messages: list[Message]
    logistics: Optional[dict[str, Any]] = None
    issues: list[Issue] = field(default_factory=list)
    actions: list[ProposedAction] = field(default_factory=list)

    def participant(self, pid: str) -> Optional[Participant]:
        return next((p for p in self.participants if p.id == pid), None)

    def issue(self, iid: str) -> Optional[Issue]:
        return next((i for i in self.issues if i.id == iid), None)
