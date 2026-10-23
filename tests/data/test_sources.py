"""The dataset registry and the raw/processed layout. No network."""

import hashlib
import re
from pathlib import Path

import pytest

from raredx.data import sources

REGISTRY = Path(__file__).resolve().parents[2] / "evals" / "datasets.toml"


def test_every_registered_source_is_pinned_and_verifiable() -> None:
    registry = sources.load_sources(REGISTRY)
    assert {"phenopacket-store", "hpo"} <= set(registry)
    for source in registry.values():
        assert source.files, source.name
        for name, sha256 in source.files.items():
            assert re.fullmatch(r"[0-9a-f]{64}", sha256), f"{source.name}/{name}"
        assert source.url.startswith("https://") and source.url.endswith("/"), source.name
        if source.fetched_by:  # read page by page; a manifest in git pins each page
            continue
        if not source.latest_only:  # the address names the version, or each file does
            named = source.version in source.url or all(source.version in n for n in source.files)
            assert named, f"{source.name}: neither url nor files name the version"
        assert source.license, source.name


def test_raw_and_processed_paths_are_versioned(tmp_path: Path) -> None:
    source = sources.load_sources(REGISTRY)["phenopacket-store"]
    assert sources.raw_dir(source, tmp_path) == (
        tmp_path / "raw" / "phenopacket-store" / source.version
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


def test_fetch_verifies_files_already_present_without_downloading(tmp_path: Path) -> None:
    source = sources.Source(
        name="toy",
        version="1",
        url="https://example.invalid/1/",  # never contacted: both files are present
        files={},
        homepage="",
        license="CC0",
        role="test",
    )
    folder = sources.raw_dir(source, tmp_path)
    folder.mkdir(parents=True)
    for name in ("a.txt", "b.txt"):
        (folder / name).write_text(name)
        source.files[name] = sources.sha256_of(folder / name)
    assert sources.fetch(source, tmp_path) == [folder / "a.txt", folder / "b.txt"]
    (folder / "b.txt").write_text("changed")
    with pytest.raises(ValueError, match="sha256"):
        sources.fetch(source, tmp_path)


def test_a_source_built_by_a_command_is_verified_never_downloaded(tmp_path: Path) -> None:
    source = sources.Source(
        name="wiki",
        version="1",
        url="https://unreachable.invalid/",
        files={"pages.jsonl.gz": hashlib.sha256(b"pages").hexdigest()},
        homepage="",
        license="",
        role="",
        fetched_by="raredx data wikipedia",
    )
    with pytest.raises(FileNotFoundError, match="raredx data wikipedia"):
        sources.fetch(source, tmp_path)
    (sources.raw_dir(source, tmp_path) / "pages.jsonl.gz").parent.mkdir(parents=True)
    (sources.raw_dir(source, tmp_path) / "pages.jsonl.gz").write_bytes(b"pages")
    assert sources.fetch(source, tmp_path) == [sources.raw_dir(source, tmp_path) / "pages.jsonl.gz"]
