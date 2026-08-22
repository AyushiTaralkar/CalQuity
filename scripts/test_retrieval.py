from app.rag.retriever import Retriever


def main():

    retriever = Retriever(top_k=3)

    queries = [
        "Can a BOOKED shipment be cancelled after 30 minutes?",
        "What is the priority for suspected API key exposure?",
        "Why can a SwiftShip shipment remain BOOKED after pickup?",
        "What is the maximum CSV upload size for Growth?",
    ]

    for query in queries:

        print("\n" + "=" * 70)
        print("QUERY")
        print("=" * 70)

        print(query)

        results = retriever.retrieve(query)

        print("\nRESULTS")

        for rank, result in enumerate(
            results,
            start=1,
        ):

            print("\n" + "-" * 60)

            print(f"Rank: {rank}")
            print(f"Score: {result['score']:.4f}")

            metadata = result["metadata"]

            print(f"Source: {metadata['source']}")
            print(f"Page: {metadata['page']}")
            print(f"Authority: {metadata['authority']}")

            print("\nText:")
            print(result["text"][:500])


if __name__ == "__main__":
    main()