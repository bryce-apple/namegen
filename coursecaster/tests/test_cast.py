"""Caster behavior: every block/inline construct, manifest emission by
status, caption/title transposition guard, GUID suffixes, determinism."""

import unittest
import xml.etree.ElementTree as ET

from coursecaster import constants as C
from coursecaster.cast import cast_course
from coursecaster.errors import CastError
from coursecaster.mdparse import parse_text
from tests.helpers import CONTENT, sample_plan, sample_sources

NS = {"me": C.NS_ME}


def build(plan=None, sources=None):
    plan = plan or sample_plan()
    sources = sources or sample_sources()
    result = cast_course(plan, sources)
    return result, ET.fromstring(result.xml)


def local(tag):
    return tag.split("}")[-1] if tag.startswith("{") else tag


class TestDeterminism(unittest.TestCase):
    def test_byte_identical_across_runs(self):
        a = cast_course(sample_plan(), sample_sources()).xml
        b = cast_course(sample_plan(), sample_sources()).xml
        self.assertEqual(a.encode(), b.encode())


class TestSkeleton(unittest.TestCase):
    def test_book_shape(self):
        _, root = build()
        self.assertEqual(local(root.tag), "book")
        children = [local(c.tag) for c in root]
        self.assertEqual(children[:2], ["option", "option"])
        self.assertIn("bookinfo", children)
        opts = {o.get("key"): o.get("value")
                for o in root.findall("me:option", NS)}
        self.assertEqual(opts["labeldefault:chapter"], "Unit {chapter-index}")

    def test_containers_and_ids(self):
        _, root = build()
        unit = root.find("chapter")
        self.assertEqual(unit.get("id"), "PFMA-U01")
        lesson = unit.find("chapter")
        self.assertEqual(lesson.get("id"), "PFMA-U01-L1")
        self.assertEqual(lesson.find("me:option", NS).get("value"),
                         "purchase_record")

    def test_no_labels_except_intro(self):
        # Business Ethics is the no-labels proof (§5.2): nothing carries a
        # label except label="" on introduction sections.
        _, root = build()
        for el in root.iter():
            if "label" in el.attrib:
                self.assertEqual(local(el.tag), "section")
                self.assertEqual(el.get("label"), "")
                self.assertTrue(el.get("id").endswith(C.INTRO_ADDRESS_SUFFIX))
        intro = root.find("chapter/section")
        self.assertEqual(intro.get("label"), "")

    def test_no_paracount_no_revhistory_no_glossary(self):
        result, root = build()
        self.assertNotIn("paracount", result.xml)
        for el in root.iter():
            self.assertNotIn(local(el.tag), ("revhistory", "glossary"))


class TestBlocks(unittest.TestCase):
    def setUp(self):
        self.result, self.root = build()
        self.sec = self.root.find(
            ".//section[@id='PFMA-U01-L1-S1']")

    def test_objective_sidebar(self):
        sb = self.sec.find("sidebar")
        self.assertEqual(sb.get("class"), C.OBJECTIVE_SIDEBAR_CLASS)
        self.assertEqual(sb.find("title").text, C.OBJECTIVE_SIDEBAR_TITLE)
        items = sb.findall("orderedlist/listitem")
        self.assertEqual(len(items), 2)

    def test_single_sentence_objective_is_para(self):
        text = CONTENT.replace(
            "- Understand the balance sheet.\n- Interpret comparative statements.",
            "Understand the balance sheet.")
        _, root = build(sources=sample_sources({"PFMA-U01-L1-S1": text}))
        sb = root.find(".//section[@id='PFMA-U01-L1-S1']/sidebar")
        self.assertIsNone(sb.find("orderedlist"))
        self.assertIsNotNone(sb.find("para"))

    def test_summary_is_section(self):
        summaries = [s for s in self.sec.findall("section")
                     if s.find("title").text == C.SUMMARY_SECTION_TITLE]
        self.assertEqual(len(summaries), 1)
        self.assertEqual(local(summaries[0][1].tag), "para")

    def test_admonition_no_attrs_with_title(self):
        note = self.sec.find(".//note")
        self.assertEqual(note.attrib, {})
        self.assertEqual(note.find("title").text, "Why it matters")
        self.assertIsNotNone(note.find("informalfigure"))

    def test_caption_title_not_transposed(self):
        # Tables take <caption>; figures take <title> (§5.7).
        table = self.sec.find(".//table")
        self.assertIsNotNone(table.find("caption"))
        self.assertIsNone(table.find("title"))
        figure = self.root.find(".//figure[@id='PFMA-U01-L1-S1-F1']")
        self.assertIsNotNone(figure.find("title"))
        self.assertIsNone(figure.find("caption"))

    def test_table_thead_th_direct(self):
        table = self.sec.find(".//table")
        self.assertEqual([local(c.tag) for c in table.find("thead")],
                         ["th", "th"])
        first_row = table.find("tbody/tr")
        self.assertEqual([local(c.tag) for c in first_row], ["th", "td"])

    def test_bare_markdown_table_informal(self):
        it = self.sec.find(".//informaltable")
        self.assertEqual([local(c.tag) for c in it], ["tbody"])

    def test_video_material_pair(self):
        # One component, two siblings, video first (§5.5).
        parent = self.sec.find(".//informalfigure[@id='PFMA-U01-L1-S1-V1']/..")
        kids = [(local(c.tag), c.get("id")) for c in parent]
        idx = kids.index(("informalfigure", "PFMA-U01-L1-S1-V1"))
        self.assertEqual(kids[idx + 1][0], "material")

    def test_equation_isolated(self):
        eq = self.sec.find(".//informalequation")
        self.assertEqual(eq.find("alt").text, "E = mc^2")

    def test_example_ledger_facts(self):
        self.assertEqual(self.result.report["examples"][0]["company"], "Acme")

    def test_glossentry_definition_is_trailing_text(self):
        ge = self.sec.find(".//glossentry")
        gt = ge.find("glossterm")
        self.assertEqual(gt.text, "classified balance sheet")
        self.assertEqual(gt.tail, "A balance sheet grouped into classes.")
        self.assertEqual(len(ge), 1)

    def test_inline_constructs(self):
        para = self.sec.find("para")
        tags = [local(c.tag) for c in para]
        for want in ("glossentry", "xref", "emphasis", "footnote"):
            self.assertIn(want, tags)
        xref = para.find("xref")
        self.assertEqual(xref.get("linkend"), "PFMA-U01-L1-S1-F1")
        self.assertIsNone(xref.text)          # no display text, ever
        bold = [e for e in para.findall("emphasis")
                if e.get("role") == "bold"]
        italic = [e for e in para.findall("emphasis") if e.get("role") is None]
        self.assertTrue(bold and italic)

    def test_credit_para_inside_title(self):
        text = CONTENT.replace(
            "alt: A balance sheet with sections highlighted.",
            "alt: A balance sheet with sections highlighted.\n"
            "credit: Photo by [P](https://e.com/p) via [Q](https://e.com/q).")
        _, root = build(sources=sample_sources({"PFMA-U01-L1-S1": text}))
        title = root.find(".//figure[@id='PFMA-U01-L1-S1-F1']/title")
        credit = title.find("para")
        self.assertEqual(credit.get("style"), C.CREDIT_PARA_STYLE)
        self.assertEqual(len(credit.findall("ulink")), 2)


