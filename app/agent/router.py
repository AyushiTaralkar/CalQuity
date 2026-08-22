import re
from enum import Enum


class Intent(str, Enum):
    DATABASE = "database"
    RAG = "rag"
    COMBINED = "combined"


def detect_intent(question: str) -> Intent:
    """
    Determine whether a question needs:
    - DATABASE
    - RAG
    - BOTH
    """

    q = question.lower()

    # -----------------------------
    # DATABASE signals
    # -----------------------------

    database_keywords = [
        "status",
        "where is",
        "when was",
        "carrier",
        "tracking",
        "ticket",
        "account",
        "shipment",
        "delivered",
        "booked",
        "picked_up",
    ]

    # Detect actual IDs such as:
    # ORD-1001
    # TKT-505
    # ACCT-001
    has_order_id = bool(re.search(r"\bord-\d+\b", q))
    has_ticket_id = bool(re.search(r"\btkt-\d+\b", q))
    has_account_id = bool(re.search(r"\bacct-\d+\b", q))

    has_database = (
        any(word in q for word in database_keywords)
        or has_order_id
        or has_ticket_id
        or has_account_id
    )

    # -----------------------------
    # RAG signals
    # -----------------------------

    rag_keywords = [
        "policy",
        "policies",
        "contract",
        "terms",
        "cancellation",
        "refund",
        "fee",
        "sla",
        "support",
        "documentation",
        "allowed",
        "maximum",
        "limit",
        "eligibility",
        "agreement",
        "sop",
    ]

    has_rag = any(word in q for word in rag_keywords)

    # -----------------------------
    # FINAL ROUTING
    # -----------------------------

    if has_database and has_rag:
        return Intent.COMBINED

    if has_rag:
        return Intent.RAG

    if has_database:
        return Intent.DATABASE

    # Default: ground unknown questions in documents
    return Intent.RAG