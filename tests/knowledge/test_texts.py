"""Reading the disease texts: miniatures of Orphanet's and MedlinePlus's files."""

from pathlib import Path

from raredx.knowledge import texts

FIXTURES = Path(__file__).parents[1] / "fixtures" / "texts"


def test_orphanet_definitions_of_exactly_mapped_disorders_become_passages() -> None:
    passages = texts.orphanet(FIXTURES / texts.ORPHANET)
    assert [(p.disease_ids, p.source) for p in passages] == [
        (["OMIM:690001"], "Orphanet ORPHA:9101"),
        (["OMIM:690004"], "Orphanet ORPHA:9104"),
    ]  # a broader-term mapping, and a disorder without a definition, are left out
    assert passages[0].text == (
        "Hearing-ovarian syndrome. A rare syndrome of sensorineural hearing loss with "
        "ovarian failure and absent menstruation."
    )  # led by the name, markup removed


def test_medlineplus_descriptions_become_one_passage_per_paragraph() -> None:
    passages = texts.medlineplus(FIXTURES / texts.MEDLINEPLUS)
    assert [p.text for p in passages] == [
        "Hearing-retina syndrome. Hearing-retina syndrome causes hearing loss and night "
        "blindness from rod-cone dystrophy.",
        "Hearing-retina syndrome. It runs in families.",
    ]  # other text roles, and conditions without an OMIM key, are left out
    assert {p.source for p in passages} == {
        "https://medlineplus.gov/genetics/condition/hearing-retina-syndrome"
    }
    assert all(p.disease_ids == ["OMIM:690002"] for p in passages)


def test_read_gives_both_sources_orphanet_first() -> None:
    passages = texts.read(FIXTURES, FIXTURES)
    assert [p.source.split()[0] for p in passages[:2]] == ["Orphanet", "Orphanet"]
    assert len(passages) == 4
