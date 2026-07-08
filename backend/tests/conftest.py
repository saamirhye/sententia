import shutil
import tempfile
from pathlib import Path

import pytest

from sententia.retrieval.corpus import load_corpus
from sententia.retrieval.index import build_index

CORPUS_DIR = Path(__file__).resolve().parents[2] / "corpus"


@pytest.fixture(scope="session")
def chroma_persist_dir():
    """Builds the Chroma index once per test session into a throwaway temp
    directory -- keeps tests isolated from the developer's real chroma_data/
    and avoids re-embedding the corpus for every test function."""
    tmp_dir = tempfile.mkdtemp(prefix="sententia_test_chroma_")
    try:
        docs = load_corpus(CORPUS_DIR)
        build_index(docs, persist_dir=tmp_dir)
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
