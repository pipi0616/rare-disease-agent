"""The readers, on the miniature HPO release, with a scripted model: nothing is paid."""

import json
from typing import Any

import pytest

from raredx.knowledge.hpo import HPO
from raredx.knowledge.text_index import TextIndex
from raredx.llm import Tally
from raredx.phenotyping.reader import (
    DictionaryReader,
    DirectReader,
    Finding,
    Label,
    NoteReader,
    labels,
    locate,
    name_matches,
    terms,
)


def mentions(*rows: tuple[str, str, str]) -> str:
    return json.dumps({"findings": [{"quote": q, "finding": f, "status": s} for q, f, s in rows]})


def links(codes: dict[int, str | None], checked: dict[str, str] | None = None) -> str:
    return json.dumps(
        {
            "codes": [{"n": n, "hpo_id": i} for n, i in codes.items()],
            "checked": [{"item": k, "status": v} for k, v in (checked or {}).items()],
        }
    )


def test_the_index_holds_names_and_close_synonyms_not_broad_ones(hpo: HPO) -> None:
    texts = {(n.text, n.hpo_id) for n in labels(hpo)}
    assert ("Hearing loss", "HP:0000365") in texts and ("Deafness", "HP:0000365") in texts
    assert ("Nerve deafness", "HP:0000407") not in texts  # BROAD
    assert not any(i == "HP:0000007" for _, i in texts)  # an inheritance: no finding


@pytest.mark.parametrize(
    ("quote", "where"),
    [
        ("cannot hear", (4, 15)),  # as written
        ("CANNOT HEAR", (4, 15)),  # whatever the case
        ("hear , well", (11, 20)),  # whatever the spacing and punctuation between words
        ("seizures", None),  # not in the text
    ],
)
def test_the_quoted_words_are_found_in_the_text(quote: str, where: Any) -> None:
    assert locate(quote, "She cannot hear well.") == where


def test_names_are_matched_longest_first_without_abbreviations(hpo: HPO) -> None:
    text = "Bilateral sensorineural hearing impairment, seizures and RCD."
    found = [(text[a:b], sorted(ids)) for a, b, ids in name_matches(text, hpo)]
    assert found == [
        ("Bilateral sensorineural hearing impairment", ["HP:0008619"]),  # not its parts
        ("seizures", ["HP:0001250"]),  # an exact synonym, the plural
    ]  # "RCD" is an abbreviation: in running text it may mean something else


def test_a_name_is_not_found_inside_a_hyphenated_word(hpo: HPO) -> None:
    text = "Pre-seizures, seizures-like and post-hearing loss; then seizures."
    assert [text[a:b] for a, b, _ in name_matches(text, hpo)] == ["seizures"]


def test_the_dictionary_reader_codes_every_name_it_finds(hpo: HPO) -> None:
    findings = DictionaryReader(hpo).read("Hearing loss and seizures.")
    assert [(f.quote, f.hpo_id, f.coded_by) for f in findings] == [
        ("Hearing loss", "HP:0000365", "dictionary"),
        ("seizures", "HP:0001250", "dictionary"),
    ]


