"""Source validator (brief §6).  Runs before the caster; every failure is
fatal.  All findings are collected so one run reports everything, then the
build fails.
"""

import re

from . import constants as C
from .blocks import (BLOCK_SPECS, BODY_NONE, BODY_TABLE, NOTE_FAMILY,
                     REFERENCE_BLOCKS)
from .errors import ErrorCollector, SourceError
from .srcmodel import (
    Block, BlockQuote, Bold, FootnoteRef, Heading, Italic, Link, ListNode,
    MarkdownTable, Para, TermDef, Text, Xref,
)

# An authored number, label, or cross-reference literal (§6).  The corpus
# shows why: 'Figrue 9.2', a table labelled 'Figure 3.1', a dangling
# 'chatper01'.  Numbering derives from position at render; prose must not
# hard-code it.
_AUTHORED_NUMBER_RE = re.compile(
    r"\b(Figure|Table|Chapter|Section|Unit|Lesson|Topic|Week|Exhibit)\s+\d",
    re.IGNORECASE)

_FRONTMATTER_REQUIRED = ("address", "title")
_FRONTMATTER_KEYS = {"address", "title", "serves", "obligation", "instances",
                     "terms_first_use"}
_LIST_KEYS = ("serves", "instances", "terms_first_use")


def _iter_blocks(nodes):
    for node in nodes:
        if isinstance(node, Block):
            yield node
            yield from _iter_blocks(node.body)
        elif isinstance(node, (BlockQuote,)):
            yield from _iter_blocks(node.children)


def _iter_inlines(nodes):
    for node in nodes:
        if isinstance(node, Para):
            yield from _flat_inlines(node.inlines)
        elif isinstance(node, Heading):
            yield from _flat_inlines(node.inlines)
        elif isinstance(node, ListNode):
            for item in node.items:
                yield from _iter_inlines(item.children)
        elif isinstance(node, BlockQuote):
            yield from _iter_inlines(node.children)
        elif isinstance(node, MarkdownTable):
            for row in ([node.header] if node.header else []) + node.rows:
                for cell in row:
                    yield from _flat_inlines(cell)
        elif isinstance(node, Block):
            yield from _iter_inlines(node.body)


def _flat_inlines(inlines):
    for node in inlines:
        yield node
        if isinstance(node, (Bold, Italic, Link)):
            yield from _flat_inlines(node.children)


