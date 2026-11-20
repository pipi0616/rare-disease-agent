"""The case-report build's rules, on small examples: no network, no model."""

from datetime import date
from pathlib import Path

import pytest

from raredx.data import casereports as cr
from raredx.knowledge.diseases import Identity

SSSOM = """# a miniature of Mondo's mappings
subject_id\tsubject_label\tpredicate_id\tobject_id\tobject_label\tmapping_justification
MONDO:1\tMarfan syndrome\tskos:exactMatch\tOMIM:154700\t\tx
MONDO:1\tMarfan syndrome\tskos:exactMatch\tOrphanet:558\t\tx
MONDO:1\tMarfan syndrome\tskos:exactMatch\tmesh:D008382\t\tx
MONDO:2\tGout\tskos:exactMatch\tmesh:D006073\t\tx
MONDO:3\tFabry disease\tskos:exactMatch\tOMIM:301500\t\tx
MONDO:3\tFabry disease\tskos:exactMatch\tmesh:D000795\t\tx
MONDO:4\tGaucher disease\tskos:exactMatch\tOMIM:230800\t\tx
MONDO:4\tGaucher disease\tskos:exactMatch\tOrphanet:355\t\tx
MONDO:4\tGaucher disease\tskos:exactMatch\tmesh:D005776\t\tx
MONDO:9\tA group\tskos:broadMatch\tmesh:D999999\t\tx
"""


@pytest.fixture
def mesh(tmp_path: Path) -> cr.Mesh:
    path = tmp_path / "mondo.sssom.tsv"
    path.write_text(SSSOM, encoding="utf-8")
    return cr.Mesh(path, Identity(path))


def test_mesh_ids_become_the_diseases_mondo_matches_exactly(mesh: cr.Mesh) -> None:
    assert mesh.mondo("MESH:D008382") == "MONDO:1"
    assert mesh.diseases("MONDO:1") == {"OMIM:154700", "ORPHA:558"}
    assert mesh.mondo("OMIM:301500") == "MONDO:3"  # an OMIM id PubTator3 gives directly
    assert mesh.mondo("MESH:D999999") is None  # a broader match is not the same disease
    assert mesh.diseases("MONDO:2") == frozenset()  # gout: in MeSH, not in OMIM or Orphanet


def test_annotations_are_read_per_passage_and_only_diseases() -> None:
    payload = {
        "PubTator3": [
            {
                "pmid": 7,
                "passages": [
                    {
                        "infons": {"type": "title"},
                        "text": "Marfan syndrome in a boy",
                        "annotations": [
                            {"infons": {"type": "Disease", "identifier": "MESH:D008382"}},
                            {"infons": {"type": "Gene", "identifier": "2200"}},
                        ],
                    },
                    {
                        "infons": {"type": "abstract"},
                        "text": "He had gout.",
                        "annotations": [
                            {"infons": {"type": "Disease", "identifier": "MESH:D006073"}},
                            {"infons": {"type": "Disease", "identifier": None}},
                        ],
                    },
                ],
            }
        ]
    }
    (paper,) = cr.read_annotations(payload)
    assert (paper.pmid, paper.title) == ("7", "Marfan syndrome in a boy")
    assert paper.title_diseases == ["MESH:D008382"]
    assert paper.abstract_diseases == ["MESH:D006073"]


def test_the_case_description_is_the_case_sections_paragraphs() -> None:
    def passage(section: str, kind: str, text: str, **infons: str) -> dict[str, object]:
        return {"infons": {"section_type": section, "type": kind, **infons}, "text": text}

    payload = [
        {
            "documents": [
                {
                    "passages": [
                        passage(
                            "TITLE", "front", "T", **{"article-id_pmc": "123", "license": "CC BY"}
                        ),
                        passage("CASE", "title_1", "Case presentation"),
                        passage("CASE", "paragraph", " A boy presented. "),
                        passage("FIG", "fig_caption", "Figure 1"),
                        passage("CASE", "paragraph", "He was tall."),
                        passage("DISCUSS", "paragraph", "Marfan syndrome is..."),
                    ]
                }
            ]
        }
    ]
    text = cr.read_bioc("7", payload)
    assert text is not None
    assert (text.pmcid, text.license) == ("PMC123", "CC BY")
    assert text.paragraphs == ["A boy presented.", "He was tall."]
    assert cr.read_bioc("7", [{"documents": []}]) is None


