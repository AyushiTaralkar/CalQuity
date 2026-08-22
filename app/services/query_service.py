from typing import Optional

from app.rag.retriever import Retriever
from app.rag.generator import AnswerGenerator


class QueryService:
    """
    Main CalQuity query orchestration layer.

    Flow:
        User question
            ↓
        Retriever
            ↓
        Account-aware evidence
            ↓
        AnswerGenerator
            ↓
        Grounded response
    """

    def __init__(
        self,
        top_k: int = 3,
    ):
        self.retriever = Retriever(
            top_k=top_k
        )

        self.generator = AnswerGenerator()

    def query(
        self,
        question: str,
        account_id: Optional[str] = None,
    ):
        """
        Execute a complete CalQuity query.
        """

        # -----------------------------
        # Validate question
        # -----------------------------
        if not question or not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        question = question.strip()

        # -----------------------------
        # Retrieve evidence
        # -----------------------------
        results = self.retriever.retrieve(
            query=question,
            account_id=account_id,
        )

        # -----------------------------
        # Generate grounded answer
        # -----------------------------
        response = self.generator.generate(
            question=question,
            results=results,
            account_id=account_id,
        )

        # -----------------------------
        # Return clean response
        # -----------------------------
        return {
            "question": question,
            "account_id": account_id,
            "answer": response["answer"],
            "confidence": response["confidence"],
            "sources": response["sources"],
            "retrieved_chunks": len(results),
        }