"""Reading the text sources into documents: sections, paragraphs, the papers each cites."""

from pathlib import Path

from raredx.knowledge import corpus
from raredx.knowledge.hpo import HPO

CHAPTER = b"""<book-part-wrapper content-type="chapter" id="xyz">
<book-part><book-part-meta>
  <title-group><title>Xyz Syndrome</title></title-group>
  <abstract><sec><title>Clinical characteristics</title><p>Xyz syndrome causes hearing loss
  [<xref ref-type="bibr" rid="xyz.REF.a">A et al 2020</xref>].</p></sec>
  <sec><title>Management</title><p>Hearing aids.</p></sec></abstract>
</book-part-meta>
<body>
  <sec><title>Diagnosis</title><p>Suspect it in a child with night blindness.</p>
    <sec><title>Suggestive Findings</title><list><list-item><p>Retinal dystrophy
    [<xref ref-type="bibr" rid="xyz.REF.b">B 2021</xref>]</p></list-item></list></sec></sec>
  <sec><title>Genetic Counseling</title>
    <p>It is inherited in an autosomal recessive manner.</p></sec>
  <sec><title>Management</title><p>Treat the symptoms.</p></sec>
  <sec><title>References</title><ref-list><ref id="xyz.REF.a"><mixed-citation>A.
    <pub-id pub-id-type="pmid">111</pub-id></mixed-citation></ref>
    <ref id="xyz.REF.b"><mixed-citation>B. <pub-id pub-id-type="pmid">222</pub-id>
    </mixed-citation></ref></ref-list></sec>
</body></book-part></book-part-wrapper>"""


def test_a_genereviews_chapter_keeps_its_sections_and_each_paragraphs_papers() -> None:
    doc = corpus.genereviews_chapter(CHAPTER, "xyz", "NBK1", ["OMIM:690001"])
    assert doc is not None and doc.title == "Xyz Syndrome" and doc.url.endswith("NBK1")
    titles = [s.title for s in doc.sections]
    assert titles == [
        "Summary — Clinical characteristics",
        "Diagnosis",
        "Diagnosis — Suggestive Findings",
        "Genetic Counseling",
    ]  # treatment and the references left out, at every level
    cited = {p.text[:12]: p.pmids for s in doc.sections for p in s.paragraphs}
    assert cited["Xyz syndrome"] == ["PMID:111"] and cited["Retinal dyst"] == ["PMID:222"]
    assert cited["Suspect it i"] == []


PAGE = {
    "title": "Xyz syndrome",
    "revid": 42,
    "orpha": ["ORPHA:9001"],
    "omim": [],
    "html": """<div class="mw-parser-output">
<table class="infobox"><tr><td>Specialty</td></tr></table>
<p>Xyz syndrome is a rare disorder of hearing.<sup class="reference">
<a href="#cite_note-1">[1]</a></sup></p>
<div class="mw-heading mw-heading2"><h2>Signs and symptoms</h2></div>
<ul><li>Night blindness, from early childhood</li></ul>
<div class="mw-heading mw-heading2"><h2>References</h2></div>
<ol class="references"><li id="cite_note-1">
<a href="https://pubmed.ncbi.nlm.nih.gov/333">333</a></li></ol>
</div>""",
}


def test_a_wikipedia_article_reads_into_sections_with_its_footnotes_papers() -> None:
    doc = corpus.wikipedia_article(PAGE)
    assert doc is not None and doc.url.endswith("oldid=42")
    assert [s.title for s in doc.sections] == ["", "Signs and symptoms"]  # not the references
    lead = doc.sections[0].paragraphs[0]
    assert lead.text == "Xyz syndrome is a rare disorder of hearing." and lead.pmids == ["PMID:333"]
    assert "Specialty" not in " ".join(p.text for s in doc.sections for p in s.paragraphs)


def test_mondo_definitions_are_about_the_ids_their_class_matches(tmp_path: Path) -> None:
    obo = tmp_path / "mondo.obo"
    obo.write_text(
        '[Term]\nid: MONDO:9000001\nname: xyz syndrome\ndef: "A syndrome of hearing." '
        "[PMID:444, https://x]\n\n[Term]\nid: MONDO:0000002\nname: unmatched\n"
        'def: "Something." []\n',
        encoding="utf-8",
    )
    members = {"MONDO:9000001": frozenset({"OMIM:690001", "ORPHA:9001"})}
    [doc] = corpus.mondo(obo, members)
    assert doc.disease_ids == ["OMIM:690001", "ORPHA:9001"]
    assert doc.sections[0].paragraphs[0].pmids == ["PMID:444"]


def test_documents_are_named_by_the_knowledges_diseases_or_dropped(knowledge: HPO) -> None:
    def doc(ids: list[str]) -> corpus.Document:
        return corpus.Document(id="x", source="t", title="t", disease_ids=ids, sections=[])

    [kept] = corpus.resolve([doc(["ORPHA:9001", "OMIM:690001"]), doc(["OMIM:600000"])], knowledge)
    assert kept.disease_ids == ["OMIM:690001"]  # ORPHA:9001 is merged into it
