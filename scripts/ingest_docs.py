"""
CLI: ingest PDF policy documents into the FAISS vector store.

Usage:
    python scripts/ingest_docs.py --file path/to/policy.pdf --intent refund
    python scripts/ingest_docs.py --dir data/policies/refund --intent refund
    python scripts/ingest_docs.py --dir data/policies --intent general --recursive
"""

import argparse
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent2.vector_store import add_documents, INTENTS

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " "],
)


def ingest_file(pdf_path: Path, intent: str) -> int:
    loader = PyPDFLoader(str(pdf_path))
    raw_docs = loader.load()

    # Attach source metadata so retriever can surface references
    for doc in raw_docs:
        doc.metadata.setdefault("source", pdf_path.name)
        doc.metadata["intent"] = intent

    chunks = splitter.split_documents(raw_docs)
    add_documents(chunks, intent)
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description="Ingest policy PDFs into FAISS index")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Single PDF file to ingest")
    group.add_argument("--dir", type=Path, help="Directory of PDF files to ingest")
    parser.add_argument(
        "--intent",
        required=True,
        choices=INTENTS,
        help=f"Policy namespace: {INTENTS}",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories (only with --dir)",
    )
    args = parser.parse_args()

    if args.file:
        if not args.file.exists():
            print(f"Error: {args.file} not found")
            sys.exit(1)
        n = ingest_file(args.file, args.intent)
        print(f"Ingested {n} chunks from {args.file.name} → namespace '{args.intent}'")

    elif args.dir:
        if not args.dir.is_dir():
            print(f"Error: {args.dir} is not a directory")
            sys.exit(1)
        pattern = "**/*.pdf" if args.recursive else "*.pdf"
        pdfs = list(args.dir.glob(pattern))
        if not pdfs:
            print(f"No PDF files found in {args.dir}")
            sys.exit(0)
        total = 0
        for pdf in pdfs:
            n = ingest_file(pdf, args.intent)
            print(f"  {pdf.name}: {n} chunks")
            total += n
        print(f"\nTotal: {total} chunks ingested → namespace '{args.intent}'")


if __name__ == "__main__":
    main()
