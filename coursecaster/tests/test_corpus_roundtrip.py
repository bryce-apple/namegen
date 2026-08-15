"""Corpus round-trip — the primary test (§9).

For each corpus XML: derive an equivalent source (uncast), cast it, and
assert structural equivalence with the original, comparing element trees
under corpuscmp's normalization (ids and me:paracount ignored, plus the
explicit rule list documented there).

Skips LOUDLY if the corpus samples are not present in coursecaster/corpus/
— the build is then unverified per §0 of the brief.
"""

import glob
import os
import unittest
import xml.etree.ElementTree as ET

from coursecaster import constants as C
from coursecaster.cast import cast_course
from coursecaster.corpuscmp import compare_trees
from coursecaster.mdparse import parse_text
from coursecaster.uncast import Uncaster

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")


def corpus_path(prefix):
    hits = sorted(glob.glob(os.path.join(CORPUS_DIR, prefix + "*.xml")))
    return hits[0] if hits else None


def require(test, prefix):
    path = corpus_path(prefix)
    if path is None:
        test.skipTest(
            f"CORPUS MISSING: no {prefix}*.xml in corpus/ — the build "
            "cannot be verified without the corpus samples (brief §0)")
    return path


def roundtrip(path, slug):
    root = ET.parse(path).getroot()
    un = Uncaster(root, slug)
    plan, texts = un.run()
    sources = {a: parse_text(t, a + ".md") for a, t in texts.items()}
    result = cast_course(plan, sources)
    cast_root = ET.fromstring(result.xml)
    diff = compare_trees(root, cast_root, expected_linkend_map=un.addr_map)
    return root, plan, result, cast_root, diff


def local(tag):
    return tag.split("}")[-1] if tag.startswith("{") else tag


class TestBusinessEthics(unittest.TestCase):
    """The no-labels, one-tier case."""

    def setUp(self):
        self.path = require(self, "2016")

    def test_roundtrip(self):
        root, plan, result, cast_root, diff = roundtrip(self.path, "BETH")
        self.assertIsNone(diff, f"round-trip divergence:\n{diff}")
        # one-tier: no nested chapters
        self.assertFalse(any(plan_unit.lessons for plan_unit in plan.units))
        # the corpus authors zero labels; our recast emits none either
        labels = [el for el in cast_root.iter() if "label" in el.attrib]
        self.assertEqual(labels, [])

    def test_recast_deterministic(self):
        _, _, a, _, _ = roundtrip(self.path, "BETH")
        _, _, b, _, _ = roundtrip(self.path, "BETH")
        self.assertEqual(a.xml.encode(), b.xml.encode())


class TestCom295T(unittest.TestCase):
    """The two-tier case."""

    def setUp(self):
        self.path = require(self, "com295T")

    def test_roundtrip(self):
        root, plan, result, cast_root, diff = roundtrip(self.path, "COM")
        self.assertIsNone(diff, f"round-trip divergence:\n{diff}")
        self.assertTrue(all(u.lessons for u in plan.units))
        # two-tier: nested chapters present in the recast
        nested = [c for c in cast_root.iter() if local(c.tag) == "chapter"]
        tops = [c for c in cast_root if local(c.tag) == "chapter"]
        self.assertGreater(len(nested), len(tops))


class TestStorytelling(unittest.TestCase):
    """The material-pairing case."""

    def setUp(self):
        self.path = require(self, "1761c")

    def test_roundtrip_and_pairing(self):
        root, plan, result, cast_root, diff = roundtrip(self.path, "STORY")
        self.assertIsNone(diff, f"round-trip divergence:\n{diff}")
        # every recast video is immediately followed by its me:material
        pairs = 0
        for parent in cast_root.iter():
            children = list(parent)
            for i, el in enumerate(children):
                if el.find("mediaobject/videoobject") is not None:
                    nxt = children[i + 1] if i + 1 < len(children) else None
                    self.assertIsNotNone(nxt)
                    self.assertEqual(local(nxt.tag), "material")
                    self.assertTrue(nxt.get("guid").endswith(
                        C.GUID_SUFFIXES["material"]))
                    pairs += 1
        self.assertEqual(pairs, 24)


class TestPatchStub(unittest.TestCase):
    """The second document type: same namespace URI, different prefix."""

    def setUp(self):
        self.path = require(self, "1761a")

    def test_prefix_independence(self):
        root = ET.parse(self.path).getroot()
        # bound to be:, not me: — resolution must go by URI (§7)
        self.assertEqual(root.tag, f"{{{C.NS_ME}}}patches")


if __name__ == "__main__":
    unittest.main()