def test_sentences_split_at_full_stops_but_not_at_abbreviations() -> None:
    paragraphs = [
        "A 9-year-old boy was seen by Dr. Smith. His height was 1.52 m (Fig. 1). He was tall!",
        "Echo showed aortic dilation, e.g. at the root. No family history.",
    ]
    assert cr.sentences(paragraphs) == [
        "A 9-year-old boy was seen by Dr. Smith.",
        "His height was 1.52 m (Fig. 1).",
        "He was tall!",
        "Echo showed aortic dilation, e.g. at the root.",
        "No family history.",
    ]


def test_a_full_stop_set_against_the_next_sentence_still_ends_one() -> None:
    text = ["It met the Criteria.Furthermore, a mass was noted; the variant was p.Val50Met."]
    assert cr.sentences(text) == [
        "It met the Criteria.",
        "Furthermore, a mass was noted; the variant was p.Val50Met.",
    ]


def test_the_cut_is_before_the_first_sentence_that_names_the_disease_or_its_gene() -> None:
    long, short = cr.name_forms(["MARFAN SYNDROME; MFS", "Ehlers-Danlos syndrome, classic type"])
    assert "marfan syndrome" in long and "ehlers danlos syndrome" in long and short == {"MFS"}
    text = [
        "A tall boy presented with chest pain.",
        "His mother had lens dislocation.",
        "Sequencing found a variant in FBN1.",
        "Marfan syndrome was diagnosed.",
    ]
    assert cr.cut(text, None, long, short, ["FBN1"]) == 2  # the gene, before the name
    assert cr.cut(text, None, long, short, []) == 2  # "Sequencing found": a confirming test
    assert cr.cut(["He was tall.", "Marfan syndrome was diagnosed."], None, long, short, []) == 1
    assert cr.cut(text, 2, long, short, ["FBN1"]) == 1  # annotator B's sentence is earlier
    plain = ["He was tall.", "His lens was dislocated."]
    assert cr.cut(plain, 9, set(), set(), []) == 2  # a number past the end keeps everything
    assert cr.reveals("Features of Marfan-syndrome were noted", long, short, [])
    typed, _ = cr.name_forms(["Neurofibromatosis type 1", "Spinocerebellar ataxia 3", "Gout 2"])
    assert {"neurofibromatosis", "spinocerebellar ataxia"} <= typed and "gout" not in typed
    assert cr.reveals("the Neurofibromatosis Diagnostic Criteria", typed, set(), [])
    assert cr.reveals("MFS was suspected", long, short, [])
    assert not cr.reveals("the mfs score was low", long, short, [])  # an abbreviation, as written
    assert (
        cr.kept_text(text, 2)
        == "A tall boy presented with chest pain. His mother had lens dislocation."
    )


def test_the_cut_also_stops_at_a_sentence_that_reports_a_confirming_test() -> None:
    text = [
        "A man presented with fever and a rash.",
        "Routine blood tests showed anaemia; a chest radiograph was normal.",
        "A skin biopsy was taken.",
        "It showed vasculitis.",
    ]
    assert cr.cut(text, None, set(), set(), []) == 2
    for sentence in (
        "Blood cultures were negative.",
        "Tissue staining was positive for S100; immunohistochemistry followed.",
        "Bone marrow morphology revealed blasts: 39%.",
        "Trio whole exome sequencing revealed a de novo variant.",
        "FISH was requested.",
        "Antinuclear antibodies were positive at 1:1280.",
        "A heterozygous change was found.",
    ):
        assert cr.reports_a_test(sentence), sentence
    for sentence in (
        "He ate raw fish on a trip.",
        "Her cultural background was noted.",
        "An anatomical variant of the cystic duct was seen on imaging.",
        "He was given antibiotics.",
    ):
        assert not cr.reports_a_test(sentence), sentence


def test_a_disease_is_on_one_side_by_a_draw_fixed_beforehand() -> None:
    sides = [cr.side_of(f"MONDO:{i}") for i in range(2000)]
    assert sides == [cr.side_of(f"MONDO:{i}") for i in range(2000)]
    share = sides.count("exam") / len(sides)
    assert abs(share - cr.EXAM_SIZE / (cr.EXAM_SIZE + cr.DEV_SIZE)) < 0.04


