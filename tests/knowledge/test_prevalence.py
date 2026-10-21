"""Orphanet's prevalence classes, read from files shaped like the real ones."""

from pathlib import Path
from xml.sax.saxutils import escape

from raredx.knowledge import prevalence


def prevalence_entry(
    kind: str, cls: str | None, where: str = "Worldwide", status: str = "Validated"
) -> str:
    found = (
        f"<PrevalenceClass><Name lang='en'>{escape(cls)}</Name></PrevalenceClass>"
        if cls
        else "<PrevalenceClass/>"
    )
    return (
        f"<Prevalence><PrevalenceType><Name lang='en'>{kind}</Name></PrevalenceType>{found}"
        f"<PrevalenceGeographic><Name lang='en'>{where}</Name></PrevalenceGeographic>"
        f"<PrevalenceValidationStatus><Name lang='en'>{status}</Name></PrevalenceValidationStatus>"
        "</Prevalence>"
    )


def disorder(code: int, *entries: str) -> str:
    listed = f"<PrevalenceList>{''.join(entries)}</PrevalenceList>"
    return f"<Disorder><OrphaCode>{code}</OrphaCode>{listed}</Disorder>"


def test_each_disorder_takes_its_preferred_validated_measure(tmp_path: Path) -> None:
    path = tmp_path / prevalence.PREVALENCE
    path.write_text(
        "<JDBOR><DisorderList>"
        + disorder(  # point prevalence, worldwide, preferred to a region and to birth
            1,
            prevalence_entry("Prevalence at birth", "1-9 / 100 000"),
            prevalence_entry("Point prevalence", "<1 / 1 000 000", "Europe"),
            prevalence_entry("Point prevalence", "1-9 / 1 000 000"),
        )
        + disorder(2, prevalence_entry("Prevalence at birth", "1-5 / 10 000", "Netherlands"))
        + disorder(3, prevalence_entry("Cases/families", None))  # known from a few families
        + disorder(
            4, prevalence_entry("Point prevalence", "1-9 / 100 000", status="Not yet validated")
        )
        + disorder(5, prevalence_entry("Point prevalence", "Unknown"))
        + "</DisorderList></JDBOR>"
    )
    assert prevalence.bands(path) == {
        "ORPHA:1": "1–9 in 1,000,000",
        "ORPHA:2": "1 in 100,000 or more",
        "ORPHA:3": "under 1 in 1,000,000",
    }
    assert prevalence.classes(path) == {  # Orphanet's own class, finer than the bands
        "ORPHA:1": "1-9 / 1 000 000",
        "ORPHA:2": "1-5 / 10 000",
        "ORPHA:3": "<1 / 1 000 000",
    }


def test_an_omim_disease_takes_its_exact_matches_most_common_class(tmp_path: Path) -> None:
    prevalences = tmp_path / prevalence.PREVALENCE
    prevalences.write_text(
        "<JDBOR><DisorderList>"
        + disorder(1, prevalence_entry("Point prevalence", "<1 / 1 000 000"))
        + disorder(2, prevalence_entry("Point prevalence", "1-9 / 1 000 000"))
        + disorder(3, prevalence_entry("Point prevalence", "1-5 / 10 000"))
        + "</DisorderList></JDBOR>"
    )

    def mapped(code: int, omim: str, relation: str) -> str:
        return (
            f"<Disorder><OrphaCode>{code}</OrphaCode><ExternalReferenceList><ExternalReference>"
            f"<Source>OMIM</Source><Reference>{omim}</Reference><DisorderMappingRelation>"
            f"<Name lang='en'>{relation}</Name></DisorderMappingRelation>"
            "</ExternalReference></ExternalReferenceList></Disorder>"
        )

    exact, narrower = "E (Exact mapping: the two concepts are equivalent)", "NTBT (narrower term)"
    disorders = tmp_path / "en_product1.xml"
    disorders.write_text(
        "<JDBOR><DisorderList>"
        + mapped(1, "100001", exact)
        + mapped(2, "100001", exact)  # two exact matches disagree: the more common class
        + mapped(3, "100002", narrower)  # not exact: not used
        + "</DisorderList></JDBOR>"
    )
    assert prevalence.omim_bands(prevalences, disorders) == {"OMIM:100001": "1–9 in 1,000,000"}
    assert prevalence.omim_classes(prevalences, disorders) == {"OMIM:100001": "1-9 / 1 000 000"}


def test_with_identity_an_omim_disease_takes_the_class_of_its_equal_orphanet_disorder(
    tmp_path: Path,
) -> None:
    prevalences = tmp_path / prevalence.PREVALENCE
    prevalences.write_text(
        "<JDBOR><DisorderList>"
        + disorder(536, prevalence_entry("Point prevalence", "1-5 / 10 000"))
        + disorder(81, prevalence_entry("Point prevalence", "1-9 / 100 000"))
        + "</DisorderList></JDBOR>"
    )
    disorders = tmp_path / "en_product1.xml"  # Orphanet maps neither exactly to OMIM
    disorders.write_text("<JDBOR><DisorderList></DisorderList></JDBOR>")

    def same(disease: str) -> set[str]:  # Mondo: ORPHA:536 is OMIM:152700
        pair = {"OMIM:152700", "ORPHA:536"}
        return pair if disease in pair else {disease}

    classes = prevalence.disease_classes(prevalences, disorders, same)
    assert classes["OMIM:152700"] == "1-5 / 10 000"  # through Mondo
    assert classes["ORPHA:81"] == "1-9 / 100 000"  # an Orphanet disease's own
    assert prevalence.disease_bands(prevalences, disorders, same)["OMIM:152700"] == (
        "1 in 100,000 or more"
    )
