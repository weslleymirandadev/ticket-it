from pydantic import BaseModel, Field


class Ticket(BaseModel):
    ticket: str = Field(min_length=1, max_length=8000)
    channel: str = "email"


# Fields are plain strings on purpose. The allowed values are written in the
# prompt only: category = billing | bug | account | feature_request | other,
# priority = p1 | p2 | p3 | p4, sentiment = angry | negative | neutral | positive
class Triage(BaseModel):
    category: str
    priority: str
    sentiment: str
    summary: str
    suggested_reply: str
    needs_human: bool = False


class TriageResult(BaseModel):
    ticket_id: str
    channel: str
    route: str  # "escalation" or "auto_reply"
    triage: Triage
    queue: str = ""
    sla_minutes: int = 0
    reply: str = ""
    elapsed_ms: float = 0.0
