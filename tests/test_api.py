from fastapi.testclient import TestClient

from app.main import STATS, app

client = TestClient(app)


def setup_function():
    STATS["total"] = 0
    STATS["escalated"] = 0


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_feature_request_gets_auto_reply():
    r = client.post("/triage", json={"ticket": "It would be nice to add dark mode.", "channel": "web"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"] == "auto_reply"
    assert body["triage"]["category"] == "feature_request"
    assert body["reply"]


def test_refund_is_escalated():
    r = client.post("/triage", json={"ticket": "I was charged twice, please refund me."})
    body = r.json()
    assert body["route"] == "escalation"
    assert body["triage"]["category"] == "billing"
    assert body["queue"] == "billing-ops"


def test_outage_is_p1():
    r = client.post("/triage", json={"ticket": "PRODUCTION IS DOWN! URGENT outage, we lost data."})
    body = r.json()
    assert body["triage"]["priority"] == "p1"
    assert body["route"] == "escalation"
    assert body["sla_minutes"] == 15


def test_empty_ticket_is_rejected():
    assert client.post("/triage", json={"ticket": ""}).status_code == 422


def test_stats_counts():
    client.post("/triage", json={"ticket": "URGENT outage, nothing works!"})
    client.post("/triage", json={"ticket": "How do I change my email?"})
    assert client.get("/stats").json() == {"total": 2, "escalated": 1}
