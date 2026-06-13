"""Seed the Chroma vector store from the repair corpus.

Run once (and after any edit to repairs.json):

    cd backend && uv run python scripts/ingest.py

Reads `data/repairs.json`, builds each doc's embedded string
(`title + symptoms + user_phrasings`) via `retrieval.embedding_text`, embeds
with the local model, and upserts into the persisted `./.chroma` collection.
Displayed fields (`content`, `related_parts`, `title`, `appliance`) ride along
as Chroma metadata so retrieval needs no second lookup.

This is a build artifact: `.chroma/` is gitignored and rebuilt locally — it's
tied to the chosen embedding model, so it must be regenerated, not committed.
"""

import json
from pathlib import Path

from app import embedder, retrieval

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "repairs.json"


def main() -> None:
    docs = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(docs)} repair docs from {DATA_FILE.name}")

    ids = [d["id"] for d in docs]
    embed_strings = [retrieval.embedding_text(d) for d in docs]
    # Chroma metadata values must be scalars — join the parts list to a string;
    # retrieval.search splits it back. `content` is what the UI displays.
    metadatas = [
        {
            "title": d["title"],
            "appliance": d["appliance"],
            "content": d["content"],
            "related_parts": ",".join(d["related_parts"]),
        }
        for d in docs
    ]

    print(f"Embedding with {embedder.MODEL_NAME} (first run downloads the model)...")
    vectors = embedder.embed(embed_strings)

    collection = retrieval.get_collection()
    # Upsert so re-running is idempotent rather than erroring on existing ids.
    collection.upsert(ids=ids, embeddings=vectors, metadatas=metadatas)

    print(f"Upserted {collection.count()} docs into '{retrieval.COLLECTION}' at {retrieval.CHROMA_PATH}")


if __name__ == "__main__":
    main()
