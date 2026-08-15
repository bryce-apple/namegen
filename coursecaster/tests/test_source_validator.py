"""Every source-validator failure, asserting the specific error (§9)."""

import unittest

from coursecaster.registers import TermRegister
from coursecaster.source_validator import validate_sources
from tests.helpers import CONTENT, sample_plan, sample_sources


def codes(plan, sources, register=None):
    return [e.code for e in validate_sources(plan, sources, register).errors]


class TestSourceValidator(unittest.TestCase):
    def setUp(self):
        self.plan = sample_plan()

    def test_clean_sample_passes(self):
        register = TermRegister({"classified balance sheet": "PFMA-U01-L1-S1"})
        self.assertEqual(codes(self.plan, sample_sources(), register), [])

    def check(self, expected_code, replacement, target="PFMA-U01-L1-S1",
              needle=None):
        text = CONTENT.replace(needle, replacement) if needle else replacement
        sources = sample_sources({target: text})
        self.assertIn(expected_code, codes(self.plan, sources))

    def test_unknown_block(self):
        self.check("SRC-UNKNOWN-BLOCK",
                   ":::mystery\n:::\n\n:::summary", needle=":::summary")

    def test_unknown_attr(self):
        self.check("SRC-UNKNOWN-ATTR", ":::objective zone=theirs colour=red",
                   needle=":::objective zone=theirs")

    def test_missing_required_attr(self):
        self.check("SRC-MISSING-ATTR", ":::caution\nOops.\n:::\n\n:::summary",
                   needle=":::summary")

    def test_unrecognised_field_is_fatal_body(self):
        # A misspelled field name must not silently become body text.
        self.check("SRC-UNEXPECTED-BODY",
                   "caption: A comparison of statements.\nzzz: nope",
                   needle="caption: A comparison of statements.")

    def test_figure_without_alt(self):
        self.check("SRC-FIGURE-NO-ALT", "alt2: A balance sheet with sections highlighted.",
                   needle="alt: A balance sheet with sections highlighted.")

    def test_specified_without_brief(self):
        self.check("SRC-SPECIFIED-NO-BRIEF", "brief2: Diagram the classification.",
                   needle="brief: Diagram the classification.")

    def test_term_wrong_address(self):
        register = TermRegister({"classified balance sheet": "PFMA-U99-L9-S9"})
        result = codes(self.plan, sample_sources(), register)
        self.assertIn("SRC-TERM-WRONG-ADDRESS", result)

    def test_term_duplicate_course_wide(self):
        intro = ("---\naddress: PFMA-U01-L1-S0\ntitle: Introduction\n---\n\n"
                 "Also {{term:classified balance sheet|Again.}} here.\n")
        sources = sample_sources({"PFMA-U01-L1-S0": intro})
        self.assertIn("SRC-TERM-DUP", codes(self.plan, sources))

    def test_xref_unknown_address(self):
        self.check("SRC-XREF-UNKNOWN", "{{xref:PFMA-U77-L7-S7}}",
                   needle="{{xref:PFMA-U01-L1-S1-F1}}")

    def test_flipcard_anchor_no_heading(self):
        self.check(
            "SRC-FLIPCARD-ANCHOR",
            ":::flipcard anchor=\"No Such Heading\"\nq: Q?\na: A.\n:::\n\n"
            ":::summary", needle=":::summary")

    def test_flipcard_anchor_matches(self):
        sources = sample_sources({"PFMA-U01-L1-S1": CONTENT.replace(
            ":::summary",
            ":::flipcard anchor=\"Reading the Statement\"\nq: Q?\na: A.\n:::\n\n"
            ":::summary")})
        self.assertNotIn("SRC-FLIPCARD-ANCHOR", codes(self.plan, sources))

    def test_authored_number(self):
        self.check("SRC-AUTHORED-NUMBER", "As Figure 3.1 shows, organizes accounts.",
                   needle="organizes accounts.")

    def test_frontmatter_address_mismatch(self):
        self.check("SRC-ADDRESS-MISMATCH", "address: PFMA-U01-L1-S9",
                   needle="address: PFMA-U01-L1-S1")

    def test_missing_objective(self):
        text = CONTENT.replace(":::objective zone=theirs", ":::xml").replace(
            "- Understand the balance sheet.\n- Interpret comparative statements.",
            "<para id=\"x\">x</para>")
        self.assertIn("SRC-MISSING-OBJECTIVE",
                      codes(self.plan, sample_sources({"PFMA-U01-L1-S1": text})))

    def test_missing_summary(self):
        text = CONTENT.replace(
            ":::summary\nThe statements interlock.\n:::", "")
        self.assertIn("SRC-MISSING-SUMMARY",
                      codes(self.plan, sample_sources({"PFMA-U01-L1-S1": text})))

    def test_intro_exempt_from_objective_summary(self):
        result = codes(self.plan, sample_sources())
        self.assertNotIn("SRC-MISSING-OBJECTIVE", result)
        self.assertNotIn("SRC-MISSING-SUMMARY", result)

    def test_guid_suffix_activity(self):
        # An activity guid carrying the material suffix (…1x3) is exactly
        # the transposition §5.6 warns about.
        text = CONTENT.replace(
            ":::activity status=proposed owner=unassigned address=PFMA-U01-L1-S1-A1",
            ":::activity guid=g23bca57e6c5a8001x3")
        self.assertIn("SRC-GUID-SUFFIX",
                      codes(self.plan, sample_sources({"PFMA-U01-L1-S1": text})))

    def test_manifest_guid_suffix(self):
        plan = sample_plan()
        plan.manifest[0].guid = "g2ec4e2b6b5a20001x3"     # activity with 1x3
        self.assertIn("SRC-GUID-SUFFIX", codes(plan, sample_sources()))

    def test_missing_file_and_orphan(self):
        sources = sample_sources()
        del sources["PFMA-U01-L1-S0"]
        sources["PFMA-U09-L9-S9"] = sources["PFMA-U01-S0"]
        result = codes(self.plan, sources)
        self.assertIn("SRC-MISSING-FILE", result)
        self.assertIn("SRC-ORPHAN-FILE", result)

    def test_ref_status_mismatch(self):
        text = CONTENT.replace(
            ":::figure formal=true status=specified owner=pipeline address=PFMA-U01-L1-S1-F1",
            ":::figure formal=true status=resolved src=x.png owner=pipeline address=PFMA-U01-L1-S1-F1")
        self.assertIn("SRC-REF-STATUS-MISMATCH",
                      codes(self.plan, sample_sources({"PFMA-U01-L1-S1": text})))

    def test_terms_first_use_mismatch(self):
        text = CONTENT.replace("terms_first_use: [classified balance sheet]",
                               "terms_first_use: []")
        self.assertIn("SRC-TERMS-FIRST-USE",
                      codes(self.plan, sample_sources({"PFMA-U01-L1-S1": text})))


if __name__ == "__main__":
    unittest.main()
