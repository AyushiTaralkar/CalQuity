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

from app.services.account_guard import (
    AccountAccessGuard,
    AccountAccessError,
)


class QueryService:
    """
    Main CalQuity orchestration layer.

    Combines:

        1. Account authorization
        2. Operational database data
        3. Policy / contract RAG evidence
        4. Grounded Gemini generation
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

            raise ValueError(
                "Question cannot be empty."
            )

        question = question.strip()

        # =====================================================
        # 0. ACCOUNT ACCESS CONTROL
        # =====================================================

        guard = AccountAccessGuard(
            account_id=account_id
        )

        try:

            # Verify account exists
            guard.validate_account()

            # Check whether question explicitly targets
            # another customer.
            guard.validate_question(
                question
            )

        except AccountAccessError as exc:

            return {
                "question": question,
                "account_id": account_id,
                "order_id": order_id,
                "ticket_id": ticket_id,

                "answer": (
                    "ANSWER:\n"
                    "Access denied.\n\n"
                    "REASONING:\n"
                    f"{str(exc)}"
                ),

                "confidence": 1.0,

                "sources": [],

                "retrieved_chunks": 0,

                "database_context": {},
            }

        # =====================================================
        # 1. DATABASE CONTEXT
        # =====================================================

        database_context = {}

        # -----------------------------------------------------
        # ACCOUNT
        # -----------------------------------------------------

        if account_id:

            account = lookup_account(
                account_id
            )

            if account:

                database_context["account"] = account

                database_context["orders"] = (
                    get_account_orders(
                        account_id
                    )
                )

                database_context["tickets"] = (
                    get_account_tickets(
                        account_id
                    )
                )

        # -----------------------------------------------------
        # ORDER
        # -----------------------------------------------------

        if order_id:

            order = lookup_order(
                order_id
            )

            if order:

                # HARD OWNERSHIP CHECK
                try:

                    guard.validate_order_access(
                        order
                    )

                except AccountAccessError as exc:

                    return {
                        "question": question,
                        "account_id": account_id,
                        "order_id": order_id,
                        "ticket_id": ticket_id,

                        "answer": (
                            "ANSWER:\n"
                            "Access denied.\n\n"
                            "REASONING:\n"
                            f"{str(exc)}"
                        ),

                        "confidence": 1.0,
                        "sources": [],
                        "retrieved_chunks": 0,
                        "database_context": {},
                    }

                database_context["order"] = order

        # -----------------------------------------------------
        # TICKET
        # -----------------------------------------------------

        if ticket_id:

            ticket = lookup_ticket(
                ticket_id
            )

            if ticket:

                # HARD OWNERSHIP CHECK
                try:

                    guard.validate_ticket_access(
                        ticket
                    )

                except AccountAccessError as exc:

                    return {
                        "question": question,
                        "account_id": account_id,
                        "order_id": order_id,
                        "ticket_id": ticket_id,

                        "answer": (
                            "ANSWER:\n"
                            "Access denied.\n\n"
                            "REASONING:\n"
                            f"{str(exc)}"
                        ),

                        "confidence": 1.0,
                        "sources": [],
                        "retrieved_chunks": 0,
                        "database_context": {},
                    }

                database_context["ticket"] = ticket

        # =====================================================
        # 2. RAG RETRIEVAL
        # =====================================================

        results = self.retriever.retrieve(
            query=question,
            account_id=account_id,
        )

        # =====================================================
        # 3. GROUNDED GENERATION
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
        }