class SourceValidator:
    def __init__(self, plan, sources, term_register):
        self.plan = plan
        self.sources = sources
        self.register = term_register
        self.errors = ErrorCollector()
        self.manifest = plan.manifest_by_address

    def err(self, code, message, **kw):
        self.errors.error(SourceError, code, message, **kw)

    # ------------------------------------------------------------ file set --

    def _check_file_set(self):
        planned = set(self.plan.subsection_addresses())
        have = set(self.sources)
        for addr in sorted(planned - have):
            self.err("SRC-MISSING-FILE",
                     f"plan subsection {addr} has no source file", address=addr)
        for addr in sorted(have - planned):
            self.err("SRC-ORPHAN-FILE",
                     f"source file {addr}.md is not in the course plan",
                     address=addr)

    # --------------------------------------------------------- frontmatter --

    def _check_frontmatter(self, addr, doc):
        fm = doc.frontmatter
        for key in _FRONTMATTER_REQUIRED:
            if not fm.get(key):
                self.err("SRC-MISSING-FRONTMATTER",
                         f"frontmatter lacks '{key}'", path=doc.path)
        unknown = set(fm) - _FRONTMATTER_KEYS
        if unknown:
            self.err("SRC-UNKNOWN-FRONTMATTER",
                     f"unknown frontmatter key(s): {', '.join(sorted(unknown))}",
                     path=doc.path)
        for key in _LIST_KEYS:
            if key in fm and not isinstance(fm[key], list):
                self.err("SRC-BAD-FRONTMATTER",
                         f"frontmatter '{key}' must be a list", path=doc.path)
        if fm.get("address") and fm["address"] != addr:
            self.err("SRC-ADDRESS-MISMATCH",
                     f"frontmatter address {fm['address']} does not match "
                     f"filename address {addr}", path=doc.path)

    # -------------------------------------------------------------- blocks --

    def _check_block(self, addr, doc, block, inside=None):
        spec = BLOCK_SPECS.get(block.type)
        if spec is None:
            self.err("SRC-UNKNOWN-BLOCK", f"unknown block type :::{block.type}",
                     path=doc.path, line=block.line)
            return
        if inside is not None and block.type != "figure":
            self.err("SRC-BAD-INNER",
                     f":::{block.type} cannot nest inside :::{inside} "
                     "(only :::figure may)", path=doc.path, line=block.line)
        for attr in sorted(set(block.attrs) - spec["attrs"]):
            self.err("SRC-UNKNOWN-ATTR",
                     f":::{block.type} has unknown attribute '{attr}'",
                     path=doc.path, line=block.line)
        for attr in sorted(spec["required_attrs"] - set(block.attrs)):
            self.err("SRC-MISSING-ATTR",
                     f":::{block.type} requires attribute '{attr}'",
                     path=doc.path, line=block.line)
        for fieldname in sorted(set(block.fields) - spec["fields"]):
            self.err("SRC-UNKNOWN-FIELD",
                     f":::{block.type} has unknown field '{fieldname}'",
                     path=doc.path, line=block.line)
        if spec["body"] in (BODY_NONE, BODY_TABLE) and block.raw_body:
            # Catches, among others, a misspelled field name silently
            # becoming body text.
            self.err("SRC-UNEXPECTED-BODY",
                     f":::{block.type} has unrecognised body content: "
                     f"{block.raw_body.splitlines()[0]!r}",
                     path=doc.path, line=block.line)

        if block.type == "figure" and "alt" not in block.fields:
            # Stricter than the corpus deliberately (§5.4): 20/36 in
            # Business Ethics shows the platform tolerates missing alt;
            # our pipeline does not.
            self.err("SRC-FIGURE-NO-ALT", ":::figure without alt",
                     path=doc.path, line=block.line)

        status = block.attrs.get("status", "resolved")
        if block.type in REFERENCE_BLOCKS:
            if status not in C.MANIFEST_STATUSES:
                self.err("SRC-BAD-STATUS",
                         f":::{block.type} has unknown status '{status}'",
                         path=doc.path, line=block.line)
            if status == "specified" and block.type in ("figure", "video") \
                    and "brief" not in block.fields:
                self.err("SRC-SPECIFIED-NO-BRIEF",
                         f":::{block.type} status=specified without brief",
                         path=doc.path, line=block.line)
            ref_addr = block.attrs.get("address")
            if status != "resolved" and not ref_addr:
                self.err("SRC-REF-NO-ADDRESS",
                         f":::{block.type} status={status} needs address= "
                         "to bind its manifest entry",
                         path=doc.path, line=block.line)
            if ref_addr:
                entry = self.manifest.get(ref_addr)
                if entry is None:
                    self.err("SRC-REF-UNKNOWN-ADDRESS",
                             f"address {ref_addr} is not in the manifest",
                             path=doc.path, line=block.line)
                else:
                    want_kind = block.type
                    if entry.kind != want_kind:
                        self.err("SRC-REF-KIND-MISMATCH",
                                 f"{ref_addr} is kind={entry.kind} in the "
                                 f"manifest but referenced by :::{block.type}",
                                 path=doc.path, line=block.line)
                    if entry.status != status:
                        self.err("SRC-REF-STATUS-MISMATCH",
                                 f"{ref_addr}: block says status={status}, "
                                 f"manifest says {entry.status}",
                                 path=doc.path, line=block.line)

        # GUID suffix inconsistent with its element type (§6).
        guid = block.attrs.get("guid")
        if guid and C.parse_pending_token(guid) is None:
            want = None
            if block.type == "activity":
                want = C.GUID_SUFFIXES["activity"]
            elif block.type == "video":
                want = C.GUID_SUFFIXES["material"]   # the paired me:material
            if want and not guid.endswith(want):
                self.err("SRC-GUID-SUFFIX",
                         f"guid {guid} does not end in '{want}' "
                         f"({block.type})", path=doc.path, line=block.line)

        if block.type == "flipcard":
            anchor = block.attrs.get("anchor")
            if anchor is not None:
                headings = [n.text for n in doc.children
                            if isinstance(n, Heading)]
                if anchor not in headings:
                    self.err("SRC-FLIPCARD-ANCHOR",
                             f"flipcard anchor '{anchor}' matches no heading "
                             "in the file", path=doc.path, line=block.line)

        for child in block.body:
            if isinstance(child, Block):
                self._check_block(addr, doc, child, inside=block.type)

    # -------------------------------------------------------------- inline --

    def _xref_targets(self):
        # Plan and manifest addresses, plus addresses declared by :::table
        # blocks (tables are xref targets in the corpus but not platform
        # objects, so they live outside the manifest).
        targets = set(self.plan.all_addresses())
        for source in self.sources.values():
            for block in _iter_blocks(source.children):
                if block.type == "table" and block.attrs.get("address"):
                    targets.add(block.attrs["address"])
        return targets

    def _check_inlines(self, addr, doc, term_uses):
        valid_targets = self._xref_targets()
        for node in _iter_inlines(doc.children):
            if isinstance(node, TermDef):
                term_uses.setdefault(node.phrase.casefold(), []).append(
                    (node.phrase, addr, doc.path))
                assigned = self.register.address_of(node.phrase) \
                    if self.register else None
                if self.register and assigned != addr:
                    self.err(
                        "SRC-TERM-WRONG-ADDRESS",
                        f"term '{node.phrase}' is assigned to "
                        f"{assigned or 'no address'} in the register, "
                        f"defined at {addr}", path=doc.path)
            elif isinstance(node, Xref):
                if node.address not in valid_targets:
                    self.err("SRC-XREF-UNKNOWN",
                             f"xref to {node.address}, which is not in the "
                             "course plan", path=doc.path)
            elif isinstance(node, FootnoteRef):
                if node.label not in doc.footnotes:
                    self.err("SRC-UNDEFINED-FOOTNOTE",
                             f"footnote [^{node.label}] has no definition",
                             path=doc.path)
            elif isinstance(node, Text):
                m = _AUTHORED_NUMBER_RE.search(node.value)
                if m:
                    self.err("SRC-AUTHORED-NUMBER",
                             f"authored number/label literal '{m.group(0)}' — "
                             "numbering derives at render; use {{xref:…}}",
                             path=doc.path)

    # ------------------------------------------------------------ document --

    def _check_doc(self, addr, doc, term_uses):
        self._check_frontmatter(addr, doc)
        blocks = list(_iter_blocks(doc.children))
        for block in doc.children:
            if isinstance(block, Block):
                self._check_block(addr, doc, block)
        self._check_inlines(addr, doc, term_uses)

        if not addr.endswith(C.INTRO_ADDRESS_SUFFIX):
            # A subsection without an objective or a summary (§6).
            # Introduction sections (*-S0) are exempt: the corpus intro
            # sections are welcome paragraphs with neither.
            types = {b.type for b in blocks}
            if "objective" not in types:
                self.err("SRC-MISSING-OBJECTIVE",
                         f"subsection {addr} has no :::objective",
                         path=doc.path)
            if "summary" not in types:
                self.err("SRC-MISSING-SUMMARY",
                         f"subsection {addr} has no :::summary", path=doc.path)

        declared = {t.casefold(): t
                    for t in doc.frontmatter.get("terms_first_use") or []}
        used = {n.phrase.casefold(): n.phrase
                for n in _iter_inlines(doc.children) if isinstance(n, TermDef)}
        for key in sorted(set(declared) - set(used)):
            self.err("SRC-TERMS-FIRST-USE",
                     f"frontmatter lists term '{declared[key]}' but the body "
                     "does not define it", path=doc.path)
        for key in sorted(set(used) - set(declared)):
            self.err("SRC-TERMS-FIRST-USE",
                     f"body defines term '{used[key]}' but frontmatter "
                     "terms_first_use does not list it", path=doc.path)

    # ------------------------------------------------------------ manifest --

    def _check_manifest(self):
        for entry in self.plan.manifest:
            if entry.status == "resolved":
                if not entry.guid and entry.kind in ("activity", "material"):
                    self.err("SRC-MANIFEST-NO-GUID",
                             f"manifest {entry.address} is resolved but has "
                             "no guid", address=entry.address)
            if entry.guid and C.parse_pending_token(entry.guid) is None:
                want = C.GUID_SUFFIXES.get(entry.kind)
                if want and not entry.guid.endswith(want):
                    self.err("SRC-GUID-SUFFIX",
                             f"manifest {entry.address} guid {entry.guid} "
                             f"does not end in '{want}' ({entry.kind})",
                             address=entry.address)

    # --------------------------------------------------------------- entry --

    def run(self):
        self._check_file_set()
        self._check_manifest()
        term_uses = {}
        for addr in sorted(self.sources):
            self._check_doc(addr, self.sources[addr], term_uses)
        # Any term defined more than once course-wide is fatal (§6).
        for key, uses in sorted(term_uses.items()):
            if len(uses) > 1:
                places = ", ".join(a for _, a, _ in uses)
                self.err("SRC-TERM-DUP",
                         f"term '{uses[0][0]}' defined at multiple addresses: "
                         f"{places}")
        return self.errors


def validate_sources(plan, sources, term_register=None) -> ErrorCollector:
    return SourceValidator(plan, sources, term_register).run()