def test_a_finding_named_as_hpo_names_it_needs_no_second_call(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    api = fake_llm(mentions(("seizures", "Seizure", "present")))
    findings = NoteReader(api, "m", hpo, term_index).read("She has seizures.")
    assert [(f.hpo_id, f.coded_by) for f in findings] == [("HP:0001250", "name")]
    assert len(api.requests) == 1


def test_the_model_picks_a_term_among_those_the_search_offers(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    api = fake_llm(
        mentions(("cannot hear in either ear", "Bilateral deafness", "present")),
        links({1: "HP:0008619"}),
    )
    [finding] = NoteReader(api, "m", hpo, term_index).read("He cannot hear in either ear.")
    assert (finding.hpo_id, finding.label, finding.coded_by) == (
        "HP:0008619",
        "Bilateral sensorineural hearing impairment",
        "model",
    )
    offered = api.requests[1]["messages"][1]["content"]
    assert 'Text: "cannot hear in either ear" | Finding: Bilateral deafness' in offered
    assert "HP:0008619 Bilateral sensorineural hearing impairment" in offered


def test_an_id_the_search_did_not_offer_is_not_taken(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    api = fake_llm(
        mentions(("cannot hear", "Deaf", "present")),
        links({1: "HP:0001252"}),  # a real HPO id, but not among the candidates
    )
    [finding] = NoteReader(api, "m", hpo, term_index).read("She cannot hear.")
    assert finding.hpo_id is None
    assert finding.uncoded == "the model chose HP:0001252, which was not offered"


def test_a_finding_whose_words_are_not_in_the_note_is_not_coded(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    api = fake_llm(mentions(("convulsions", "Seizure", "present")))
    [finding] = NoteReader(api, "m", hpo, term_index).read("She is well.")
    assert finding.hpo_id is None and finding.uncoded == "its words are not in the note"
    assert len(api.requests) == 1  # nothing to ask about it


def test_a_name_outside_the_findings_is_checked_by_the_model(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    text = "Seizures since birth. Her brother has hearing loss. Rod-cone dystrophy was excluded."
    api = fake_llm(
        mentions(("Seizures", "Seizure", "present")),
        links({}, {"A": "family", "B": "none"}),
    )
    findings = NoteReader(api, "m", hpo, term_index).read(text)
    assert [(f.hpo_id, f.status, f.coded_by) for f in findings] == [
        ("HP:0001250", "present", "name"),
        ("HP:0000365", "family", "dictionary"),
    ]  # "none": the model says the words do not state it
    asked = api.requests[1]["messages"][1]["content"]
    assert "A. HP:0000365 Hearing impairment\n   Written in: Her brother has hearing loss." in asked
    assert "B. HP:0000510 Rod-cone dystrophy" in asked


def test_a_name_inside_a_finding_takes_its_status_unless_it_says_less(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    text = "No bilateral sensorineural hearing loss with seizures."
    api = fake_llm(
        mentions(
            ("bilateral sensorineural hearing loss with seizures", "Bilateral SNHL", "absent")
        ),
        links({1: "HP:0008619"}),
    )
    findings = NoteReader(api, "m", hpo, term_index).read(text)
    # "hearing loss" is a more general name for the finding's own term: nothing added.
    # "seizures" says something else: added, absent like the finding it was found in.
    assert [(f.hpo_id, f.status, f.coded_by) for f in findings] == [
        ("HP:0008619", "absent", "model"),
        ("HP:0001250", "absent", "dictionary"),
    ]


def test_the_model_asked_for_ids_outright_is_taken_at_its_word(hpo: HPO, fake_llm: Any) -> None:
    reply = json.dumps(
        {
            "findings": [
                {"quote": "seizures", "hpo_id": "HP:0001250", "status": "present"},
                {"quote": "deaf", "hpo_id": "HP:0001730", "status": "present"},  # an alt id
                {"quote": "floppy", "hpo_id": "HP:9999999", "status": "present"},  # invented
                {"quote": "odd", "hpo_id": "hypotonia", "status": "present"},
            ]
        }
    )
    findings = DirectReader(fake_llm(reply), "m", hpo).read("seizures, deaf, floppy, odd")
    assert [(f.hpo_id, f.label) for f in findings] == [
        ("HP:0001250", "Seizure"),
        ("HP:0001730", "Hearing impairment"),
        ("HP:9999999", None),  # kept as given: scored as wrong
        (None, None),
    ]
    assert findings[3].uncoded == "not an HPO id: 'hypotonia'"


def test_the_present_terms_are_each_listed_once_in_order() -> None:
    findings = [
        Finding(quote="a", finding="A", hpo_id="HP:2", status="present"),
        Finding(quote="b", finding="B", hpo_id="HP:1", status="absent"),
        Finding(quote="c", finding="C", hpo_id="HP:2", status="present"),
        Finding(quote="d", finding="D", hpo_id="HP:3", status="present"),
        Finding(quote="e", finding="E"),
    ]
    assert terms(findings) == ["HP:2", "HP:3"]
    assert terms(findings, "absent") == ["HP:1"]


def test_a_tally_counts_the_calls_made_for_one_read(
    hpo: HPO, term_index: TextIndex[Label], fake_llm: Any
) -> None:
    from types import SimpleNamespace

    api = fake_llm(mentions(("seizures", "Seizure", "present")))
    create = api._create

    def with_usage(**request: Any) -> Any:
        response = create(**request)
        response.usage = SimpleNamespace(
            prompt_tokens=100, completion_tokens=20, prompt_cache_hit_tokens=60
        )
        return response

    api.chat.completions.create = with_usage
    tally = Tally()
    NoteReader(api, "m", hpo, term_index).read("She has seizures.", tally)
    assert (tally.model_calls, tally.input_tokens, tally.cached_input_tokens) == (1, 100, 60)
    assert tally.output_tokens == 20