def test_a_side_keeps_a_third_for_relatively_common_diseases() -> None:
    selection = cr.Selection({"exam": 6, "dev": 3})
    for i in range(4):
        assert selection.refusal("exam", f"rare{i}", common=False) is None
        selection.add("exam", f"rare{i}", common=False)
    assert "share of rarer" in (selection.refusal("exam", "rare9", common=False) or "")
    for _ in range(cr.PER_DISEASE):
        selection.add("dev", "x", common=True)
    assert "already" in (selection.refusal("exam", "x", common=True) or "")
    selection.add("exam", "c1", common=True)
    selection.add("exam", "c2", common=True)
    assert "full" in (selection.refusal("exam", "c3", common=True) or "")
    assert selection.full()


def builder(
    mesh: cr.Mesh, key: cr.Key | None, paragraphs: list[str], **changes: object
) -> cr.Builder:
    known = {
        "OMIM:154700": "OMIM:154700",
        "ORPHA:558": "OMIM:154700",
        "OMIM:301500": "OMIM:301500",
        "OMIM:230800": "OMIM:230800",
    }
    names = {"marfan syndrome": "OMIM:154700", "gaucher disease": "OMIM:230800"}
    settings: dict[str, object] = {
        "mesh": mesh,
        "canonical": known.get,
        "find": lambda name: tuple(filter(None, [names.get(name.lower())])),
        "names_of": lambda mondo: (
            ["Marfan syndrome", "MFS"] if mondo == "MONDO:1" else ["Fabry disease"]
        ),
        "genes_of": lambda disease: ["FBN1"] if disease == "OMIM:154700" else ["GLA"],
        "band_of": lambda disease: cr.COMMON if disease == "OMIM:154700" else "",
        "ask": lambda title, abstract, numbered: key,
        "fetch": lambda pmid: cr.FullText(
            pmid=pmid, pmcid="PMC1", license="", paragraphs=paragraphs
        ),
        "used": frozenset({"PMID:99"}),
        "cutoff": date(2025, 6, 1),
    }
    return cr.Builder(**(settings | changes))  # type: ignore[arg-type]


LONG = " ".join(["He had another finding on examination."] * 12)
STORY = [f"A tall boy presented with chest pain. {LONG}", "Sequencing found a variant in FBN1."]


def paper(pmid: str = "7", title: list[str] | None = None) -> cr.Abstract:
    return cr.Abstract(
        pmid=pmid,
        title="t",
        abstract="a",
        title_diseases=["MESH:D008382"] if title is None else title,
        abstract_diseases=["MESH:D006073"],
    )


def test_a_report_is_accepted_when_both_annotators_agree_and_is_cut(mesh: cr.Mesh) -> None:
    key = cr.Key(diagnosis="Marfan syndrome", patients=1, diagnostic=True, reveal=None)
    build = builder(mesh, key, STORY)
    row = build.process(paper(), date(2025, 7, 1))
    assert row is not None
    assert (row.id, row.pmid, row.side) == ("CaseReport_7", "PMID:7", cr.side_of("MONDO:1"))
    assert row.accepted_ids == ["OMIM:154700"] and row.band == cr.COMMON
    assert row.kept == 13  # every sentence before the one that names the gene
    assert "FBN1" not in build.texts[row.id]
    assert row.sha256 == cr.checksum(build.texts[row.id])
    assert build.log[-1].split("\t")[:2] == ["PMID:7", "accepted"]
    assert cr.read_table_text(cr.render_table([row])) == [row]


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"pmid": "99"}, "already used"),
        ({"day": date(2025, 5, 31)}, "not first public after the cutoff"),
        ({"title": ["MESH:D006073"]}, "no disease of the knowledge in the title"),
        (
            {"title": ["MESH:D000795"]},
            "no disease of the knowledge in the title",
        ),  # not in Orphanet
        ({"title": ["MESH:D008382", "MESH:D005776"]}, "more than one disease"),
        ({"key": None}, "unreadable"),
        (
            {"key": cr.Key(diagnosis="Marfan syndrome", patients=2, diagnostic=True)},
            "single patient",
        ),
        ({"key": cr.Key(diagnosis="Marfan syndrome", patients=1, diagnostic=False)}, "known from"),
        ({"key": cr.Key(diagnosis="Something else", patients=1, diagnostic=True)}, "not found"),
        ({"key": cr.Key(diagnosis="Gaucher disease", patients=1, diagnostic=True)}, "disagree"),
        (
            {"key": cr.Key(diagnosis="Marfan syndrome", patients=1, diagnostic=True, reveal=2)},
            "fewer",
        ),
        ({"paragraphs": []}, "no case description"),
    ],
)
def test_every_other_report_is_skipped_with_its_reason(
    mesh: cr.Mesh, change: dict[str, object], reason: str
) -> None:
    key = change.get("key", cr.Key(diagnosis="Marfan syndrome", patients=1, diagnostic=True))
    paragraphs = change.get("paragraphs", STORY)
    build = builder(mesh, key, paragraphs)  # type: ignore[arg-type]
    asked = paper(str(change.get("pmid", "7")), change.get("title"))  # type: ignore[arg-type]
    assert build.process(asked, change.get("day", date(2025, 7, 1))) is None  # type: ignore[arg-type]
    assert reason in build.log[-1] and not build.accepted


