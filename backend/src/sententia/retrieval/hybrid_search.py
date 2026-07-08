import re
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from rank_bm25 import BM25Okapi

from sententia.retrieval.corpus import CorpusDocument, load_corpus
from sententia.retrieval.index import COLLECTION_NAME

RRF_K = 60  # standard constant from the Reciprocal Rank Fusion paper (Cormack et al., 2009)
CORPUS_DIR = Path(__file__).resolve().parents[4] / "corpus"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def get_collection(persist_dir: str) -> chromadb.api.models.Collection.Collection:
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
    )


def _reciprocal_rank_fusion(*ranked_id_lists: list[str]) -> list[str]:
    scores: dict[str, float] = {}
    for ranked_ids in ranked_id_lists:
        for rank, doc_id in enumerate(ranked_ids):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (RRF_K + rank + 1)
    return sorted(scores, key=lambda doc_id: scores[doc_id], reverse=True)


def hybrid_search(
    collection: chromadb.api.models.Collection.Collection,
    query: str,
    top_k: int,
    exclude_citations: set[str] | None = None,
    corpus_dir: Path = CORPUS_DIR,
) -> list[CorpusDocument]:
    exclude_citations = exclude_citations or set()
    docs = load_corpus(corpus_dir)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    candidate_docs = [doc for doc in docs if doc.citation not in exclude_citations]
    candidate_ids = {doc.doc_id for doc in candidate_docs}

    n_candidates = min(10, len(candidate_docs))
    if n_candidates == 0:
        return []

    vector_result = collection.query(
        query_texts=[query],
        n_results=min(10, collection.count()),
    )
    vector_ranked_ids = [
        doc_id for doc_id in vector_result["ids"][0] if doc_id in candidate_ids
    ][:n_candidates]

    bm25_corpus = [_tokenize(doc.body) for doc in candidate_docs]
    bm25 = BM25Okapi(bm25_corpus)
    bm25_scores = bm25.get_scores(_tokenize(query))
    bm25_ranked_ids = [
        candidate_docs[i].doc_id
        for i in sorted(range(len(candidate_docs)), key=lambda i: bm25_scores[i], reverse=True)
    ][:n_candidates]

    fused_ids = _reciprocal_rank_fusion(vector_ranked_ids, bm25_ranked_ids)
    return [docs_by_id[doc_id] for doc_id in fused_ids[:top_k]]
