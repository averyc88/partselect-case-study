"""Swappable embedding interface.

Both `ingest.py` (seed time) and `retrieval.py` (query time) call `embed()`
here, so the same model embeds the corpus and the queries — non-negotiable, or
the vectors live in different spaces and similarity is meaningless.

Default impl is local `sentence-transformers/all-MiniLM-L6-v2`: 384-dim, ~80MB,
CPU-fine, zero API keys (the reviewer needs only an Anthropic key). The model is
downloaded once on first use and cached by `sentence-transformers`.

To scale up, swap the impl behind `embed()` for a hosted model (e.g. Voyage
`voyage-3-lite` or OpenAI `text-embedding-3-small`) — set a key, change this one
function, and nothing else in the pipeline moves. That seam is the whole point
of keeping embedding explicit rather than letting Chroma own it internally.
"""

from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model():
    """Load the SentenceTransformer once and reuse it (memoized singleton).

    Imported lazily inside the function so importing this module (e.g. in tests
    that don't embed) doesn't pay the multi-second model-load cost.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into a list of float vectors.

    Returns plain Python lists (not numpy) so the output drops straight into
    Chroma and serializes cleanly. Vectors are L2-normalized so cosine
    similarity and dot product agree.
    """
    if not texts:
        return []
    vectors = _model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()
