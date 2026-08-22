from typing import Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.query_service import QueryService


router = APIRouter(
    prefix="/api/v1",
    tags=["CalQuity"],
)


query_service = QueryService(top_k=3)


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


class QueryResponse(BaseModel):
    question: str
    account_id: Optional[str] = None
    order_id: Optional[str] = None
    ticket_id: Optional[str] = None

    answer: str
    confidence: float

    sources: list[Source]

    retrieved_chunks: int

    database_context: dict[str, Any] = {}


@router.post(
    "/query",
    response_model=QueryResponse,
)
def query(request: QueryRequest):

    try:

        response = query_service.query(
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