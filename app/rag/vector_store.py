from pathlib import Path
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

VECTOR_STORE_DIR = Path("data/processed/vector_store")

INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
METADATA_FILE = VECTOR_STORE_DIR / "metadata.pkl"


def load_vector_store():
    """
    Load the embedding model, FAISS index, and chunk metadata.
    """

    model = SentenceTransformer(MODEL_NAME)

    index = faiss.read_index(
        str(INDEX_FILE)
    )

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
    """
    Perform semantic search over the FAISS vector store.
    """

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