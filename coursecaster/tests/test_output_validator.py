"""Output validator (§7): vocabulary, token reconciliation both
directions, PENDING-CAST incompleteness, structure, round-trip counts."""

import unittest

from coursecaster.cast import cast_course
from coursecaster.output_validator import validate_output
from tests.helpers import CONTENT, sample_plan, sample_sources


def codes(xml, plan=None, sources=None, report=None):
    errors, rep = validate_output(xml, plan, sources, report)
    return [e.code for e in errors.errors], rep


class TestOutputValidator(unittest.TestCase):
    def build(self, plan=None, overrides=None):
        plan = plan or sample_plan()
        sources = sample_sources(overrides)
        result = cast_course(plan, sources)
        return result, plan, sources

    def test_clean_build_passes(self):
        result, plan, sources = self.build()
        got, rep = codes(result.xml, plan, sources, result.report)
        self.assertEqual(got, [])
        self.assertFalse(rep["incomplete"])

    def test_malformed(self):
        got, _ = codes("<book><unclosed></book>")
        self.assertEqual(got, ["OUT-MALFORMED"])

    def test_vocabulary_catches_misspelled_element(self):
        # The corpus ships a live <emphais>; a passthrough block is the one
        # road unrecognised markup can ride in on — the validator reports it.
        text = CONTENT.replace(
            ":::summary",
            ":::xml\n<para id=\"zz9zz\">an <emphais>oops</emphais></para>\n:::\n\n"
            ":::summary")
        result, plan, sources = self.build(overrides={"PFMA-U01-L1-S1": text})
        got, _ = codes(result.xml, plan, sources, result.report)
        self.assertIn("OUT-VOCABULARY", got)

    def test_passthrough_reported(self):
        text = CONTENT.replace(
            ":::summary",
            ":::xml\n<para id=\"zz9zz\">verbatim</para>\n:::\n\n:::summary")
        result, plan, sources = self.build(overrides={"PFMA-U01-L1-S1": text})
        _, rep = codes(result.xml, plan, sources, result.report)
        self.assertEqual(len(rep["passthrough"]), 1)
        self.assertEqual(rep["passthrough"][0]["address"], "PFMA-U01-L1-S1")

    def test_never_emit_label(self):
        result, plan, sources = self.build()
        bad = result.xml.replace("<chapter id=\"PFMA-U01\">",
                                 "<chapter label=\"Unit 1\" id=\"PFMA-U01\">")
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-NEVER-EMIT", got)

    def test_never_emit_paracount(self):
        result, plan, sources = self.build()
        bad = result.xml.replace(
            "<chapter id=\"PFMA-U01\">",
            "<chapter me:paracount=\"5\" id=\"PFMA-U01\">")
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-NEVER-EMIT", got)

    def test_token_reconciliation_missing_token(self):
        # Manifest says specified, output carries no token → both-directions
        # check fails.
        result, plan, sources = self.build()
        bad = result.xml.replace('guid="PENDING:PFMA-U01-L1-QZ"',
                                 'guid="g2ec4e2b6b5a20001x2"')
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-TOKEN-COUNT", got)

    def test_token_reconciliation_unknown_address(self):
        result, plan, sources = self.build()
        bad = result.xml.replace("PENDING:PFMA-U01-L1-QZ",
                                 "PENDING:PFMA-U88-QZ")
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-TOKEN-UNKNOWN", got)
        self.assertIn("OUT-TOKEN-COUNT", got)

    def test_video_expects_two_tokens(self):
        result, plan, sources = self.build()
        bad = result.xml.replace('fileref="PENDING:PFMA-U01-L1-S1-V1"',
                                 'fileref="123"')
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-TOKEN-COUNT", got)

    def test_pending_cast_marks_incomplete(self):
        text = CONTENT.replace(
            ":::summary",
            ":::flipcard anchor=\"Reading the Statement\"\nq: Q?\na: A.\n:::\n\n"
            ":::summary")
        result, plan, sources = self.build(overrides={"PFMA-U01-L1-S1": text})
        got, rep = codes(result.xml, plan, sources, result.report)
        self.assertIn("OUT-PENDING-CAST", got)
        self.assertTrue(rep["incomplete"])

    def test_structure_intro_terminal(self):
        result, plan, sources = self.build()
        bad = result.xml.replace('<section label="" id="PFMA-U01-S0">',
                                 '<section id="PFMA-U01-S0">')
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-STRUCTURE", got)

    def test_structure_wrong_order(self):
        plan = sample_plan()
        plan.units[0].lessons[0].subsections.reverse()
        result, _, sources = self.build()
        got, _ = codes(result.xml, plan, sources, result.report)
        self.assertIn("OUT-STRUCTURE", got)

    def test_roundtrip_counts(self):
        result, plan, sources = self.build()
        bad = result.xml.replace(
            "<glossentry", "<removedentry").replace("</glossentry>",
                                                    "</removedentry>")
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-ROUNDTRIP", got)

    def test_dangling_xref(self):
        result, plan, sources = self.build()
        bad = result.xml.replace('linkend="PFMA-U01-L1-S1-F1"',
                                 'linkend="chatper01"')
        got, _ = codes(bad, plan, sources, result.report)
        self.assertIn("OUT-XREF-DANGLING", got)


if __name__ == "__main__":
    unittest.main()
