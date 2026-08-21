from pathlib import Path

from app.rag.metadata import build_metadata


DOCUMENTS_DIR = Path("data/raw/documents")


def main():

    print("\n" + "=" * 70)
    print("DOCUMENT METADATA")
    print("=" * 70)

    for pdf in sorted(DOCUMENTS_DIR.glob("*.pdf")):

        metadata = build_metadata(pdf.name)

        print("\n" + pdf.name)

        for key, value in metadata.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()