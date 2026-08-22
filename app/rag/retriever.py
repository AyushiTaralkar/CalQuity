from typing import Optional

from app.rag.vector_store import load_vector_store, search


class Retriever:
    """
    Authority-aware and account-aware semantic retriever.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

        self.model, self.index, self.metadata = load_vector_store()

    def retrieve(
        self,
        query: str,
        account_id: Optional[str] = None,
        authority: Optional[str] = None,
        document_status: Optional[str] = None,
    ):
        """
        Retrieve relevant chunks.

        Args:
            query: User question.
            account_id: Optional customer account ID.
            authority: Optional authority filter.
            document_status: Optional status filter.

        Returns:
            Top-k filtered and ranked results.
        """

        # Retrieve extra candidates before filtering.
        candidate_k = max(self.top_k * 4, 20)

        results = search(
            self.model,
            self.index,
            self.metadata,
            query,
            top_k=candidate_k,
        )

        filtered = []

        for result in results:
            metadata = result.get("metadata", {})

            result_authority = str(
                metadata.get("authority", "")
            ).strip().lower()

            result_account = metadata.get("account_id")

            result_status = str(
                metadata.get("status")
                or metadata.get("document_status")
                or metadata.get("version_status")
                or ""
            ).strip().lower()

            # -------------------------------------------------
            # Account filtering
            # -------------------------------------------------
            if account_id:
                if result_account is not None:
                    if str(result_account).strip() != str(account_id).strip():
                        continue

            # -------------------------------------------------
            # Authority filtering
            # -------------------------------------------------
            if authority:
                if result_authority != authority.strip().lower():
                    continue

            # -------------------------------------------------
            # Explicit document status filtering
            # -------------------------------------------------
            if document_status:
                if result_status != document_status.strip().lower():
                    continue

            # Add normalized metadata for downstream LLM.
            result["metadata"] = {
                **metadata,
                "_normalized_authority": result_authority,
                "_normalized_status": result_status,
            }

            filtered.append(result)

        # -----------------------------------------------------
        # Ranking
        # -----------------------------------------------------
        def ranking_score(result):
            metadata = result.get("metadata", {})

            similarity = float(result.get("score", 0))

            status = metadata.get(
                "_normalized_status", ""
            )

            authority_value = metadata.get(
                "_normalized_authority", ""
            )

            # Current documents receive a small boost.
            current_bonus = 0.15 if status == "current" else 0.0

            # Contracts are useful for account-specific questions.
            contract_bonus = (
                0.05 if authority_value == "contract" and account_id else 0.0
            )

            return similarity + current_bonus + contract_bonus

        filtered.sort(
            key=ranking_score,
            reverse=True,
        )

        return filtered[: self.top_k]