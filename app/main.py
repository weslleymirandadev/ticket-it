from fastapi import FastAPI

from .models import Ticket, TriageResult
from .triage import triage_ticket

app = FastAPI(title="ticket-it", version="0.1.0")

STATS = {"total": 0, "escalated": 0}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResult)
def triage(ticket: Ticket) -> TriageResult:
    result = triage_ticket(ticket.ticket, ticket.channel)
    STATS["total"] += 1
    if result.route == "escalation":
        STATS["escalated"] += 1
    return result


@app.get("/stats")
def stats():
    return STATS
