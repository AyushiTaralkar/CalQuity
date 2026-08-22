from typing import Optional

from app.database.repository import (
    lookup_account,
    lookup_order,
    lookup_ticket,
    get_account_orders,
    get_account_tickets,
    get_all_accounts,
)

from app.rag.evidence import (
    build_evidence,
    filter_account_evidence,
    get_best_evidence,
)

from app.rag.retriever import Retriever
from app.rag.generator import AnswerGenerator


class QueryService:
    """
    Main CalQuity orchestration layer.

    Combines:
        1. Operational database data
        2. Account authorization / tenant isolation
        3. Policy / contract RAG evidence
        4. Grounded Gemini generation

    Security:
        A customer can ONLY access:
        - Their own account
        - Their own orders
        - Their own tickets
        - Their own account-specific contract

        Global ParcelPilot policies are accessible to all accounts.
    """

    def __init__(self, top_k: int = 3):
        self.retriever = Retriever(top_k=top_k)
        self.generator = AnswerGenerator()

    # ============================================================
    # SECURITY HELPERS
    # ============================================================

    def _access_denied_response(self):
        return {
            "answer": (
                "ANSWER:\n"
                "Access denied.\n\n"
                "REASONING:\n"
                "Access denied: you cannot access another customer's "
                "account information."
            ),
            "confidence": 1.0,
            "sources": [],
        }

    def _account_not_found_response(self):
        return {
            "answer": (
                "ANSWER:\n"
                "Account not found.\n\n"
                "REASONING:\n"
                "The supplied account ID does not exist in the "
                "operational database."
            ),
            "confidence": 1.0,
            "sources": [],
        }

    def _order_not_found_response(self):
        return {
            "answer": (
                "ANSWER:\n"
                "The requested order could not be found.\n\n"
                "REASONING:\n"
                "No operational database record exists for this order."
            ),
            "confidence": 1.0,
            "sources": [],
        }

    def _ticket_not_found_response(self):
        return {
            "answer": (
                "ANSWER:\n"
                "The requested ticket could not be found.\n\n"
                "REASONING:\n"
                "No operational database record exists for this ticket."
            ),
            "confidence": 1.0,
            "sources": [],
        }

    # ============================================================
    # GEMINI FALLBACK
    # ============================================================

    def _evidence_fallback_response(
        self,
        question: str,
        results: list,
        database_context: dict,
    ):
        """
        Safe fallback when Gemini is unavailable.

        Never invents an answer.
        Returns only information that exists in retrieved evidence.
        """

        if not results and not database_context:
            return {
                "answer": (
                    "ANSWER:\n"
                    "The available evidence is insufficient.\n\n"
                    "REASONING:\n"
                    "No relevant authorized evidence was retrieved for "
                    "this question. Therefore, I cannot determine the "
                    "answer without risking an unsupported claim."
                ),
                "confidence": 0.0,
                "sources": [],
            }

        answer_parts = [
            "ANSWER:",
            "The AI generation service is temporarily unavailable, "
            "so I cannot provide a synthesized answer.",
            "",
            "REASONING:",
            "The following authorized evidence was retrieved and can "
            "be reviewed, but it should not be interpreted beyond "
            "what is explicitly stated in the evidence.",
        ]

        sources = []

        for result in results:

            document = result.get("document")
            page = result.get("page")
            authority = result.get("authority")
            content = result.get("content", "")
            score = result.get("score")

            if content:
                content = content.strip()

                # Prevent extremely large fallback responses
                if len(content) > 700:
                    content = content[:700].rstrip() + "..."

                answer_parts.extend(
                    [
                        "",
                        f"- {content}",
                    ]
                )

            sources.append(
                {
                    "document": document,
                    "page": page,
                    "authority": authority,
                    "account_id": result.get("account_id"),
                    "score": score,
                }
            )

        answer_parts.extend(
            [
                "",
                "NOTE:",
                "This response is based only on retrieved authorized "
                "evidence because the AI generation service is currently "
                "unavailable.",
            ]
        )

        # Conservative confidence because this is not LLM-generated
        confidence = 0.5 if results else 0.2

        return {
            "answer": "\n".join(answer_parts),
            "confidence": confidence,
            "sources": sources,
        }

    # ============================================================
    # CROSS-ACCOUNT SECURITY
    # ============================================================

    def _contains_other_account_reference(
        self,
        question: str,
        current_account_id: str,
    ) -> bool:
        """
        Detect explicit references to another customer account.
        """

        if not current_account_id:
            return False

        question_lower = question.lower()

        accounts = get_all_accounts()

        for account in accounts:

            target_account_id = account["account_id"]
            target_account_name = account["account_name"]

            # Skip current account
            if target_account_id == current_account_id:
                continue

            # Account ID
            if target_account_id.lower() in question_lower:
                return True

            # Full account name
            if (
                target_account_name
                and target_account_name.lower() in question_lower
            ):
                return True

            # Short company name
            words = target_account_name.lower().split()

            if words:

                short_name = words[0]

                if len(short_name) >= 4:
                    if short_name in question_lower:
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
        """
        Execute a secure CalQuity query.

        Pipeline:

        1. Validate question
        2. Validate requesting account
        3. Detect cross-account references
        4. Validate order ownership
        5. Validate ticket ownership
        6. Build database context
        7. Retrieve RAG evidence
        8. Apply account filtering
        9. Apply evidence precedence
        10. Generate grounded answer
        11. Fall back safely if Gemini fails
        """

        # ========================================================
        # 1. BASIC VALIDATION
        # ========================================================

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        question = question.strip()

        # ========================================================
        # 2. ACCOUNT VALIDATION
        # ========================================================

        requesting_account = None

        if account_id:

            requesting_account = lookup_account(account_id)

            if requesting_account is None:

                response = self._account_not_found_response()

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": response["answer"],
                    "confidence": response["confidence"],
                    "sources": response["sources"],
                    "retrieved_chunks": 0,
                }

        # ========================================================
        # 3. CROSS-ACCOUNT QUESTION CHECK
        # ========================================================

        if account_id:

            if self._contains_other_account_reference(
                question,
                account_id,
            ):

                response = self._access_denied_response()

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": response["answer"],
                    "confidence": response["confidence"],
                    "sources": response["sources"],
                    "retrieved_chunks": 0,
                }

        # ========================================================
        # 4. ORDER AUTHORIZATION
        # ========================================================

        order = None

        if order_id:

            order = lookup_order(order_id)

            # Order does not exist
            if order is None:

                response = self._order_not_found_response()

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": response["answer"],
                    "confidence": response["confidence"],
                    "sources": response["sources"],
                    "retrieved_chunks": 0,
                }

            # Tenant isolation
            if account_id and order["account_id"] != account_id:

                response = self._access_denied_response()

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": response["answer"],
                    "confidence": response["confidence"],
                    "sources": response["sources"],
                    "retrieved_chunks": 0,
                }

        # ========================================================
        # 5. TICKET AUTHORIZATION
        # ========================================================

        ticket = None

        if ticket_id:

            ticket = lookup_ticket(ticket_id)

            # Ticket does not exist
            if ticket is None:

                response = self._ticket_not_found_response()

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": response["answer"],
                    "confidence": response["confidence"],
                    "sources": response["sources"],
                    "retrieved_chunks": 0,
                }

            # Tenant isolation
            if account_id and ticket["account_id"] != account_id:

                response = self._access_denied_response()

                return {
                    "question": question,
                    "account_id": account_id,
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "answer": response["answer"],
                    "confidence": response["confidence"],
                    "sources": response["sources"],
                    "retrieved_chunks": 0,
                }

        # ========================================================
        # 6. DATABASE CONTEXT
        # ========================================================

        database_context = {}

        if requesting_account:

            database_context["account"] = requesting_account

            database_context["orders"] = get_account_orders(
                account_id
            )

            database_context["tickets"] = get_account_tickets(
                account_id
            )

        if order:
            database_context["order"] = order

        if ticket:
            database_context["ticket"] = ticket

        # ========================================================
        # 7. ACCOUNT-AWARE RAG RETRIEVAL
        # ========================================================

        # Retrieve evidence for every question.
        # Intent routing is intentionally bypassed here because
        # policy/product questions must not be skipped due to
        # incorrect intent classification.

        results = self.retriever.retrieve(
            query=question,
            account_id=account_id,
        )

        # ========================================================
        # 8. EVIDENCE + PRECEDENCE
        # ========================================================

        evidence = build_evidence(results)

        # Never allow another customer's contract
        # to enter the generation context.
        evidence = filter_account_evidence(
            evidence,
            account_id,
        )

        # Deterministic authority ordering.
        evidence = get_best_evidence(
            evidence,
            limit=self.retriever.top_k,
        )

        # ========================================================
        # 9. CONVERT EVIDENCE FOR GENERATOR
        # ========================================================

        results = [
            {
                "document": item.document,
                "page": item.page,
                "content": item.content,
                "authority": item.authority,
                "account_id": item.account_id,
                "score": item.score,
            }
            for item in evidence
        ]

        # ========================================================
        # 10. GROUNDED ANSWER GENERATION
        # ========================================================

        try:

            response = self.generator.generate(
                question=question,
                results=results,
                account_id=account_id,
                database_context=database_context,
            )

        except Exception as exc:

            error_message = str(exc)

            print(
                "[WARN] Gemini generation failed. "
                f"Using evidence fallback. Error: {error_message}"
            )

            response = self._evidence_fallback_response(
                question=question,
                results=results,
                database_context=database_context,
            )

        # ========================================================
        # 11. FINAL RESPONSE
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