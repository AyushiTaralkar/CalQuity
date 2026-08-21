from pathlib import Path
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

VECTOR_STORE_DIR = Path(
    "data/processed/vector_store"
)

INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
METADATA_FILE = VECTOR_STORE_DIR / "metadata.pkl"


def load_vector_store():

    print("Loading embedding model...")

    model = SentenceTransformer(
        MODEL_NAME
    )

    print("Loading FAISS index...")

    index = faiss.read_index(
        str(INDEX_FILE)
    )

    print("Loading metadata...")

    with open(
        METADATA_FILE,
        "rb",
    ) as file:

        metadata = pickle.load(file)

    return model, index, metadata


def search(
    model,
    index,
    metadata,
    query: str,
    top_k: int = 3,
):

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    query_embedding = query_embedding.astype(
        np.float32
    )

    scores, indices = index.search(
        query_embedding,
        top_k,
    )

    results = []

    for score, index_position in zip(
        scores[0],
        indices[0],
    ):

        if index_position == -1:
            continue

        item = metadata[index_position]

        results.append(
            {
                "score": float(score),
                **item,
            }
        )

    return results


def main():

    model, index, metadata = (
        load_vector_store()
    )

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

        results = search(
            model,
            index,
            metadata,
            query,
            top_k=3,
        )

        print("\nRESULTS")

        for rank, result in enumerate(
            results,
            start=1,
        ):

            print(
                "\n" + "-" * 60
            )

            print(
                f"Rank: {rank}"
            )

            print(
                f"Score: {result['score']:.4f}"
            )

            print(
                f"Source: "
                f"{result['metadata']['source']}"
            )

            print(
                f"Page: "
                f"{result['metadata']['page']}"
            )

            print(
                f"Authority: "
                f"{result['metadata']['authority']}"
            )

            print("\nText:")

            print(
                result["text"][:500]
            )


if __name__ == "__main__":
    main()