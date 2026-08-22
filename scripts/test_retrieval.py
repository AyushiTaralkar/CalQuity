from app.rag.retriever import Retriever


def print_results(title, results):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})

        print(f"\n#{i}")
        print("Score:", result.get("score"))
        print("Source:", metadata.get("source"))
        print("Page:", metadata.get("page"))
        print("Authority:", metadata.get("authority"))
        print("Account:", metadata.get("account_id"))
        print("Status:", metadata.get("_normalized_status"))
        print("Text:", result.get("text", "")[:500])


def main():
    retriever = Retriever(top_k=3)

    # -----------------------------------------
    # Test 1: General RAG
    # -----------------------------------------
    results = retriever.retrieve(
        "Why can a SwiftShip shipment remain BOOKED after pickup?"
    )

    print_results(
        "GENERAL QUERY",
        results,
    )

    # -----------------------------------------
    # Test 2: Account-aware retrieval
    # -----------------------------------------
    results = retriever.retrieve(
        "What are the cancellation terms?",
        account_id="ACCT-001",
    )

    print_results(
        "ACCT-001 QUERY",
        results,
    )

    # -----------------------------------------
    # Test 3: Another account
    # -----------------------------------------
    results = retriever.retrieve(
        "What are the cancellation terms?",
        account_id="ACCT-002",
    )

    print_results(
        "ACCT-002 QUERY",
        results,
    )


if __name__ == "__main__":
    main()