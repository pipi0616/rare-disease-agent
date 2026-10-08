"""Dataset sources: what evals/datasets.toml says, where each file lives, how it is fetched.

Layout under the data directory, one folder per source and version:

    raw/<source>/<version>/<file>              as downloaded; never modified
    processed/<source>/<version>/cases.jsonl   built from raw by code; safe to delete

Every raw file is verified against its sha256 in the registry. A download that
does not match is deleted rather than used.
"""

import hashlib
import tomllib
from pathlib import Path

import httpx
from pydantic import BaseModel


class Source(BaseModel):
    name: str
    version: str
    url: str  # the release folder; each file is downloaded from url + its name
    files: dict[str, str]  # file name -> sha256
    homepage: str
    license: str
    role: str


def load_sources(path: Path) -> dict[str, Source]:
    with path.open("rb") as f:
        entries = tomllib.load(f)
    return {name: Source(name=name, **fields) for name, fields in entries.items()}


def raw_dir(source: Source, data_dir: Path) -> Path:
    return data_dir / "raw" / source.name / source.version


def processed_dir(source: Source, data_dir: Path) -> Path:
    return data_dir / "processed" / source.name / source.version


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, expected: str) -> None:
    actual = sha256_of(path)
    if actual != expected:
        raise ValueError(f"{path}: sha256 {actual} != expected {expected}")


def fetch(source: Source, data_dir: Path, *, force: bool = False) -> list[Path]:
    """Download the source's files into the raw layer and verify each. Idempotent."""
    return [
        _fetch_file(source.url + name, raw_dir(source, data_dir) / name, sha256, force=force)
        for name, sha256 in source.files.items()
    ]


def _fetch_file(url: str, target: Path, sha256: str, *, force: bool) -> Path:
    if target.exists() and not force:
        verify(target, sha256)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    try:
        verify(tmp, sha256)
    except ValueError:
        tmp.unlink()
        raise
    tmp.replace(target)
    return target
