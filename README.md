# Skyward — AI Flight Agent

A local development project: FastAPI + LangGraph + optional Gemini, React + TypeScript, optional Duffel sandbox, and SQLAlchemy with SQLite or PostgreSQL.

**This is a working demo/sandbox starter, not a production travel agency. Every booking is simulated. It never takes payment, calls Duffel's order-creation API, or issues a ticket.** Demo flights, airline names, times, prices, and baggage allowances are invented and clearly labeled in the UI. Duffel test searches use provider sandbox data.

## Open in VS Code

Unzip the project, open the `flight-agent` folder, then open `flight-agent.code-workspace`. Or run `code flight-agent.code-workspace` from the folder if the VS Code shell command is installed. Requires Python 3.11+ and Node.js 20.19+ (Node 22+ recommended).

## Run on macOS / Linux

Terminal 1, from the project folder:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, from the project folder:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Backend API documentation: http://127.0.0.1:8000/docs.

On Windows, use `py -m venv .venv`, `.venv\Scripts\Activate.ps1`, and `Copy-Item .env.example .env`. Start the two services manually; the included VS Code tasks use macOS/Linux paths. Once dependencies are installed on macOS/Linux, use **Terminal → Run Task → Start flight agent**.

## Try it without keys

Search through the form, or send: `Find flights from Colombo to Singapore on 2026-12-10 under $400` (choose a future date). The offline parser understands `from CITY to CITY`, ISO dates, optional USD budgets, and economy/business. Supported city aliases: Colombo, Singapore, Dubai, London, Paris, Bangkok, Tokyo, Sydney, Amsterdam, Frankfurt. Three-letter IATA codes also work. It asks for clarification on missing dates/routes and unsupported requests. It is a deterministic demo parser, not an LLM.

Select **Review flight**, confirm the itinerary and reviewed total, then **Simulate booking**. The result explicitly states that no payment or ticket was created. The app supports **one adult and one-way travel**. The form uses economy; the assistant can extract other cabins with Gemini. USD budget filtering is applied only to USD offers; no currency conversion is fabricated.

## Enable Gemini

Set `GEMINI_API_KEY` in `backend/.env`. The default model is `gemini-2.5-flash`; change `GEMINI_MODEL` to another model supporting structured output if needed. Restart the backend. Gemini extracts validated search parameters; LangGraph routes to the deterministic provider search. The model has no booking/payment tool. Input is sent to Google; use invented itinerary data during development and do not paste passports or payment information into chat.

## Enable Duffel sandbox

Create a Duffel account and obtain a **test** access token. In `backend/.env`:

```dotenv
FLIGHT_PROVIDER=duffel_test
DUFFEL_ACCESS_TOKEN=duffel_test_your_token_here
```

Restart the backend. Tokens not beginning `duffel_test_` are rejected. Searches use `POST /air/offer_requests`; offer review uses `GET /air/offers/{id}` to retrieve the current offer. These network integrations require your keys and have not been exercised against a provider account in this deliverable. Bookings remain locally simulated even with Duffel sandbox enabled.

## Database

SQLite is the zero-setup default. To use local PostgreSQL:

```bash
docker compose up -d postgres
```

Set `DATABASE_URL=postgresql+psycopg://flight:flight@localhost:5432/flight` and restart. Demo quotes/bookings persist across restarts. This starter uses schema creation on startup; add migrations before evolving a production schema. Offers and quotes have expirations; duplicate booking attempts are protected by database uniqueness and idempotency keys.

## Verify

```bash
cd backend
source .venv/bin/activate
pytest -q
```

```bash
cd frontend
npm run build
```

## Project structure

- `backend/app/agent.py`: LangGraph extraction → search workflow; optional Gemini structured output.
- `backend/app/providers.py`: explicit demo inventory and Duffel test search/repricing adapter.
- `backend/app/main.py`: API, quote review, confirmation gate, simulated bookings.
- `backend/app/database.py`: persistent offers, quotes, and booking records.
- `frontend/src/App.tsx`: assistant, structured search, offer cards, review dialog, and simulation result.
- `flight-agent.code-workspace`, `.vscode/tasks.json`: VS Code workspace and run tasks.

## Before adding real bookings

Real ticket issuance is intentionally unimplemented. It requires approved provider access and payment arrangements, full passenger validation, authentication and ownership checks, secure checkout, provider-side order reconciliation, webhook verification, refunds/cancellations, rate limits, retention controls, and monitoring. A successful payment alone is not a ticket confirmation. Keep the app bound to localhost until those controls exist. Quotes are currently referenced by opaque IDs without user accounts; this is appropriate only for a local starter. The default SQLite storage and development database password are for development.

The frontend uses regular CSS rather than Tailwind to keep setup small. No paid tracing service, vector database, Redis, or cloud account is needed. LangGraph requests are stateless; persistence stores offers, quotes, and booking simulations, not conversation history. Cloud deployment, passenger forms, return/multi-city trips, and real payments are later work.

Official integration references:
- https://duffel.com/docs/api/v2/offer-requests
- https://duffel.com/docs/api/v2/offers
- https://ai.google.dev/gemini-api/docs/structured-output
- https://docs.langchain.com/oss/python/langgraph/graph-api
