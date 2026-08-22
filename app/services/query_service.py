from typing import Optional

from app.database.repository import (
    lookup_account,
    lookup_order,
    lookup_ticket,
    get_account_orders,
    get_account_tickets,
)

from app.rag.retriever import Retriever
from app.rag.generator import AnswerGenerator


class QueryService:
    """
    Main CalQuity orchestration layer.

    Combines:
        1. Operational database data
        2. Policy / contract RAG evidence
        3. Grounded Gemini generation
    """

    def __init__(self, top_k: int = 3):
        self.retriever = Retriever(top_k=top_k)
        self.generator = AnswerGenerator()

    def query(
        self,
        question: str,
        account_id: Optional[str] = None,
        order_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
    ):
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        question = question.strip()

        # =====================================================
        # 1. DATABASE CONTEXT
        # =====================================================

        database_context = {}

        if account_id:
            account = lookup_account(account_id)

            if account:
                database_context["account"] = account

                database_context["orders"] = (
                    get_account_orders(account_id)
                )

                database_context["tickets"] = (
                    get_account_tickets(account_id)
                )

        if order_id:
            order = lookup_order(order_id)

            if order:
                database_context["order"] = order

        if ticket_id:
            ticket = lookup_ticket(ticket_id)

            if ticket:
                database_context["ticket"] = ticket

        # =====================================================
        # 2. RAG RETRIEVAL
        # =====================================================

        results = self.retriever.retrieve(
            query=question,
            account_id=account_id,
        )

        # =====================================================
        # 3. GENERATE GROUNDED ANSWER
        # =====================================================

        response = self.generator.generate(
            question=question,
            results=results,
            account_id=account_id,
            database_context=database_context,
        )

        # =====================================================
        # 4. RETURN RESPONSE
        # =====================================================

        return {
            "question": question,
            "account_id": account_id,
            "order_id": order_id,
            "ticket_id": ticket_id,
            "answer": response["answer"],
            "confidence": response["confidence"],
            "sources": response["sources"],
            "retrieved_chunks": len(results),
            "database_context": database_context,
        }