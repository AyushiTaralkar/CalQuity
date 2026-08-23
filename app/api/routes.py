import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.repository import (
    escalate_ticket,
    lookup_ticket,
)
from app.services.query_service import QueryService


router = APIRouter(
    prefix="/api/v1",
    tags=["CalQuity"],
)


# ============================================================
# LAZY QUERY SERVICE
# ============================================================

query_service = None


def get_query_service() -> QueryService:
    """
    Create QueryService only when it is actually needed.

    This prevents SentenceTransformer + FAISS from loading
    during FastAPI startup.
    """
    global query_service

    if query_service is None:
        query_service = QueryService(top_k=3)

    return query_service


# ============================================================
# ESCALATION DETECTION
# ============================================================

def detect_escalation_action(
    question: str,
    account_id: Optional[str],
):
    """
    Detect an explicit user request to escalate a ticket.

    This does NOT execute the escalation.
    It only creates a proposed action.

    The user must explicitly confirm before the
    state-changing endpoint is executed.
    """

    if not question:
        return None

    text = question.lower()

    escalation_keywords = [
        "escalate",
        "escalation",
    ]

    if not any(
        keyword in text
        for keyword in escalation_keywords
    ):
        return None

    # Find ticket IDs such as TKT-450.
    match = re.search(
        r"\bTKT-\d+\b",
        question.upper(),
    )

    if not match:
        return None

    ticket_id = match.group(0)

    reason = "User requested ticket escalation"

    if "sla" in text:
        reason = "SLA breach"

    return {
        "type": "escalate_ticket",
        "ticket_id": ticket_id,
        "account_id": account_id,
        "reason": reason,
    }


# ============================================================
# QUERY MODELS
# ============================================================

class QueryRequest(BaseModel):
    question: str
    account_id: Optional[str] = None
    order_id: Optional[str] = None
    ticket_id: Optional[str] = None


class Source(BaseModel):
    document: Optional[str] = None
    page: Optional[int] = None
    authority: Optional[str] = None
    account_id: Optional[str] = None
    score: Optional[float] = None


class ActionProposal(BaseModel):
    type: str
    ticket_id: str
    account_id: str
    reason: str


class QueryResponse(BaseModel):
    question: str

    account_id: Optional[str] = None
    order_id: Optional[str] = None
    ticket_id: Optional[str] = None

    answer: str
    confidence: float

    sources: list[Source]

    retrieved_chunks: int

    tool: Optional[str] = None

    action: Optional[ActionProposal] = None


# ============================================================
# QUERY ENDPOINT
# ============================================================

@router.post(
    "/query",
    response_model=QueryResponse,
)
def query(request: QueryRequest):
    """
    Main ParcelPilot AI query endpoint.

    Handles:
    1. Explicit escalation requests
    2. Normal AI/RAG queries

    State-changing actions require a separate
    explicit confirmation request.
    """

    try:

        # ====================================================
        # 1. DETECT STATE-CHANGING REQUEST
        # ====================================================

        action = detect_escalation_action(
            question=request.question,
            account_id=request.account_id,
        )

        # ====================================================
        # 2. ACTION REQUEST -> PROPOSAL ONLY
        # ====================================================

        if action:

            return {
                "question": request.question,
                "account_id": request.account_id,
                "order_id": request.order_id,
                "ticket_id": action["ticket_id"],
                "answer": (
                    f"I found ticket {action['ticket_id']}. "
                    f"You requested an escalation because of "
                    f"{action['reason'].lower()}. "
                    f"No changes have been made yet. "
                    f"Please confirm if you want me to escalate "
                    f"the ticket."
                ),
                "confidence": 1.0,
                "sources": [],
                "retrieved_chunks": 0,
                "tool": "Ticket Lookup",
                "action": action,
            }

        # ====================================================
        # 3. NORMAL AI QUERY
        # ====================================================

        service = get_query_service()

        response = service.query(
            question=request.question,
            account_id=request.account_id,
            order_id=request.order_id,
            ticket_id=request.ticket_id,
        )

        return response

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(exc)}",
        )


# ============================================================
# ACTION MODELS
# ============================================================

class EscalationRequest(BaseModel):
    ticket_id: str
    account_id: str

    # Action cannot execute unless the user explicitly confirms.
    confirm: bool = False


class EscalationResponse(BaseModel):
    success: bool
    action: str
    confirmed: bool

    ticket_id: str
    account_id: str

    previous_status: Optional[str] = None
    new_status: Optional[str] = None

    message: str


# ============================================================
# ESCALATION ACTION
# ============================================================

@router.post(
    "/actions/escalate-ticket",
    response_model=EscalationResponse,
)
def escalate_ticket_action(
    request: EscalationRequest,
):
    """
    State-changing escalation action.

    Flow:

        confirm=False
            ↓
        Proposal only

        confirm=True
            ↓
        Execute escalation

    SECURITY:
        The ticket must belong to the supplied account_id.
    """

    # ========================================================
    # 1. LOOK UP TICKET
    # ========================================================

    ticket = lookup_ticket(
        request.ticket_id
    )

    if ticket is None:

        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    # ========================================================
    # 2. TENANT / ACCOUNT ISOLATION
    # ========================================================

    if ticket["account_id"] != request.account_id:

        raise HTTPException(
            status_code=403,
            detail=(
                "Access denied: this ticket does not "
                "belong to the requesting account."
            ),
        )

    previous_status = ticket["status"]

    # ========================================================
    # 3. CONFIRMATION GATE
    # ========================================================

    if not request.confirm:

        return {
            "success": False,
            "action": "ESCALATE_TICKET",
            "confirmed": False,
            "ticket_id": request.ticket_id,
            "account_id": request.account_id,
            "previous_status": previous_status,
            "new_status": None,
            "message": (
                f"Escalation proposed for ticket "
                f"{request.ticket_id}. "
                f"The ticket is currently {previous_status}. "
                f"Explicit confirmation is required before "
                f"the ticket is changed."
            ),
        }

    # ========================================================
    # 4. EXECUTE STATE CHANGE
    # ========================================================

    result = escalate_ticket(
        ticket_id=request.ticket_id,
        account_id=request.account_id,
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Ticket could not be escalated or does not "
                "belong to the requesting account."
            ),
        )

    # ========================================================
    # 5. ALREADY ESCALATED
    # ========================================================

    if result.get("already_escalated"):

        return {
            "success": True,
            "action": "ESCALATE_TICKET",
            "confirmed": True,
            "ticket_id": request.ticket_id,
            "account_id": request.account_id,
            "previous_status": previous_status,
            "new_status": result["status"],
            "message": (
                f"Ticket {request.ticket_id} was already "
                f"escalated."
            ),
        }

    # ========================================================
    # 6. SUCCESSFUL ESCALATION
    # ========================================================

    return {
        "success": True,
        "action": "ESCALATE_TICKET",
        "confirmed": True,
        "ticket_id": request.ticket_id,
        "account_id": request.account_id,
        "previous_status": previous_status,
        "new_status": result["status"],
        "message": (
            f"Ticket {request.ticket_id} has been successfully "
            f"escalated."
        ),
    }