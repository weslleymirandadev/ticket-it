# ticket-it

A small support-ticket triage service built with LangChain and FastAPI.
Send a ticket in, get back a category, priority, sentiment and a route.
It runs offline with no API key, so you can try it right away.

## Features

- Asks an LLM to classify the ticket and write a reply, then checks the JSON.
- Decides between `escalation` (a human handles it) and `auto_reply`.
- Remembers how many tickets it has seen and how many were escalated.
- Works offline with simple keyword rules when `OPENAI_API_KEY` is not set.

## Install

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Start the server:

```bash
uvicorn app.main:app --reload
```

Classify a ticket:

```bash
curl -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"ticket": "I was charged twice, please refund me.", "channel": "email"}'
```

Check the counters:

```bash
curl http://127.0.0.1:8000/stats
```

You can also run `python demo.py` to send a few sample tickets through the code.

## How it works

The prompt asks the model for a JSON object with `category`, `priority`,
`sentiment`, `summary`, `suggested_reply` and `needs_human`. The chain is just
`prompt | llm | parser`, where the parser turns that JSON into a `Triage` model.
After that a plain `if` decides the route: a `p1` priority or `needs_human`
goes to a human queue, everything else gets the suggested reply. If there is no
API key, a small fake model returns a JSON object built from keyword rules
instead, so the same chain and endpoints still run.

## Tests

```bash
python -m pytest tests -q
```

## License

MIT
