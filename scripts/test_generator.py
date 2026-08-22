from app.rag.retriever import Retriever
from app.rag.generator import AnswerGenerator


def main():

    retriever = Retriever(top_k=3)

    generator = AnswerGenerator()

    question = (
        "Can Northstar cancel a BOOKED shipment "
        "without a cancellation fee?"
    )

    account_id = "ACCT-001"

    print("\nRetrieving evidence...")

    results = retriever.retrieve(
        question,
        account_id=account_id,
    )

    print(
        f"Retrieved {len(results)} sources."
    )

    print("\nGenerating grounded answer...")

    response = generator.generate(
        question=question,
        results=results,
        account_id=account_id,
    )

    print("\n" + "=" * 80)
    print("CALQUITY ANSWER")
    print("=" * 80)

    print(response["answer"])

    print("\n" + "=" * 80)
    print("CONFIDENCE")
    print("=" * 80)

    print(response["confidence"])

    print("\n" + "=" * 80)
    print("SOURCES")
    print("=" * 80)

    for source in response["sources"]:

        print(
            f"- {source['document']} "
            f"(page {source['page']}) "
            f"[{source['authority']}]"
        )


if __name__ == "__main__":
    main()