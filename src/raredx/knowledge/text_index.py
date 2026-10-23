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

Each record's diseases and cited papers are stored with its vectors (Qdrant's
payload), so a search can be filtered: to one disease's records, or without those
the evaluation masks — filtering inside the store, as access rules are applied in a
company's search.

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
MEMORY = ":memory:"
# Every vector compared, not an approximate (HNSW) neighbourhood: on a server the
# approximate search returns slightly different neighbours as its index is built in the
# background, and an evaluation must give the same answer twice. Exact search over
# 100,000 vectors still takes milliseconds.
EXACT = models.SearchParams(exact=True)
PASSAGES, DENSE, SPARSE, INFO = "passages.jsonl", "dense.npy", "sparse.jsonl", "index.json"
Mode = Literal["hybrid", "dense", "keyword"]


Sparse = tuple[list[int], list[float]]


class Embedder(Protocol):
    """Turns texts into a dense and a sparse vector each."""

    def passages(self, texts: list[str]) -> tuple[np.ndarray, list[Sparse]]: ...

    def query(self, text: str) -> tuple[list[float], Sparse]: ...


class FastEmbedder:
    """The two models, run locally by FastEmbed (ONNX); downloaded once into models_dir.
    Another dense model can be named (chapter 33 compares some); threads caps the CPU
    cores used, so a long embedding leaves the machine usable."""

    def __init__(
        self, models_dir: Path, dense_model: str = DENSE_MODEL, threads: int | None = None
    ) -> None:
        from fastembed import SparseTextEmbedding, TextEmbedding

        self.name = dense_model
        self.dense = TextEmbedding(dense_model, cache_dir=str(models_dir), threads=threads)
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
        location: str = MEMORY,
        collection: str = COLLECTION,
    ) -> None:
        """In memory (the default), the points are uploaded here and now. On a Qdrant
        server (location a URL), they are uploaded once into the named collection and
        found there the next time; chapter 33's indexes of tens of thousands of chunks
        are searched there, filtered, in milliseconds instead of a second."""
        self.passages = passages
        self.info = info
        self._embedder = embedder
        self._lock = (
            threading.Lock()
        )  # one search at a time: the embedded store is not built for more
        self._collection = collection
        if location == MEMORY:
            # Qdrant advises a server beyond 20,000 points in memory. The HPO terms'
            # names are 43,000: loaded in 5 s, searched in 0.1 s on a laptop.
            warnings.filterwarnings("ignore", message="Local mode is not recommended")
            self._client = QdrantClient(MEMORY)
        else:
            self._client = QdrantClient(url=location, timeout=120)
            if self._client.collection_exists(collection) and self._client.count(
                collection
            ).count == len(passages):
                return  # uploaded before
            if self._client.collection_exists(collection):
                self._client.delete_collection(collection)
        self._client.create_collection(
            collection,
            vectors_config={
                "dense": models.VectorParams(size=dense.shape[1], distance=models.Distance.COSINE)
            },
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        if location != MEMORY:  # a server filters through an index on each field
            for field in ("diseases", "pmids"):
                self._client.create_payload_index(
                    collection, field, field_schema=models.PayloadSchemaType.KEYWORD
                )
        self._client.upload_points(
            collection,
            (
                models.PointStruct(
                    id=i,
                    payload=_payload(passages[i]),
                    vector={
                        "dense": dense[i].tolist(),
                        "bm25": models.SparseVector(indices=sparse[i][0], values=sparse[i][1]),
                    },
                )
                for i in range(len(passages))
            ),
            batch_size=256,
        )

    @staticmethod
    def save(
        folder: Path,
        passages: Sequence[BaseModel],
        dense: np.ndarray,
        sparse: list[Sparse],
        info: dict[str, Any],
        dense_model: str = DENSE_MODEL,
    ) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / PASSAGES).open("w", encoding="utf-8") as f:
            for p in passages:
                f.write(p.model_dump_json() + "\n")
        np.save(folder / DENSE, dense)
        with (folder / SPARSE).open("w", encoding="utf-8") as f:
            for indices, values in sparse:
                f.write(json.dumps([indices, values]) + "\n")
        info = {**info, "passages": len(passages), "dense": dense_model, "sparse": SPARSE_MODEL}
        (folder / INFO).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(
        cls, folder: Path, embedder: Embedder, kind: type[T], location: str = MEMORY
    ) -> "TextIndex[T]":
        """The index saved in folder, its records read back as `kind`; on a server, in
        the collection named after the folder."""
        with (folder / PASSAGES).open(encoding="utf-8") as f:
            passages = [kind.model_validate_json(line) for line in f]
        with (folder / SPARSE).open(encoding="utf-8") as f:
            sparse: list[Sparse] = [(row[0], row[1]) for row in map(json.loads, f)]
        info = json.loads((folder / INFO).read_text(encoding="utf-8"))
        return cls(passages, np.load(folder / DENSE), sparse, embedder, info, location, folder.name)

    @classmethod
    def open(
        cls,
        folder: Path,
        models_dir: Path,
        kind: type[T],
        threads: int | None = None,
        location: str = MEMORY,
    ) -> "TextIndex[T]":
        """The index saved in folder, with the dense model it was embedded with."""
        info = json.loads((folder / INFO).read_text(encoding="utf-8"))
        embedder = FastEmbedder(models_dir, info["dense"], threads)
        return cls.load(folder, embedder, kind, location)

    def search(
        self,
        query: str,
        limit: int,
        mode: Mode = "hybrid",
        *,
        only: Sequence[str] = (),
        hide_diseases: Sequence[str] = (),
        hide_pmids: Sequence[str] = (),
    ) -> list[tuple[T, float]]:
        """The records best matching the query, best first, with their scores (RRF
        scores in hybrid mode; compare within one search only). Only records about the
        diseases in `only`, when given; never those about a hidden disease or citing a
        hidden paper."""
        must: list[models.Condition] = [_any("diseases", only)] if only else []
        must_not: list[models.Condition] = (
            [_any("diseases", hide_diseases)] if hide_diseases else []
        )
        must_not += [_any("pmids", hide_pmids)] if hide_pmids else []
        where = models.Filter(must=must, must_not=must_not) if must or must_not else None
        with self._lock:
            dense, (indices, values) = self._embedder.query(query)
            sparse = models.SparseVector(indices=indices, values=values)
            if mode == "dense":
                points = self._client.query_points(
                    self._collection,
                    query=dense,
                    using="dense",
                    limit=limit,
                    query_filter=where,
                    search_params=EXACT,
                ).points
            elif mode == "keyword":
                points = self._client.query_points(
                    self._collection, query=sparse, using="bm25", limit=limit, query_filter=where
                ).points
            else:  # each list from the store, fused here: see _fuse
                lists = [
                    self._client.query_points(
                        self._collection,
                        query=vector,
                        using=using,
                        limit=limit * 2,
                        query_filter=where,
                        search_params=EXACT if using == "dense" else None,
                    ).points
                    for vector, using in ((dense, "dense"), (sparse, "bm25"))
                ]
                return [(self.passages[i], score) for i, score in _fuse(lists, limit)]
        return [(self.passages[int(p.id)], float(p.score)) for p in points]


