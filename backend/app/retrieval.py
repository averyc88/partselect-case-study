"""Chroma-backed semantic retrieval — the *fuzzy* half of hybrid retrieval.

Only the repair/troubleshooting corpus is embedded here. Structured facts
(parts, models, orders, compatibility) never touch the vector store — they go
through `data_access.py`. This module owns the Chroma client, the collection
config, and the rule for turning a repair doc into its embedded string, so that
rule lives in exactly one place and `ingest.py` (seed) and querying (here) can
never drift apart.
"""

from pathlib import Path

import chromadb

from app import embedder

# Persisted index lives next to the backend, gitignored, rebuilt by ingest.py.
CHROMA_PATH = str(Path(__file__).resolve().parent.parent / ".chroma")
COLLECTION = "repairs"


def embedding_text(doc: dict) -> str:
    """Build the string we embed for a repair doc.

    The rule (locked in PLAN.md): embed `title + symptoms + user_phrasings`.
    The `user_phrasings` are messy, natural ways a user describes the problem —
    they're where retrieval power lives, so they MUST be in the embedded string,
    not just stored as metadata. `content` (polished prose) is displayed, not
    embedded.
    """
    parts = [doc["title"], *doc["symptoms"], *doc["user_phrasings"]]
    return " ".join(parts)


def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection() -> chromadb.Collection:
    """Return the repairs collection, creating it if absent.

    Cosine space matches our L2-normalized embeddings.
    """
    return _client().get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def search(query: str, appliance: str | None = None, k: int = 3) -> list[dict]:
    """Return the top-k repair docs most similar to the query.

    We embed the query with the same model used at seed time, then ask Chroma
    for nearest neighbors. An optional `appliance` filter ("refrigerator" /
    "dishwasher") narrows results via Chroma metadata so a dishwasher query
    can't surface a fridge doc. Each result carries the displayed `content`,
    `related_parts`, and a similarity `score` for ranking/UX.
    """
    query = query.strip()
    if not query:
        return []

    collection = get_collection()
    where = {"appliance": appliance} if appliance else None
    [query_vec] = embedder.embed([query])

    res = collection.query(
        query_embeddings=[query_vec],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns parallel lists nested one level (one per query).
    ids = res["ids"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    results = []
    for doc_id, meta, dist in zip(ids, metas, dists):
        results.append(
            {
                "id": doc_id,
                "title": meta["title"],
                "appliance": meta["appliance"],
                "content": meta["content"],
                "related_parts": meta["related_parts"].split(",") if meta["related_parts"] else [],
                "score": round(1.0 - dist, 4),  # cosine distance -> similarity
            }
        )
    return results
