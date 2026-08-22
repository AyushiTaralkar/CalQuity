from dataclasses import dataclass
from typing import Optional


# ============================================================
# SOURCE AUTHORITY
# ============================================================

AUTHORITY_PRIORITY = {
    "contract": 5,
    "customer_policy": 4,
    "current": 3,
    "product": 2,
    "historical": 1,
    "deprecated": 0,
}


@dataclass
class Evidence:
    document: str
    page: int
    content: str
    authority: str
    account_id: Optional[str] = None
    score: float = 0.0

    @property
    def authority_priority(self) -> int:
        return AUTHORITY_PRIORITY.get(self.authority, 0)


# ============================================================
# BUILD EVIDENCE
# ============================================================

def build_evidence(results: list[dict]) -> list[Evidence]:
    """
    Convert raw RAG retrieval results into structured Evidence.

    Supports both formats:

    1. {
        "metadata": {
            "document": "...",
            "page": 1,
            "authority": "contract",
            "account_id": "ACCT-001"
        },
        "content": "...",
        "score": 0.9
    }

    2. {
        "document": "...",
        "page": 1,
        "authority": "contract",
        "account_id": "ACCT-001",
        "content": "...",
        "score": 0.9
    }
    """

    evidence = []

    for result in results:

        # ----------------------------------------------------
        # Safely extract metadata
        # ----------------------------------------------------

        metadata = result.get("metadata") or {}

        # ----------------------------------------------------
        # DOCUMENT
        # ----------------------------------------------------

        document = (
            metadata.get("document")
            or metadata.get("source")
            or result.get("document")
            or result.get("source")
            or "unknown"
        )

        # ----------------------------------------------------
        # PAGE
        # ----------------------------------------------------

        page = (
            metadata.get("page")
            or metadata.get("page_number")
            or result.get("page")
            or result.get("page_number")
            or 0
        )

        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        content = (
            result.get("content")
            or result.get("text")
            or metadata.get("content")
            or ""
        )

        # ----------------------------------------------------
        # AUTHORITY
        # ----------------------------------------------------

        authority = (
            metadata.get("authority")
            or result.get("authority")
            or "current"
        )

        # ----------------------------------------------------
        # ACCOUNT
        # ----------------------------------------------------

        result_account_id = (
            metadata.get("account_id")
            or result.get("account_id")
        )

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        score = (
            result.get("score")
            if result.get("score") is not None
            else result.get("similarity", 0.0)
        )

        # ----------------------------------------------------
        # Create Evidence object
        # ----------------------------------------------------

        evidence.append(
            Evidence(
                document=str(document),
                page=int(page) if page is not None else 0,
                content=str(content),
                authority=str(authority),
                account_id=result_account_id,
                score=float(score or 0.0),
            )
        )

    return evidence


# ============================================================
# ACCOUNT FILTER
# ============================================================

def filter_account_evidence(
    evidence: list[Evidence],
    account_id: Optional[str],
) -> list[Evidence]:
    """
    Prevent cross-account contract leakage.

    Rules:

    Global documents:
        account_id = None
        -> allowed

    Customer-specific documents:
        account_id = current account
        -> allowed

    Customer-specific documents belonging to another account:
        -> rejected
    """

    if not account_id:
        return evidence

    filtered = []

    for item in evidence:

        # ----------------------------------------------------
        # Global policy / product documentation
        # ----------------------------------------------------

        if item.account_id is None:
            filtered.append(item)
            continue

        # ----------------------------------------------------
        # Account-specific evidence
        # ----------------------------------------------------

        if item.account_id == account_id:
            filtered.append(item)

    return filtered


# ============================================================
# AUTHORITY SORTING
# ============================================================

def rank_evidence(
    evidence: list[Evidence],
) -> list[Evidence]:
    """
    Rank evidence using:

        1. Authority
        2. Similarity score
    """

    return sorted(
        evidence,
        key=lambda x: (
            x.authority_priority,
            x.score,
        ),
        reverse=True,
    )


# ============================================================
# PRECEDENCE
# ============================================================

def apply_precedence(
    evidence: list[Evidence],
) -> list[Evidence]:
    """
    Deterministic source precedence:

        Contract
            ↓
        Customer Policy
            ↓
        Current Policy
            ↓
        Product Documentation
            ↓
        Historical
            ↓
        Deprecated
    """

    if not evidence:
        return []

    return rank_evidence(evidence)


# ============================================================
# BEST EVIDENCE
# ============================================================

def get_best_evidence(
    evidence: list[Evidence],
    limit: int = 3,
) -> list[Evidence]:
    """
    Return the highest-quality evidence.
    """

    ranked = apply_precedence(evidence)

    return ranked[:limit]


# ============================================================
# FORMAT FOR LLM
# ============================================================

def evidence_for_prompt(
    evidence: list[Evidence],
) -> str:
    """
    Convert structured evidence into a clean prompt section.
    """

    if not evidence:
        return "NO RELEVANT EVIDENCE FOUND."

    sections = []

    for i, item in enumerate(evidence, start=1):

        sections.append(
            f"""
EVIDENCE {i}

Document: {item.document}
Page: {item.page}
Authority: {item.authority}
Account ID: {item.account_id}
Relevance Score: {item.score:.3f}

Content:
{item.content}
""".strip()
        )

    return "\n\n".join(sections)