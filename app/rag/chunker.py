from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """
    A chunk of document text with its metadata.
    """

    chunk_id: str
    text: str
    metadata: dict


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[str]:
    """
    Split text into overlapping chunks.

    Example:

        chunk 1: characters 0-1000
        chunk 2: characters 850-1850
        chunk 3: characters 1700-2700

    Overlap helps prevent important information from being
    split across two chunks.
    """

    if not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def create_chunks(documents: list[dict]) -> list[DocumentChunk]:
    """
    Convert extracted document pages into DocumentChunk objects.
    """

    all_chunks = []

    for document in documents:

        source = document["source"]
        page = document["page"]
        text = document["text"]
        base_metadata = document.get("metadata", {})

        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):

            chunk_id = (
                f"{source}:page-{page}:chunk-{index}"
            )

            metadata = {
                **base_metadata,
                "source": source,
                "page": page,
                "chunk_index": index,
                "chunk_id": chunk_id,
            }

            all_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    text=chunk,
                    metadata=metadata,
                )
            )

    return all_chunks