class TestManifestEmission(unittest.TestCase):
    """Emission by each manifest status (§5.6), especially proposed →
    nothing."""

    def test_resolved_real_guid(self):
        _, root = build()
        qz = root.find(".//section[@id='PFMA-U01-QZ']")
        act = qz.find("me:activity", NS)
        self.assertEqual(act.get("guid"), "g2ec4e2b6b5a20001x2")
        self.assertEqual(len(act), 0)
        self.assertIsNone(act.text)

    def test_specified_token_never_empty_guid(self):
        result, root = build()
        act = root.find(".//section[@id='PFMA-U01-L1-QZ']/me:activity", NS)
        self.assertEqual(act.get("guid"), "PENDING:PFMA-U01-L1-QZ")
        self.assertNotIn('guid=""', result.xml)

    def test_proposed_emits_nothing(self):
        result, root = build()
        self.assertNotIn("PFMA-U01-L1-S1-A1", result.xml)

    def test_omitted_emits_nothing(self):
        plan = sample_plan()
        for m in plan.manifest:
            if m.address == "PFMA-U01-L1-S1-A1":
                m.status = "omitted"
        text = CONTENT.replace("status=proposed", "status=omitted")
        result = cast_course(plan, sample_sources({"PFMA-U01-L1-S1": text}))
        self.assertNotIn("PFMA-U01-L1-S1-A1", result.xml)

    def test_token_is_single_constant(self):
        self.assertEqual(C.pending_token("X"), "PENDING:X")
        self.assertEqual(C.parse_pending_token("PENDING:X"), "X")
        self.assertIsNone(C.parse_pending_token("g123x2"))

    def test_guid_suffix_enforced_at_cast(self):
        plan = sample_plan()
        for m in plan.manifest:
            if m.address == "PFMA-U01-QZ":
                m.guid = "g2ec4e2b6b5a20001x3"       # material suffix
        with self.assertRaises(CastError) as cm:
            cast_course(plan, sample_sources())
        self.assertEqual(cm.exception.code, "CAST-GUID-SUFFIX")


class TestFlipcard(unittest.TestCase):
    def test_pending_cast_marker(self):
        # §5.10: cast target unknown — marker emitted, isolated in one
        # function, and output validation must fail on it (covered in
        # test_output_validator).
        text = CONTENT.replace(
            ":::summary",
            ":::flipcard anchor=\"Reading the Statement\"\nq: Q?\na: A.\n:::\n\n"
            ":::summary")
        result = cast_course(sample_plan(),
                             sample_sources({"PFMA-U01-L1-S1": text}))
        self.assertIn(C.PENDING_CAST_MARKER, result.xml)
        self.assertEqual(result.report["pending_casts"][0]["type"], "flipcard")


if __name__ == "__main__":
    unittest.main()
