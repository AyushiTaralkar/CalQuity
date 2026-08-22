from enum import Enum


class Intent(str, Enum):
    DATABASE = "database"
    RAG = "rag"
    COMBINED = "combined"


def detect_intent(question: str) -> Intent:
    """
    Simple deterministic intent router.

    DATABASE:
        Questions answerable from operational data.

    RAG:
        Questions requiring policies, contracts, SOPs, or documentation.

    COMBINED:
        Questions requiring both operational data and documents.
    """

    q = question.lower()

    # DATABASE keywords
    database_keywords = [
        "status",
        "where is",
        "when was",
        "carrier",
        "tracking",
        "order",
        "ticket",
        "account",
        "shipment",
        "delivered",
        "booked",
        "picked_up",
    ]

    # RAG / knowledge keywords
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

    has_database = any(word in q for word in database_keywords)
    has_rag = any(word in q for word in rag_keywords)

    # Both DB + documents
    if has_database and has_rag:
        return Intent.COMBINED

    # Documents only
    if has_rag:
        return Intent.RAG

    # Database only
    if has_database:
        return Intent.DATABASE

    # Default to RAG because unknown knowledge
    # questions should be grounded in documents.
    return Intent.RAG