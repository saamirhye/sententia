from pathlib import Path

from sententia.config import CHROMA_PERSIST_DIR
from sententia.retrieval.corpus import load_corpus
from sententia.retrieval.index import build_index

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"

if __name__ == "__main__":
    docs = load_corpus(CORPUS_DIR)
    build_index(docs, persist_dir=CHROMA_PERSIST_DIR)
    print(f"Indexed {len(docs)} documents into Chroma at {CHROMA_PERSIST_DIR}.")
