import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from sententia.retrieval.corpus import CorpusDocument

COLLECTION_NAME = "sententia_corpus"


def build_index(docs: list[CorpusDocument], persist_dir: str) -> chromadb.api.models.Collection.Collection:
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=DefaultEmbeddingFunction(),
    )

    collection.upsert(
        ids=[doc.doc_id for doc in docs],
        documents=[doc.body for doc in docs],
        metadatas=[
            {
                "citation": doc.citation,
                "source_url": doc.source_url,
                "topic": doc.topic,
                "court": doc.court,
                "kind": doc.kind,
            }
            for doc in docs
        ],
    )
    return collection
