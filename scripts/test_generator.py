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

    results = retriever.retrieve(
        question,
        account_id=account_id,
    )

    print("\n" + "=" * 80)
    print("RETRIEVED EVIDENCE")
    print("=" * 80)

    for result in results:
        metadata = result.get("metadata", {})

        print("\nSOURCE:", metadata.get("source"))
        print("ACCOUNT:", metadata.get("account_id"))
        print("AUTHORITY:", metadata.get("authority"))
        print("SCORE:", result.get("score"))

    prompt = generator.build_prompt(
        question=question,
        results=results,
        account_id=account_id,
    )

    print("\n" + "=" * 80)
    print("GENERATED PROMPT")
    print("=" * 80)

    print(prompt)


if __name__ == "__main__":
    main()