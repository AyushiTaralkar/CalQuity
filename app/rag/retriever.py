from typing import Optional

from app.rag.vector_store import load_vector_store, search


class Retriever:
    """
    Reusable semantic retriever for CalQuity documents.
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

        self.model, self.index, self.metadata = load_vector_store()

    def retrieve(
        self,
        query: str,
        account_id: Optional[str] = None,
    ):
        """
        Retrieve relevant document chunks.

        Account-specific evidence is preferred,
        while global policies remain available.
        """

        results = search(
            self.model,
            self.index,
            self.metadata,
            query,
            top_k=self.top_k,
        )

        if not account_id:
            return results

        account_results = []
        global_results = []

        for result in results:

            # Support both metadata formats
            metadata = result.get("metadata") or {}

            result_account = (
                metadata.get("account_id")
                or result.get("account_id")
            )

            if result_account == account_id:

                account_results.append(result)

            elif result_account is None:

                global_results.append(result)

        # Account-specific evidence first.
        ordered = account_results + global_results

        return ordered[:self.top_k]