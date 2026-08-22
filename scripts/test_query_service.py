from app.services.query_service import QueryService


def main():

    service = QueryService(
        top_k=3
    )

    test_cases = [
        {
            "question": (
                "Can Northstar cancel a BOOKED shipment "
                "without a cancellation fee?"
            ),
            "account_id": "ACCT-001",
        },
        {
            "question": (
                "What are the cancellation terms?"
            ),
            "account_id": "ACCT-002",
        },
        {
            "question": (
                "Why can a SwiftShip shipment remain "
                "BOOKED after pickup?"
            ),
            "account_id": None,
        },
    ]

    for test in test_cases:

        print("\n" + "=" * 80)
        print("QUESTION")
        print("=" * 80)

        print(test["question"])

        print("\nACCOUNT:")
        print(test["account_id"])

        response = service.query(
            question=test["question"],
            account_id=test["account_id"],
        )

        print("\n" + "=" * 80)
        print("ANSWER")
        print("=" * 80)

        print(response["answer"])

        print("\nCONFIDENCE:")
        print(response["confidence"])

        print("\nRETRIEVED CHUNKS:")
        print(response["retrieved_chunks"])

        print("\nSOURCES:")

        for source in response["sources"]:
            print(
                f"- {source['document']} "
                f"(page {source['page']}) "
                f"[{source['authority']}]"
            )


if __name__ == "__main__":
    main()