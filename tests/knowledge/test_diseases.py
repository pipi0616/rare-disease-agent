"""Disease identity: Mondo's exact matches between OMIM and Orphanet ids."""

from raredx.knowledge.diseases import Identity


def test_ids_matched_exactly_to_one_mondo_class_are_the_same_disease(identity: Identity) -> None:
    assert identity.same("OMIM:690001") == {"OMIM:690001", "ORPHA:9001"}
    assert identity.same("ORPHA:9001") == {"OMIM:690001", "ORPHA:9001"}
    assert identity.mondo("ORPHA:9001") == "MONDO:9000001"


def test_orphanet_codes_are_written_as_orpha(identity: Identity) -> None:
    assert identity.same("OMIM:699998") == {"OMIM:699998", "ORPHA:9002"}
    assert identity.mondo("Orphanet:9002") is None


def test_only_exact_matches_to_omim_or_orphanet_count(identity: Identity) -> None:
    # a broader match is a different disease; another catalogue is not read
    assert identity.mondo("ORPHA:9005") is None and identity.mondo("DOID:9003") is None


def test_an_id_mondo_does_not_match_is_only_itself(identity: Identity) -> None:
    assert identity.same("OMIM:690003") == {"OMIM:690003"} and identity.mondo("OMIM:690003") is None
