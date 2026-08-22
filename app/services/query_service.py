from typing import Optional

from app.database.repository import (
    lookup_account,
    lookup_order,
    lookup_ticket,
    get_account_orders,
    get_account_tickets,
    get_all_accounts,
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

    Security:
        - Enforces tenant/account isolation
        - Prevents cross-account order access
        - Prevents cross-account ticket access
        - Prevents questions about other customer accounts
        - Performs authorization BEFORE RAG retrieval
    """

    def __init__(self, top_k: int = 3):
        self.retriever = Retriever(top_k=top_k)
        self.generator = AnswerGenerator()

    # ============================================================
    # SECURITY RESPONSE
    # ============================================================

    def _access_denied(
        self,
        question: str,
        account_id: Optional[str],
        order_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
    ):
        """
        Safe response for unauthorized cross-account requests.

        IMPORTANT:
        No RAG retrieval happens for denied requests.
        """

        return {
            "question": question,
            "account_id": account_id,
            "order_id": order_id,
            "ticket_id": ticket_id,
            "answer": (
                "ANSWER:\n"
                "Access denied.\n\n"
                "REASONING:\n"
                "Access denied: you cannot access another customer's "
                "account information."
            ),
            "confidence": 1.0,
            "sources": [],
            "retrieved_chunks": 0,
        }

    # ============================================================
    # CROSS-ACCOUNT QUESTION DETECTION
    # ============================================================

    def _contains_other_account(
        self,
        question: str,
        current_account_id: str,
    ) -> bool:
        """
        Detect whether the user's question explicitly mentions
        another customer's account ID or account name.

        Example:

            Current account:
                ACCT-001 / Northstar Logistics

            Question:
                "What are LumenWorks' cancellation terms?"

            Result:
                True

        This check happens BEFORE RAG retrieval.
        """

        question_lower = question.lower()

        accounts = get_all_accounts()

        for account in accounts:

            other_account_id = account["account_id"]
            other_account_name = account["account_name"]

            # Ignore the current customer's own account.
            if other_account_id == current_account_id:
                continue

            # ----------------------------------------------------
            # Check account ID
            # ----------------------------------------------------

            if (
                other_account_id
                and other_account_id.lower() in question_lower
            ):
                return True

            # ----------------------------------------------------
            # Check account name
            # ----------------------------------------------------

            if (
                other_account_name
                and other_account_name.lower() in question_lower
            ):
                return True

        return False

    # ============================================================
    # MAIN QUERY
    # ============================================================

    def query(
        self,
        question: str,
        account_id: Optional[str] = None,
        order_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
    ):

        # ========================================================
        # 1. BASIC VALIDATION
        # ========================================================

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        question = question.strip()

        # ========================================================
        # 2. ACCOUNT VALIDATION
        # ========================================================

        account = None

        if account_id:

            account = lookup_account(account_id)

            # Unknown account
            if not account:
                return self._access_denied(
                    question=question,
                    account_id=account_id,
                    order_id=order_id,
                    ticket_id=ticket_id,
                )

        # ========================================================
        # 3. CROSS-ACCOUNT QUESTION PROTECTION
        # ========================================================

        """
        IMPORTANT SECURITY CHECK.

        Example:

            account_id = ACCT-001

            question =
                "What are LumenWorks' cancellation terms?"

        Even though no order_id or ticket_id is supplied,
        the question itself references another customer.

        Therefore we reject BEFORE RAG.
        """

        if account_id:

            if self._contains_other_account(
                question=question,
                current_account_id=account_id,
            ):
                return self._access_denied(
                    question=question,
                    account_id=account_id,
                    order_id=order_id,
                    ticket_id=ticket_id,
                )

        # ========================================================
        # 4. ORDER AUTHORIZATION
        # ========================================================

        order = None

        if order_id:

            order = lookup_order(order_id)

            # ----------------------------------------------------
            # Order does not exist
            # ----------------------------------------------------

            if not order:

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": (
                        "ANSWER:\n"
                        "The requested order could not be found.\n\n"
                        "REASONING:\n"
                        "No operational database record exists "
                        "for this order."
                    ),
                    "confidence": 1.0,
                    "sources": [],
                    "retrieved_chunks": 0,
                }

            # ----------------------------------------------------
            # CRITICAL TENANT CHECK
            # ----------------------------------------------------

            if account_id:

                if order["account_id"] != account_id:

                    return self._access_denied(
                        question=question,
                        account_id=account_id,
                        order_id=order_id,
                        ticket_id=ticket_id,
                    )

        # ========================================================
        # 5. TICKET AUTHORIZATION
        # ========================================================

        ticket = None

        if ticket_id:

            ticket = lookup_ticket(ticket_id)

            # ----------------------------------------------------
            # Ticket does not exist
            # ----------------------------------------------------

            if not ticket:

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": (
                        "ANSWER:\n"
                        "The requested ticket could not be found.\n\n"
                        "REASONING:\n"
                        "No operational database record exists "
                        "for this ticket."
                    ),
                    "confidence": 1.0,
                    "sources": [],
                    "retrieved_chunks": 0,
                }

            # ----------------------------------------------------
            # CRITICAL TENANT CHECK
            # ----------------------------------------------------

            if account_id:

                if ticket["account_id"] != account_id:

                    return self._access_denied(
                        question=question,
                        account_id=account_id,
                        order_id=order_id,
                        ticket_id=ticket_id,
                    )

        # ========================================================
        # 6. DATABASE CONTEXT
        # ========================================================

        database_context = {}

        # --------------------------------------------------------
        # Account context
        # --------------------------------------------------------

        if account:

            database_context["account"] = account

            database_context["orders"] = get_account_orders(
                account_id
            )

            database_context["tickets"] = get_account_tickets(
                account_id
            )

        # --------------------------------------------------------
        # Specific order context
        # --------------------------------------------------------

        if order:

            database_context["order"] = order

        # --------------------------------------------------------
        # Specific ticket context
        # --------------------------------------------------------

        if ticket:

            database_context["ticket"] = ticket

        # ========================================================
        # 7. RAG RETRIEVAL
        # ========================================================

        """
        RAG happens ONLY after all authorization checks.

        This is important because unauthorized requests should
        never retrieve another customer's contract.
        """

        results = self.retriever.retrieve(
            query=question,
            account_id=account_id,
        )

        # ========================================================
        # 8. GROUNDED GENERATION
        # ========================================================

        response = self.generator.generate(
            question=question,
            results=results,
            account_id=account_id,
            database_context=database_context,
        )

        # ========================================================
        # 9. FINAL RESPONSE
        # ========================================================

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