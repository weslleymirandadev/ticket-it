import json
import os
import time
import uuid
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate

from .models import Triage, TriageResult

SYSTEM = """You triage support tickets. Reply with JSON only, using these keys:
- category: billing, bug, account, feature_request or other
- priority: p1 (outage or data loss), p2 (blocked), p3 (degraded), p4 (question)
- sentiment: angry, negative, neutral or positive
- summary: one short sentence
- suggested_reply: a short, polite reply to the customer
- needs_human: true or false

Example: {{"category": "billing", "priority": "p2", "sentiment": "negative",
"summary": "Charged twice for Pro.", "suggested_reply": "Sorry, we refunded you.",
"needs_human": true}}"""

PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM), ("human", "Channel: {channel}\nTicket: {ticket}")]
)

SLA = {"p1": 15, "p2": 60, "p3": 480, "p4": 1440}
QUEUE = {
    "billing": "billing-ops", "bug": "engineering-oncall", "account": "identity-support",
    "feature_request": "product-feedback", "other": "general-support",
}


def get_llm():
    if os.getenv("OPENAI_API_KEY"):
        from langchain.chat_models import init_chat_model

        return init_chat_model(os.getenv("TICKET_IT_MODEL", "openai:gpt-4o-mini"))
    return offline_llm


def offline_classify(ticket: str) -> dict:
    """Fake model used when there is no API key: a few keyword rules."""
    text = ticket.lower()
    rules = [
        (("refund", "charged", "invoice", "billing", "payment"), "billing"),
        (("password", "login", "locked out", "account"), "account"),
        (("outage", "down", "error", "crash", "broken"), "bug"),
        (("feature", "add", "dark mode", "would be nice", "suggest"), "feature_request"),
    ]
    category = "other"
    for words, name in rules:
        if any(w in text for w in words):
            category = name
            break
    priority = "p4" if category in ("other", "feature_request") else "p2"
    if any(w in text for w in ("urgent", "asap", "critical", "outage", "data loss")):
        priority = "p1"
    if any(w in text for w in ("!!", "unacceptable", "furious", "terrible", "worst")):
        sentiment = "angry"
    elif any(w in text for w in ("charged", "broken", "refund", "frustrating")):
        sentiment = "negative"
    elif any(w in text for w in ("thanks", "love", "great")):
        sentiment = "positive"
    else:
        sentiment = "neutral"
    return {
        "category": category,
        "priority": priority,
        "sentiment": sentiment,
        "summary": ticket.strip().split(".")[0][:120] or "Empty ticket.",
        "suggested_reply": f"Thanks for reaching out. We logged your {category} issue as {priority.upper()}.",
        "needs_human": priority == "p1" or sentiment == "angry" or category == "billing",
    }


class OfflineLLM(BaseChatModel):
    """A fake chat model so the app runs without an API key."""

    @property
    def _llm_type(self) -> str:
        return "offline"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        ticket = messages[-1].content.split("Ticket: ", 1)[-1]
        reply = AIMessage(content=json.dumps(offline_classify(ticket)))
        return ChatResult(generations=[ChatGeneration(message=reply)])


offline_llm = OfflineLLM()

chain = PROMPT | get_llm() | JsonOutputParser()


def triage_ticket(ticket: str, channel: str = "email") -> TriageResult:
    started = time.perf_counter()
    data = chain.invoke({"ticket": ticket, "channel": channel})
    t = Triage(**data)

    route = "escalation" if t.priority == "p1" or t.needs_human else "auto_reply"
    result = TriageResult(
        ticket_id="tk_" + uuid.uuid4().hex[:12],
        channel=channel,
        route=route,
        triage=t,
        elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
    )
    if route == "escalation":
        result.queue = QUEUE.get(t.category, "general-support")
        result.sla_minutes = SLA.get(t.priority, 1440)
    else:
        result.reply = t.suggested_reply
    return result
