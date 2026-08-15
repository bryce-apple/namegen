import unittest

from coursecaster.errors import SourceError
from coursecaster.ids import IdAllocator, stable_id
from coursecaster.mdparse import parse_inlines, parse_text
from coursecaster.srcmodel import (
    Block, Bold, FootnoteRef, Heading, Italic, Link, ListNode, MarkdownTable,
    Para, TermDef, Text, Xref,
)


class TestIds(unittest.TestCase):
    def test_shape(self):
        for seed in ("a", "b", "PFMA|x|para|0"):
            i = stable_id(seed)
            self.assertRegex(i, r"^[a-z][a-z0-9]{4}$")

    def test_deterministic(self):
        a = IdAllocator("PFMA")
        b = IdAllocator("PFMA")
        seq_a = [a.allocate("X", "para") for _ in range(50)]
        seq_b = [b.allocate("X", "para") for _ in range(50)]
        self.assertEqual(seq_a, seq_b)
        self.assertEqual(len(set(seq_a)), 50)

    def test_scoped_by_address(self):
        # Editing one subsection must not churn ids in another: the id
        # depends on (address, tag, ordinal), not global document order.
        a = IdAllocator("PFMA")
        a.allocate("S1", "para")
        first_s2 = a.allocate("S2", "para")
        b = IdAllocator("PFMA")
        b.allocate("S1", "para")
        b.allocate("S1", "para")     # S1 grew a paragraph
        self.assertEqual(b.allocate("S2", "para"), first_s2)


class TestInlines(unittest.TestCase):
    def parse(self, s):
        return parse_inlines(s)

    def test_every_inline_construct(self):
        out = self.parse(
            "A {{term:x|Def.}} and {{xref:ADDR-1}} and **b** and *i* "
            "and [t](https://e.com) and [^1].")
        kinds = [type(n) for n in out]
        for kind in (TermDef, Xref, Bold, Italic, Link, FootnoteRef, Text):
            self.assertIn(kind, kinds)
        term = next(n for n in out if isinstance(n, TermDef))
        self.assertEqual((term.phrase, term.definition), ("x", "Def."))

    def test_escapes(self):
        out = self.parse(r"5 \* 3 and \[x\] and \{\{term")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].value, "5 * 3 and [x] and {{term")

    def test_bad_double_brace_fails(self):
        with self.assertRaises(SourceError) as cm:
            self.parse("{{glossary:x}}")
        self.assertEqual(cm.exception.code, "SRC-BAD-INLINE")


class TestBlocks(unittest.TestCase):
    def doc(self, body):
        return parse_text("---\naddress: A\ntitle: T\n---\n\n" + body, "A.md")

    def test_note_contains_figure(self):
        doc = self.doc(":::note title=\"N\"\nBody para.\n\n"
                       ":::figure formal=false src=x.png\nalt: A.\n:::\n:::\n")
        note = doc.children[0]
        self.assertEqual(note.type, "note")
        inner = [n for n in note.body if isinstance(n, Block)]
        self.assertEqual([b.type for b in inner], ["figure"])
        self.assertEqual(inner[0].fields["alt"], "A.")

    def test_unterminated_block_fatal(self):
        with self.assertRaises(SourceError) as cm:
            self.doc(":::note title=\"N\"\nnever closed\n")
        self.assertEqual(cm.exception.code, "SRC-UNTERMINATED-BLOCK")

    def test_stray_fence_fatal(self):
        with self.assertRaises(SourceError) as cm:
            self.doc("para\n\n:::\n")
        self.assertEqual(cm.exception.code, "SRC-STRAY-FENCE")

    def test_table_block(self):
        doc = self.doc(":::table\ncaption: C.\n\n| A | B |\n| --- | --- |\n"
                       "| 1 | 2 |\n:::\n")
        blk = doc.children[0]
        self.assertEqual(blk.fields["caption"], "C.")
        self.assertEqual(len(blk.table.rows), 1)

    def test_markdown_structure(self):
        doc = self.doc("Para one.\n\n## Head\n\n- a\n- b\n  - b1\n\n"
                       "1. one\n\n| x |\n| --- |\n| y |\n\n[^n]: Note text.\n")
        kinds = [type(n) for n in doc.children]
        self.assertIn(Heading, kinds)
        self.assertIn(ListNode, kinds)
        self.assertIn(MarkdownTable, kinds)
        self.assertIn("n", doc.footnotes)
        ul = next(n for n in doc.children
                  if isinstance(n, ListNode) and not n.ordered)
        self.assertEqual(len(ul.items), 2)
        self.assertIsInstance(ul.items[1].children[1], ListNode)

    def test_raw_body_keeps_fences_out(self):
        doc = self.doc(":::xml\n<sidebar id=\"x\"><para>hi</para></sidebar>\n:::\n")
        self.assertIn("<sidebar", doc.children[0].raw_body)

    def test_no_frontmatter_fatal(self):
        with self.assertRaises(SourceError) as cm:
            parse_text("no frontmatter here", "A.md")
        self.assertEqual(cm.exception.code, "SRC-NO-FRONTMATTER")


if __name__ == "__main__":
    unittest.main()
