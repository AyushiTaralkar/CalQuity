from pathlib import Path
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.rag.document_loader import load_all_documents
from app.rag.chunker import create_chunks


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

VECTOR_STORE_DIR = Path("data/processed/vector_store")

INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
METADATA_FILE = VECTOR_STORE_DIR / "metadata.pkl"


# ============================================================
# EMBEDDING MODEL
# ============================================================

print(f"Loading embedding model: {MODEL_NAME}")

model = SentenceTransformer(MODEL_NAME)


# ============================================================
# BUILD VECTOR STORE
# ============================================================

def build_vector_store():

    print("\nLoading documents...")

    documents = load_all_documents()

    print(f"Pages loaded: {len(documents)}")

    print("\nCreating chunks...")

    chunks = create_chunks(documents)

    print(f"Chunks created: {len(chunks)}")

    if not chunks:
        raise ValueError("No document chunks found.")

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    texts = [
        chunk.text
        for chunk in chunks
    ]

    # --------------------------------------------------------
    # Create embeddings
    # --------------------------------------------------------

    print("\nCreating embeddings...")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embeddings = embeddings.astype(
        np.float32
    )

    print(
        f"Embedding shape: {embeddings.shape}"
    )

    # --------------------------------------------------------
    # Create FAISS index
    # --------------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    print(
        f"Vectors stored: {index.ntotal}"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    VECTOR_STORE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    faiss.write_index(
        index,
        str(INDEX_FILE),
    )

    metadata = [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
        }
        for chunk in chunks
    ]

    with open(
        METADATA_FILE,
        "wb",
    ) as file:

        pickle.dump(
            metadata,
            file,
        )

    print("\n" + "=" * 70)
    print("VECTOR STORE CREATED")
    print("=" * 70)

    print(f"Index: {INDEX_FILE}")
    print(f"Metadata: {METADATA_FILE}")
    print(f"Vectors: {index.ntotal}")
    print(f"Dimensions: {dimension}")


if __name__ == "__main__":
    build_vector_store()