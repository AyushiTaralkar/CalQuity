from pathlib import Path

from pypdf import PdfReader


DOCUMENTS_DIR = Path("data/raw/documents")


def extract_pdf_text(pdf_path: Path) -> list[dict]:
    """
    Extract text from every page of a PDF.

    Returns one dictionary per page so we can preserve
    page-level metadata for future citations.
    """

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        text = text.strip()

        if not text:
            continue

        pages.append(
            {
                "source": pdf_path.name,
                "page": page_number,
                "text": text,
            }
        )

    return pages


def load_all_documents() -> list[dict]:
    """
    Load every PDF from the documents directory.
    """

    documents = []

    pdf_files = sorted(DOCUMENTS_DIR.glob("*.pdf"))

    for pdf_path in pdf_files:
        print(f"Reading: {pdf_path.name}")

        pages = extract_pdf_text(pdf_path)

        documents.extend(pages)

        print(f"  Pages extracted: {len(pages)}")

    return documents


if __name__ == "__main__":

    documents = load_all_documents()

    print("\n" + "=" * 70)
    print("DOCUMENT INGESTION SUMMARY")
    print("=" * 70)

    print(f"Total pages extracted: {len(documents)}")

    sources = sorted(
        set(document["source"] for document in documents)
    )

    print(f"Documents found: {len(sources)}")

    for source in sources:
        count = sum(
            1
            for document in documents
            if document["source"] == source
        )

        print(f"  {source}: {count} pages")