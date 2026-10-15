"""Texts as a search index: hybrid retrieval with Qdrant.

What is indexed is any list of records with a text: the disease passages the
RAG tool reads, or the names and synonyms of HPO terms a note's findings are
coded with (raredx.phenotyping).

Each passage gets two vectors, both computed on this machine with FastEmbed:
a dense one for meaning (BAAI/bge-small-en-v1.5, 384 dimensions), so
"cannot hear" finds "hearing loss"; and a sparse BM25 one for the words
themselves, so a rare term such as "hypogammaglobulinemia" counts for what it
is. A search runs both and fuses the two rankings by reciprocal rank (RRF):
the standard hybrid search, done inside Qdrant.

Embedding the passages takes minutes, so it is done once (`raredx data index`)
and stored under data/processed. A tool loads the vectors into an in-memory
Qdrant collection when it starts; against a Qdrant server the code is the
same, with a URL in place of ":memory:".
"""

import json
import threading
import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, Protocol

import numpy as np
from pydantic import BaseModel
from qdrant_client import QdrantClient, models

DENSE_MODEL = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"
COLLECTION = "disease_texts"
PASSAGES, DENSE, SPARSE, INFO = "passages.jsonl", "dense.npy", "sparse.jsonl", "index.json"
Mode = Literal["hybrid", "dense", "keyword"]


Sparse = tuple[list[int], list[float]]


class Embedder(Protocol):
    """Turns texts into a dense and a sparse vector each."""

    def passages(self, texts: list[str]) -> tuple[np.ndarray, list[Sparse]]: ...

    def query(self, text: str) -> tuple[list[float], Sparse]: ...


class FastEmbedder:
    """The two models, run locally by FastEmbed (ONNX); downloaded once into models_dir."""

    def __init__(self, models_dir: Path) -> None:
        from fastembed import SparseTextEmbedding, TextEmbedding

        self.dense = TextEmbedding(DENSE_MODEL, cache_dir=str(models_dir))
        self.sparse = SparseTextEmbedding(SPARSE_MODEL, cache_dir=str(models_dir))

    def passages(self, texts: list[str]) -> tuple[np.ndarray, list[Sparse]]:
        dense = np.array(list(self.dense.embed(texts, batch_size=64)), dtype=np.float32)
        sparse = [(v.indices.tolist(), v.values.tolist()) for v in self.sparse.embed(texts)]
        return dense, sparse

    def query(self, text: str) -> tuple[list[float], Sparse]:
        dense = next(iter(self.dense.query_embed(text))).tolist()
        sparse = next(iter(self.sparse.query_embed(text)))
        return dense, (sparse.indices.tolist(), sparse.values.tolist())


class TextIndex[T: BaseModel]:
    """Records searchable by their text; `passages` holds them in the order indexed."""

    def __init__(
        self,
        passages: list[T],
        dense: np.ndarray,
        sparse: list[Sparse],
        embedder: Embedder,
        info: dict[str, Any],
    ) -> None:
        self.passages = passages
        self.info = info
        self._embedder = embedder
        self._lock = (
            threading.Lock()
        )  # one search at a time: the embedded store is not built for more
        self._client = QdrantClient(":memory:")
        self._client.create_collection(
            COLLECTION,
            vectors_config={
                "dense": models.VectorParams(size=dense.shape[1], distance=models.Distance.COSINE)
            },
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        # Qdrant advises a server beyond 20,000 points in memory. The HPO terms' names
        # are 43,000: loaded in 5 s, searched in 0.1 s on a laptop — enough here, and a
        # server is a URL away (see above).
        warnings.filterwarnings("ignore", message="Local mode is not recommended")
        self._client.upload_points(
            COLLECTION,
            [
                models.PointStruct(
                    id=i,
                    vector={
                        "dense": dense[i].tolist(),
                        "bm25": models.SparseVector(indices=sparse[i][0], values=sparse[i][1]),
                    },
                )
                for i in range(len(passages))
            ],
        )

    @staticmethod
    def save(
        folder: Path,
        passages: Sequence[BaseModel],
        dense: np.ndarray,
        sparse: list[Sparse],
        info: dict[str, Any],
    ) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / PASSAGES).open("w", encoding="utf-8") as f:
            for p in passages:
                f.write(p.model_dump_json() + "\n")
        np.save(folder / DENSE, dense)
        with (folder / SPARSE).open("w", encoding="utf-8") as f:
            for indices, values in sparse:
                f.write(json.dumps([indices, values]) + "\n")
        info = {**info, "passages": len(passages), "dense": DENSE_MODEL, "sparse": SPARSE_MODEL}
        (folder / INFO).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, folder: Path, embedder: Embedder, kind: type[T]) -> "TextIndex[T]":
        """The index saved in folder, its records read back as `kind`."""
        with (folder / PASSAGES).open(encoding="utf-8") as f:
            passages = [kind.model_validate_json(line) for line in f]
        with (folder / SPARSE).open(encoding="utf-8") as f:
            sparse: list[Sparse] = [(row[0], row[1]) for row in map(json.loads, f)]
        info = json.loads((folder / INFO).read_text(encoding="utf-8"))
        return cls(passages, np.load(folder / DENSE), sparse, embedder, info)

    def search(self, query: str, limit: int, mode: Mode = "hybrid") -> list[tuple[T, float]]:
        """The records best matching the query, best first, with their scores (RRF
        scores in hybrid mode; compare within one search only)."""
        with self._lock:
            dense, (indices, values) = self._embedder.query(query)
            sparse = models.SparseVector(indices=indices, values=values)
            if mode == "dense":
                points = self._client.query_points(
                    COLLECTION, query=dense, using="dense", limit=limit
                ).points
            elif mode == "keyword":
                points = self._client.query_points(
                    COLLECTION, query=sparse, using="bm25", limit=limit
                ).points
            else:
                points = self._client.query_points(
                    COLLECTION,
                    prefetch=[
                        models.Prefetch(query=dense, using="dense", limit=limit * 2),
                        models.Prefetch(query=sparse, using="bm25", limit=limit * 2),
                    ],
                    query=models.FusionQuery(fusion=models.Fusion.RRF),
                    limit=limit,
                ).points
        return [(self.passages[int(p.id)], float(p.score)) for p in points]
