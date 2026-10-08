"""The dataset registry and the raw/processed layout. No network."""

import re
from pathlib import Path

import pytest

from raredx.data import sources

REGISTRY = Path(__file__).resolve().parents[2] / "evals" / "datasets.toml"


def test_every_registered_source_is_pinned_and_verifiable() -> None:
    registry = sources.load_sources(REGISTRY)
    assert "phenopacket-store" in registry
    for source in registry.values():
        assert re.fullmatch(r"[0-9a-f]{64}", source.sha256), source.name
        assert source.url.startswith("https://"), source.name
        assert source.version in source.url, f"{source.name}: url does not name the pinned version"
        assert source.license, source.name


def test_raw_and_processed_paths_are_versioned(tmp_path: Path) -> None:
    source = sources.load_sources(REGISTRY)["phenopacket-store"]
    assert sources.raw_path(source, tmp_path) == (
        tmp_path / "raw" / "phenopacket-store" / source.version / "all_phenopackets.zip"
    )
    assert sources.processed_dir(source, tmp_path) == (
        tmp_path / "processed" / "phenopacket-store" / source.version
    )


def test_verify_rejects_a_tampered_file(tmp_path: Path) -> None:
    f = tmp_path / "x.zip"
    f.write_bytes(b"hello")
    sources.verify(f, sources.sha256_of(f))
    with pytest.raises(ValueError, match="sha256"):
        sources.verify(f, "0" * 64)
