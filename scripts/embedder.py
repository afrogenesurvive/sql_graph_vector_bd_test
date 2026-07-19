"""Embedding abstraction — dispatches to OpenAI or local sentence-transformers."""

from typing import List

from scripts import config
from scripts.logger import get_logger

logger = get_logger(__name__)

# Lazy-loaded clients
_openai_client = None
_local_model = None


def _get_openai_embedding(text: str) -> List[float]:
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    response = _openai_client.embeddings.create(
        input=text,
        model=config.EMBEDDING_MODEL,
    )
    return response.data[0].embedding


def _get_local_embedding(text: str) -> List[float]:
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        _local_model = SentenceTransformer(config.EMBEDDING_MODEL)

    return _local_model.encode(text).tolist()


def get_embedding(text: str) -> List[float]:
    """Generate an embedding vector for *text*.

    Dispatches to the provider configured in ``EMBEDDING_PROVIDER``.
    """
    provider = config.EMBEDDING_PROVIDER.lower()

    if provider == "openai":
        return _get_openai_embedding(text)
    elif provider == "local":
        return _get_local_embedding(text)
    else:
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER '{provider}'. "
            "Use 'openai' or 'local'."
        )
