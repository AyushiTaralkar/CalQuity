# ParcelPilot AI

**Account-Aware AI Support Agent — Evidence. Context. Action.**

ParcelPilot AI is an operational support agent that answers logistics support questions by combining retrieval-augmented generation over policy documents, live structured queries against operational data, and controlled, human-confirmed actions — all scoped to the requesting customer account.

It is not a chatbot with a knowledge base bolted on. It is an agent that investigates.

**Live demo:** https://parcelpilot-ai-ten.vercel.app

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Core Capabilities](#core-capabilities)
- [Trust & Source Authority Model](#trust--source-authority-model)
- [Security & Account Isolation](#security--account-isolation)
- [Controlled Actions](#controlled-actions)
- [Example Interactions](#example-interactions)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [What's Not Built Yet](#whats-not-built-yet)
- [Roadmap](#roadmap)

---

## Why This Exists

Support agents shouldn't need to search five systems to answer one question. In a typical logistics support workflow, the correct answer to a customer request is scattered across:

| Source | Contains |
|---|---|
| Policies | General support rules |
| Customer Contracts | Account-specific overrides |
| Orders | Live shipment state |
| Tickets | Historical context |
| Product Documentation | Known issues, operational caveats |

These sources are not equally trustworthy, not equally current, and not equally applicable to a given customer. Getting the right answer means knowing *which* source to trust, not just finding *a* source.

ParcelPilot AI encodes that judgment into the retrieval and reasoning pipeline itself, rather than leaving it to an agent's memory or a flat document search.

## What It Does

Given a natural-language question, ParcelPilot AI:

1. Determines whether the answer requires document evidence, structured operational data, or both.
2. Retrieves and ranks the relevant evidence — scoped to the requesting account.
3. Reasons across multiple sources when a single one is insufficient (e.g., contract terms vs. general policy).
4. Returns a grounded answer with explicit sources and a confidence signal.
5. If the request implies a state change (e.g., an escalation), proposes the action and waits for explicit human confirmation before executing it.

If the evidence is insufficient, it says so — and defers to a human — rather than guessing.

## Architecture

```
                ┌────────────────────┐
                │   ParcelPilot UI    │
                └──────────┬─────────┘
                           │
                ┌──────────▼─────────┐
                │     FastAPI API     │
                └──────────┬─────────┘
                           │
                ┌──────────▼─────────┐
                │  AI Agent (Gemini)  │
                └───┬──────────┬─────┘
                    │          │           │
        ┌───────────▼──┐ ┌─────▼──────┐ ┌──▼────────────┐
        │    FAISS      │ │ PostgreSQL │ │    Actions     │
        │  (semantic     │ │(structured │ │ (state-changing│
        │   retrieval)   │ │   state)   │ │   + gated)     │
        ├────────────────┤ ├────────────┤ ├────────────────┤
        │ Policies       │ │ Accounts   │ │ Escalations    │
        │ Contracts      │ │ Orders     │ │ Confirmation   │
        │ SOPs           │ │ Tickets    │ │ Ticket Updates │
        │ Product Docs   │ │            │ │                │
        └────────────────┘ └────────────┘ └────────────────┘
```

**Design principle:** the agent never has unmediated write access. Every state-changing action passes through an explicit confirmation gate before it reaches the data layer.

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| LLM | Gemini | Grounded natural-language reasoning and generation |
| Retrieval | FAISS | Fast semantic search over the document corpus |
| Embeddings | Sentence Transformers | Lightweight, local document embeddings |
| Structured data | PostgreSQL | Accounts, orders, tickets — source of truth for operational state |
| ORM | SQLAlchemy | Type-safe database access |
| Document ingestion | PyPDF | Parsing policies, contracts, SOPs, and product docs |
| API | FastAPI | Production-grade, typed API layer |
| Hosting | Vercel | Deployed application |

No unnecessary framework overhead — every component was chosen because it's the simplest tool that solves the specific problem, not because it's fashionable.

## Core Capabilities

**Evidence Retrieval**
Finds the right policy, SOP, contract, or product documentation for a given question via semantic search, then ranks retrieved chunks by relevance and authority.

**Structured Data Queries**
Answers questions about live operational state — order status, account details, ticket history — directly from PostgreSQL rather than relying on the model's training data or stale document snapshots.

**Multi-Step Reasoning**
Chains retrieval and data steps together for compound questions (e.g., *"Can this customer cancel this order without a fee?"* requires identifying the order, the account, the applicable contract, and the general policy — then reconciling them).

**Account Isolation**
Every query is scoped to the requesting account at the data and tool layer. A request for another customer's data returns *insufficient evidence*, not a leaked record.

**Controlled Actions**
The agent can propose operational actions (e.g., escalating a ticket) but never executes them silently. Every action requires explicit human confirmation, and the UI makes the pending/confirmed state unambiguous.

## Trust & Source Authority Model

Not every source is equally authoritative. ParcelPilot AI applies an explicit priority order when sources conflict:

1. **Customer Contract** — highest priority when applicable to the account
2. **Current Policy / SOP**
3. **Current Product Documentation**
4. **Historical Tickets** — context only, not authoritative
5. **Deprecated Policy** — historical reference only
6. **Unknown / Insufficient Evidence** — escalates to a human rather than guessing

Three rules govern this hierarchy:

- `Contract > Generic Policy`
- `Current > Historical`
- `Evidence > Confidence`

This is enforced in the retrieval/ranking logic, not left as an instruction the model might ignore under pressure.

## Security & Account Isolation

Account isolation is implemented as a **data and tool-layer constraint**, not a prompt instruction. Every retrieval and query call is parameterized by the authenticated account context before it reaches FAISS or PostgreSQL — so there is no query path through which the model could retrieve another account's records, regardless of how the request is phrased.

```
Request → Account Validation → Authorization Check → [Access Denied | Scoped Query]
```

If validation fails, the agent returns an explicit *insufficient evidence* response rather than an error that reveals the existence of other accounts' data.

## Controlled Actions

State-changing operations (e.g., ticket escalation) follow a strict propose → confirm → execute flow:

1. The agent identifies the action and states its reasoning.
2. It presents a **Proposed Action** card with an explicit *"No changes have been made"* notice.
3. Execution only occurs after the user clicks **Confirm**.
4. On confirmation, the action is applied and the ticket/order state is updated.

This guarantees the model can never take an irreversible action as a side effect of a conversational turn.

## Example Interactions

| Question | Behavior |
|---|---|
| *"Why can a SwiftShip shipment remain BOOKED after pickup?"* | Retrieves the Product Operations Guide, cites the known-issue entry (webhook delay up to 20 minutes), returns a grounded answer |
| *"What is the current status of ORD-1001?"* | Queries PostgreSQL directly for live order state |
| *"Can Northstar cancel ORD-1001 without a cancellation fee? Explain why."* | Chains order lookup → account lookup → contract retrieval → policy retrieval → comparison → answer |
| *"Show me another customer's orders."* | Denied at the data layer; returns insufficient evidence, not a security exception message |
| *"Escalate ticket TKT-450 because of an SLA breach."* | Proposes the escalation, requires confirmation, then executes and updates the ticket |

## Getting Started

> Adjust commands to match your actual repo layout and package manager.

```bash
# clone
git clone <repo-url>
cd parcelpilot-ai

# backend
cd api
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, GEMINI_API_KEY, etc.
uvicorn main:app --reload

# frontend
cd ../web
npm install
npm run dev
```

Required environment variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Gemini API key for generation |
| `FAISS_INDEX_PATH` | Path to the persisted vector index |
| `EMBEDDING_MODEL` | Sentence Transformers model identifier |

## Project Structure

```
parcelpilot-ai/
├── api/                  # FastAPI backend
│   ├── agent/            # Reasoning, retrieval orchestration, tool routing
│   ├── retrieval/        # FAISS index build + query logic
│   ├── data/              # SQLAlchemy models, PostgreSQL access
│   ├── actions/           # Controlled-action handlers + confirmation gate
│   └── main.py
├── docs/                  # Source documents (policies, contracts, SOPs)
├── web/                   # ParcelPilot UI
└── README.md
```

## Design Decisions & Trade-offs

- **FAISS over a managed vector DB** — the supplied dataset is small enough that a managed vector database would add operational overhead without a retrieval-quality benefit. This is a deliberate scope decision, not a limitation of the architecture.
- **PostgreSQL as the single source of truth for operational state** — the model is never asked to reason about live status from memory or stale document content; it queries the database directly.
- **Confirmation gate as a hard boundary** — rather than relying on prompt-level caution, state-changing actions are structurally incapable of executing without an explicit user confirmation event.
- **Account scoping enforced below the model** — isolation is a property of the query layer, so it holds even if the model is adversarially prompted.

## What's Not Built Yet

Being explicit about scope:

- No proactive/anomaly detection (see Roadmap)
- No RBAC / SSO — single-account-context sessions only
- No automated evaluation harness for answer quality yet
- No formal audit log for confirmed actions beyond ticket/order state updates

## Roadmap

**Next priority: Proactive Issue Detection** — surfacing SLA-risk tickets, repeated product issues, complaint spikes, cross-account incidents, and emerging operational problems before they become a ticket backlog.

1. Evaluation & Observability — systematic scoring of answer groundedness and retrieval quality
2. Human Feedback Loop — capture corrections to improve ranking and reasoning over time
3. RBAC / SSO — multi-user, permissioned access per account
4. Automated Incident Clustering — group related tickets to detect systemic issues early

---

*Know what is true. Know why it is true. Act only when it is safe.*
