from app.rag.document_loader import load_all_documents
from app.rag.chunker import create_chunks


def main():

    print("\n" + "=" * 70)
    print("DOCUMENT CHUNKING TEST")
    print("=" * 70)

    documents = load_all_documents()

    chunks = create_chunks(documents)

    print(f"\nDocuments/pages: {len(documents)}")
    print(f"Total chunks: {len(chunks)}")

    print("\n" + "-" * 70)
    print("FIRST 5 CHUNKS")
    print("-" * 70)

    for chunk in chunks[:5]:

        print("\n")
        print(f"Chunk ID: {chunk.chunk_id}")

        print(
            f"Document type: "
            f"{chunk.metadata.get('document_type')}"
        )

        print(
            f"Authority: "
            f"{chunk.metadata.get('authority')}"
        )

        print(
            f"Page: "
            f"{chunk.metadata.get('page')}"
        )

        print(
            f"Characters: "
            f"{len(chunk.text)}"
        )

        print("\nTEXT:")
        print(chunk.text[:500])

        print("\n" + "-" * 70)


if __name__ == "__main__":
    main()