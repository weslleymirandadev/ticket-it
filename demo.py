"""Run a few sample tickets through the triage chain.

    python demo.py
"""

from app.triage import triage_ticket

TICKETS = [
    ("email", "PRODUCTION IS DOWN! Nobody can log in and we are losing data. URGENT!!"),
    ("chat", "I was charged twice for my Pro plan. Please refund the duplicate charge."),
    ("email", "It would be nice if you could add a dark mode. Thanks!"),
    ("web", "Password reset link is broken and I am locked out of my account."),
]

for channel, ticket in TICKETS:
    result = triage_ticket(ticket, channel)
    print(f"[{channel}] {ticket}")
    print(f"  category    : {result.triage.category}")
    print(f"  priority    : {result.triage.priority}")
    print(f"  sentiment   : {result.triage.sentiment}")
    print(f"  summary     : {result.triage.summary}")
    print(f"  route       : {result.route}")
    if result.route == "escalation":
        print(f"  queue       : {result.queue} (SLA {result.sla_minutes} min)")
    else:
        print(f"  reply       : {result.reply}")
    print()
