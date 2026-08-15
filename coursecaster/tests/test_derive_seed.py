"""Derivation scripts (§8) and seed generator, including the full
seed → validate → cast → validate loop on a fresh plan."""

import json
import tempfile
import unittest
from pathlib import Path

from coursecaster.cast import cast_course
from coursecaster.cli import load_sources
from coursecaster.derive import (coverage_matrix, example_ledger,
                                 reference_manifest, term_register)
from coursecaster.errors import CasterError
from coursecaster.output_validator import validate_output
from coursecaster.plan import load_plan_data
from coursecaster.seed import seed_course
from coursecaster.source_validator import validate_sources
from tests.helpers import sample_plan, sample_sources


class TestDerive(unittest.TestCase):
    def setUp(self):
        self.plan = sample_plan()
        self.sources = sample_sources()

    def test_term_register(self):
        reg = term_register(self.sources)
        self.assertEqual(reg["classified balance sheet"]["address"],
                         "PFMA-U01-L1-S1")

    def test_term_register_duplicate_fatal(self):
        dup = ("---\naddress: PFMA-U01-S0\ntitle: Introduction\n---\n\n"
               "A {{term:classified balance sheet|Again.}} here.\n")
        sources = sample_sources({"PFMA-U01-S0": dup})
        with self.assertRaises(CasterError):
            term_register(sources)

    def test_coverage_matrix(self):
        matrix = coverage_matrix(self.plan, self.sources)
        cell = matrix["skills"]["C1-S1"]["PFMA-U01-L1-S1"]
        self.assertEqual(cell, {"claim": "serves", "depth": "spine"})
        inst = matrix["skills"]["PCME-1.2.1"]["PFMA-U01-L1-S1"]
        self.assertEqual(inst["claim"], "instance")

    def test_reference_manifest(self):
        refs = reference_manifest(self.plan, self.sources)
        by_addr = {m["address"]: m for m in refs["manifest"]}
        self.assertEqual(by_addr["PFMA-U01-L1-S1-F1"]["referenced_by"],
                         ["PFMA-U01-L1-S1"])
        self.assertEqual(by_addr["PFMA-U01-L1-S1-F1"]["status"], "specified")

    def test_example_ledger(self):
        ledger = example_ledger(self.sources)
        self.assertEqual(ledger["examples"][0]["company"], "Acme")
        self.assertEqual(ledger["examples"][0]["period"], "FY2025")

    def test_json_deterministic(self):
        a = json.dumps(coverage_matrix(self.plan, self.sources), sort_keys=True)
        b = json.dumps(coverage_matrix(self.plan, sample_sources()),
                       sort_keys=True)
        self.assertEqual(a, b)


class TestSeed(unittest.TestCase):
    def test_seed_then_full_build(self):
        plan = sample_plan()
        # A freshly seeded course has no reference blocks yet; specified
        # figure/video manifest entries would (correctly) fail token
        # reconciliation, so the bring-up plan carries only the terminals.
        plan.manifest = [m for m in plan.manifest
                         if m.address.endswith("-QZ")]
        with tempfile.TemporaryDirectory() as tmp:
            written, warnings = seed_course(plan, tmp)
            self.assertEqual(len(written), 3)
            self.assertEqual(warnings, [])
            sources = load_sources(tmp)
            errors = validate_sources(plan, sources, None)
            self.assertEqual([e.code for e in errors.errors], [])
            result = cast_course(plan, sources)
            out_errors, rep = validate_output(result.xml, plan, sources,
                                              result.report)
            self.assertEqual([e.code for e in out_errors.errors], [])

    def test_seed_warns_on_rule_gaps(self):
        data = {
            "slug": "X", "title": "X",
            "units": [{"address": "X-U01", "title": "U",
                       "subsections": ["X-U01-S1"]}],
        }
        plan = load_plan_data(data)
        with tempfile.TemporaryDirectory() as tmp:
            _, warnings = seed_course(plan, tmp)
        self.assertEqual(len(warnings), 2)   # no *-S0 intro, no *-QZ entry

    def test_seed_never_clobbers(self):
        plan = sample_plan()
        with tempfile.TemporaryDirectory() as tmp:
            authored = Path(tmp) / "PFMA-U01-S0.md"
            authored.write_text("---\naddress: PFMA-U01-S0\ntitle: Mine\n---\n",
                                encoding="utf-8")
            seed_course(plan, tmp)
            self.assertIn("Mine", authored.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
