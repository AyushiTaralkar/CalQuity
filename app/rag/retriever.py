from typing import Optional

from app.rag.vector_store import load_vector_store, search


class Retriever:
    """
    Authority-aware and account-aware semantic retriever.

    Retrieval flow:
        Query
          ↓
        FAISS semantic search
          ↓
        Metadata filtering
          ↓
        Authority/version/account ranking
          ↓
        Final results
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

        self.model, self.index, self.metadata = load_vector_store()

    def retrieve(
        self,
        query: str,
        account_id: Optional[str] = None,
        authority: Optional[str] = None,
        document_status: Optional[str] = "CURRENT",
    ):
        """
        Retrieve relevant chunks with optional metadata constraints.

        Args:
            query: User's natural-language question.
            account_id: Restrict results to a specific account.
            authority: Restrict results to a specific authority.
            document_status: Prefer/filter CURRENT documents.
                             Pass None to disable status filtering.

        Returns:
            List of retrieved document chunks.
        """

        # Retrieve more candidates first so filtering does not
        # leave us with too few results.
        candidate_k = max(self.top_k * 3, 10)

        results = search(
            self.model,
            self.index,
            self.metadata,
            query,
            top_k=candidate_k,
        )

        filtered_results = []

        for result in results:
            metadata = result.get("metadata", {})

            # -----------------------------
            # Account filtering
            # -----------------------------
            if account_id:
                result_account_id = metadata.get("account_id")

                # Account-specific documents must match.
                # Global documents without an account_id are allowed.
                if (
                    result_account_id is not None
                    and result_account_id != account_id
                ):
                    continue

            # -----------------------------
            # Authority filtering
            # -----------------------------
            if authority:
                result_authority = metadata.get("authority")

                if result_authority != authority:
                    continue

            # -----------------------------
            # Document status filtering
            # -----------------------------
            if document_status:
                result_status = (
                    metadata.get("status")
                    or metadata.get("document_status")
                    or metadata.get("version_status")
                )

                # Only filter if status actually exists.
                if result_status and result_status.upper() != document_status.upper():
                    continue

            filtered_results.append(result)

        # -----------------------------
        # Current documents get priority
        # -----------------------------
        def ranking_score(result):
            metadata = result.get("metadata", {})

            status = (
                metadata.get("status")
                or metadata.get("document_status")
                or metadata.get("version_status")
                or ""
            ).upper()

            similarity = result.get("score", 0)

            current_bonus = 1.0 if status == "CURRENT" else 0.0

            return similarity + current_bonus

        filtered_results.sort(
            key=ranking_score,
            reverse=True,
        )

        return filtered_results[: self.top_k]