def test_nothing_is_fetched_or_asked_for_a_case_that_cannot_fit(mesh: cr.Mesh) -> None:
    def never(*_: object) -> None:
        raise AssertionError("fetched or asked")

    side = cr.side_of("MONDO:1")
    full = cr.Selection({side: 0, "dev" if side == "exam" else "exam": 5})
    build = builder(mesh, None, STORY, fetch=never, ask=never, selection=full)
    assert build.process(paper(), date(2025, 7, 1)) is None
    assert "side is full" in build.log[-1]


def test_mondo_names_hold_the_name_and_exact_synonyms(tmp_path: Path) -> None:
    obo = tmp_path / "mondo.obo"
    obo.write_text(
        "[Term]\nid: MONDO:1\nname: Marfan syndrome\n"
        'synonym: "MFS" EXACT ABBREVIATION [x]\nsynonym: "tall disease" RELATED [x]\n\n'
        "[Term]\nid: HP:1\nname: not a disease\n",
        encoding="utf-8",
    )
    assert cr.mondo_names(obo) == {"MONDO:1": ["Marfan syndrome", "MFS"]}


def test_a_name_is_found_by_any_of_its_forms_and_only_when_close() -> None:
    names = {"OMIM:1": "MARFAN SYNDROME; MFS", "OMIM:2": "Aspergillosis, allergic", "OMIM:3": "X"}
    synonyms = {"OMIM:2": ["allergic bronchopulmonary aspergillosis"]}
    index = cr.name_index(names, lambda disease: synonyms.get(disease, []))
    assert index["marfan syndrome"] == ("OMIM:1",) and "mfs" not in index  # too short to match
    assert cr.find_by_name("marfan's syndrome", index, 90) == ("OMIM:1",)
    assert cr.find_by_name("Allergic bronchopulmonary aspergillosis", index, 90) == ("OMIM:2",)
    assert cr.find_by_name("Gaucher disease type 1", index, 90) == ()
    # a long phrase that only contains a disease's name is not that disease
    phrase = "A forgotten foreign body in the bronchus that presented as allergic "
    phrase += "bronchopulmonary aspergillosis"
    assert cr.find_by_name(phrase, index, 90) == ()
    # two entries under one name are both what the name means
    shared = cr.name_index(
        {"OMIM:5": "CHARGE syndrome", "ORPHA:138": "CHARGE syndrome"}, lambda d: []
    )
    assert cr.find_by_name("CHARGE syndrome", shared, 90) == ("OMIM:5", "ORPHA:138")
    assert cr.ordered(["3", "1", "2"]) == cr.ordered(["2", "3", "1", "1"])


class FakeHttp:
    """Answers each request with the next of the given (status, body) pairs."""

    def __init__(self, *answers: tuple[int, str]) -> None:
        self.answers = list(answers)

    def get(self, url: str) -> object:
        import httpx

        status, body = self.answers.pop(0)
        return httpx.Response(status, text=body, request=httpx.Request("GET", url))


def test_a_busy_service_is_asked_again_and_never_taken_for_a_missing_paper() -> None:
    import httpx

    found = '[{"documents": [{"passages": [{"infons": {"article-id_pmc": "9"}, "text": "t"}]}]}]'
    again = FakeHttp((429, "busy"), (200, found))
    text = cr.full_text("7", again, pause=0, waits=(0,))  # type: ignore[arg-type]
    assert text is not None and text.pmcid == "PMC9"
    missing = FakeHttp((200, "[Error] : No result can be found."))
    assert cr.full_text("7", missing, pause=0, waits=(0,)) is None  # type: ignore[arg-type]
    busy = FakeHttp((429, "busy"), (429, "busy"))
    with pytest.raises(httpx.HTTPStatusError):
        cr.full_text("7", busy, pause=0, waits=(0,))  # type: ignore[arg-type]