def _fuse(lists: Sequence[Sequence[Any]], limit: int) -> list[tuple[int, float]]:
    """Reciprocal-rank fusion as Qdrant computes it (1 / (2 + rank), rank from 0),
    with ties broken by the record's position in the index. Qdrant's own fusion leaves
    the order of equal scores to chance — two of its segments are searched in
    parallel — so the same search could rank tied records either way, and an
    evaluation run twice gave different numbers."""
    score: dict[int, float] = {}
    for points in lists:
        for rank, point in enumerate(points):
            score[int(point.id)] = score.get(int(point.id), 0.0) + 1 / (2 + rank)
    return sorted(score.items(), key=lambda item: (-item[1], item[0]))[:limit]


def _payload(record: BaseModel) -> dict[str, list[str]]:
    """What a search can filter on: the record's diseases and the papers it cites."""
    fields = record.model_dump()
    diseases = fields.get("disease_ids") or [d for d in [fields.get("disease_id")] if d]
    pmids = fields.get("pmids") or [p for p in [fields.get("pmid")] if p]
    return {"diseases": list(diseases), "pmids": list(pmids)}


def _any(key: str, values: Sequence[str]) -> models.FieldCondition:
    return models.FieldCondition(key=key, match=models.MatchAny(any=list(values)))
