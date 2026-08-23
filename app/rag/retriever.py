from typing import Optional

from app.rag.vector_store import load_vector_store, search


class Retriever:
    """
    Semantic retriever for ParcelPilot AI documents.

    Loads the embedding model, FAISS index, and metadata once,
    then performs account-aware semantic retrieval.
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

        Account-specific evidence is preferred.
        Global policies remain available to all accounts.
        """

        raw_results = search(
            self.model,
            self.index,
            self.metadata,
            query,
            top_k=self.top_k,
        )

        normalized_results = []

        for result in raw_results:

            metadata = result.get("metadata") or {}

            normalized_results.append(
                {
                    "document": metadata.get("source"),
                    "page": metadata.get("page"),
                    "content": result.get("text", ""),
                    "authority": metadata.get("authority"),
                    "account_id": metadata.get("account_id"),
                    "score": result.get("score"),
                    "chunk_id": result.get("chunk_id"),
                }
            )

        # If no account is supplied,
        # return the global semantic results.
        if not account_id:
            return normalized_results

        account_results = []
        global_results = []

        for result in normalized_results:

            result_account = result.get("account_id")

            if result_account == account_id:
                account_results.append(result)

            elif result_account is None:
                global_results.append(result)

        # Account-specific evidence first,
        # followed by global policies.
        ordered_results = (
            account_results + global_results
        )

        return ordered_results[:self.top_k]