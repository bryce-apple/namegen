"""Output validator (brief §7).  Runs on built XML.

Namespace handling resolves by URI, never prefix — the patch document binds
the Textbook URI to ``be:`` rather than ``me:`` (§7, corpus-confirmed).
"""

import re
import xml.etree.ElementTree as ET
from collections import Counter

from . import constants as C
from .errors import ErrorCollector, OutputError
from .srcmodel import (
    Block, BlockQuote, Heading, ListNode, MarkdownTable, Para, TermDef,
)
from .vocabulary import NEVER_EMIT_ELEMENTS, VOCABULARY

_KNOWN_URIS = {C.NS_ME, C.NS_XI}


def _split_tag(tag):
    if tag.startswith("{"):
        uri, local = tag[1:].split("}")
        return uri, local
    return None, tag


class OutputValidator:
    def __init__(self, xml_text, plan=None, sources=None, cast_report=None):
        self.xml_text = xml_text
        self.plan = plan
        self.sources = sources
        self.cast_report = cast_report or {}
        self.errors = ErrorCollector()
        self.report = {"passthrough": self.cast_report.get("passthrough", []),
                       "incomplete": False}

    def err(self, code, message, **kw):
        self.errors.error(OutputError, code, message, **kw)

    # ------------------------------------------------------- basic checks --

    def _parse(self):
        try:
            return ET.fromstring(self.xml_text)
        except ET.ParseError as e:
            self.err("OUT-MALFORMED", f"output is not well-formed XML: {e}")
            return None

    def _check_namespaces(self, root):
        if C.NS_ME not in self.xml_text:
            self.err("OUT-NAMESPACE",
                     f"Textbook namespace {C.NS_ME} is not declared")
        for el in root.iter():
            uri, local = _split_tag(el.tag)
            if uri is not None and uri not in _KNOWN_URIS:
                self.err("OUT-NAMESPACE",
                         f"element {local} in unexpected namespace {uri}")

    def _check_vocabulary(self, root):
        unknown = Counter()
        for el in root.iter():
            _, local = _split_tag(el.tag)
            if local not in VOCABULARY:
                unknown[local] += 1
        for name, n in sorted(unknown.items()):
            # Two corpus courses ship defects a schema would have caught —
            # a live misspelled <emphais> among them.  Report everything.
            self.err("OUT-VOCABULARY",
                     f"element <{name}> (×{n}) is outside the observed "
                     "vocabulary")

    def _check_never_emit(self, root):
        for el in root.iter():
            _, local = _split_tag(el.tag)
            if local in NEVER_EMIT_ELEMENTS:
                self.err("OUT-NEVER-EMIT",
                         f"<{local}> is platform-generated and must never "
                         "be emitted (§5.11)")
            for attr in el.attrib:
                a_uri, a_local = _split_tag(attr)
                if a_uri == C.NS_ME and a_local == "paracount":
                    self.err("OUT-NEVER-EMIT",
                             "me:paracount is platform-generated and must "
                             "never be emitted (§5.11)")
            if "label" in el.attrib:
                # The one exception: label="" on introduction sections.
                if not (local == "section"
                        and el.get("label") == C.INTRO_LABEL_VALUE):
                    self.err(
                        "OUT-NEVER-EMIT",
                        f"<{local} label=\"{el.get('label')}\"> — labels "
                        "derive from position at render (§5.2)")

    def _check_ids_unique(self, root):
        seen = Counter(el.get("id") for el in root.iter() if el.get("id"))
        for i, n in sorted(seen.items()):
            if n > 1:
                self.err("OUT-DUP-ID", f"id '{i}' appears {n} times")

    def _check_xrefs(self, root):
        ids = {el.get("id") for el in root.iter() if el.get("id")}
        for el in root.iter():
            _, local = _split_tag(el.tag)
            if local == "xref":
                target = el.get("linkend")
                if target not in ids:
                    # The corpus ships a live dangling 'chatper01'.
                    self.err("OUT-XREF-DANGLING",
                             f"xref linkend='{target}' matches no id")

    # ------------------------------------------------------------- tokens --

    def _check_tokens(self, root):
        found = []       # (address, element local name)
        for el in root.iter():
            _, local = _split_tag(el.tag)
            for value in el.attrib.values():
                addr = C.parse_pending_token(value)
                if addr is not None:
                    found.append((addr, local))
            if el.text and C.PENDING_TOKEN_PREFIX in (el.text or ""):
                self.err("OUT-TOKEN-PLACEMENT",
                         f"PENDING token in text content of <{local}>")
        if self.plan is None:
            if found:
                self.err("OUT-TOKEN-UNKNOWN",
                         f"{len(found)} PENDING token(s) but no plan to "
                         "reconcile against")
            return
        manifest = self.plan.manifest_by_address
        # Expected token multiplicity per specified entry: a video is one
        # component emitting two siblings — videodata fileref and the
        # paired me:material guid (§5.5, §5.6).
        expected = {m.address: (2 if m.kind == "video" else 1)
                    for m in self.plan.manifest if m.status == "specified"}
        counts = Counter(addr for addr, _ in found)
        for addr, n in sorted(counts.items()):
            entry = manifest.get(addr)
            if entry is None:
                self.err("OUT-TOKEN-UNKNOWN",
                         f"token PENDING:{addr} resolves to no manifest entry")
            elif entry.status != "specified":
                self.err("OUT-TOKEN-STATUS",
                         f"token PENDING:{addr} but manifest status is "
                         f"{entry.status}")
        # Both directions (§7): every specified entry must be represented.
        for addr, want in sorted(expected.items()):
            have = counts.get(addr, 0)
            if have != want:
                self.err("OUT-TOKEN-COUNT",
                         f"manifest {addr} is specified and should emit "
                         f"{want} token(s); output has {have}")

    def _check_pending_cast(self, root):
        n = 0
        for el in root.iter():
            values = list(el.attrib.values()) + [el.text or ""]
            if any(C.PENDING_CAST_MARKER in v for v in values):
                n += 1
        if n:
            self.report["incomplete"] = True
            self.err("OUT-PENDING-CAST",
                     f"{n} PENDING-CAST marker(s) — a construct has no cast "
                     "rule yet; build is incomplete (§5.10)")

    # ---------------------------------------------------------- structure --

    def _container_children(self, chapter_el):
        secs, chs = [], []
        for child in chapter_el:
            _, local = _split_tag(child.tag)
            if local == "section":
                secs.append(child)
            elif local == "chapter":
                chs.append(child)
        return secs, chs

    def _check_container(self, el, container):
        if el.get("id") != container.address:
            self.err("OUT-STRUCTURE",
                     f"chapter id {el.get('id')} != planned address "
                     f"{container.address}")
            return
        secs, chs = self._container_children(el)
        qz = container.address + C.TERMINAL_ACTIVITY_SUFFIX
        entry = self.plan.manifest_by_address.get(qz)
        expect_qz = bool(entry and entry.status in ("resolved", "specified"))
        got = [s.get("id") for s in secs]
        want = list(container.subsections) + ([qz] if expect_qz else [])
        if got != want:
            self.err("OUT-STRUCTURE",
                     f"{container.address}: section sequence {got} != "
                     f"planned {want}")
        if [c.get("id") for c in chs] != [l.address for l in container.lessons]:
            self.err("OUT-STRUCTURE",
                     f"{container.address}: lesson sequence differs from plan")
        if self.plan.enforce_intro_terminal:
            # Every container opens with an introduction section and closes
            # with a terminal activity section (§7).
            if not (got and got[0].endswith(C.INTRO_ADDRESS_SUFFIX)
                    and secs[0].get("label") == C.INTRO_LABEL_VALUE):
                self.err("OUT-STRUCTURE",
                         f"{container.address} does not open with an "
                         "introduction section (label=\"\", *-S0)")
            last_children = [c for c in el]
            if last_children:
                _, last_local = _split_tag(last_children[-1].tag)
                last_id = last_children[-1].get("id")
                if not (last_local == "section" and last_id == qz):
                    self.err("OUT-STRUCTURE",
                             f"{container.address} does not close with its "
                             f"terminal activity section {qz}")
        for lesson_el, lesson in zip(chs, container.lessons):
            self._check_container(lesson_el, lesson)

    def _check_structure(self, root):
        _, root_local = _split_tag(root.tag)
        if root_local != "book":
            self.err("OUT-STRUCTURE", f"root element is <{root_local}>, not "
                     "<book>")
            return
        tops = [c for c in root if _split_tag(c.tag)[1] == "chapter"]
        if [c.get("id") for c in tops] != [u.address for u in self.plan.units]:
            self.err("OUT-STRUCTURE", "top-level chapter sequence differs "
                     "from planned units")
            return
        for el, unit in zip(tops, self.plan.units):
            self._check_container(el, unit)

    # ---------------------------------------------------------- round-trip --

    def _expected_counts(self):
        """Recompute, from the source AST and plan, what the output must
        contain.  A discrepancy is a caster defect, not a source defect."""
        exp = Counter()

        def walk(nodes, addr):
            for node in nodes:
                if isinstance(node, Heading):
                    exp["sections"] += 1
                elif isinstance(node, MarkdownTable):
                    exp["tables"] += 1
                elif isinstance(node, Block):
                    status = node.attrs.get("status", "resolved")
                    emits = status in ("resolved", "specified")
                    if node.type == "summary":
                        exp["sections"] += 1
                        walk(node.body, addr)
                    elif node.type == "figure":
                        exp["figures"] += 1 if emits else 0
                    elif node.type == "video":
                        if emits:
                            exp["figures"] += 1
                            exp["references"] += 1
                    elif node.type == "activity":
                        exp["references"] += 1 if emits else 0
                    elif node.type == "table":
                        exp["tables"] += 1
                    else:
                        walk(node.body, addr)
                elif isinstance(node, Para):
                    exp["glossentries"] += sum(
                        isinstance(i, TermDef) for i in node.inlines)
                elif isinstance(node, (ListNode,)):
                    for item in node.items:
                        walk(item.children, addr)
                elif isinstance(node, BlockQuote):
                    walk(node.children, addr)

        for addr in self.plan.subsection_addresses():
            doc = self.sources.get(addr)
            if doc is None:
                continue
            exp["sections"] += 1
            walk(doc.children, addr)
        for m in self.plan.manifest:
            if m.address.endswith(C.TERMINAL_ACTIVITY_SUFFIX) \
                    and m.kind == "activity" \
                    and m.status in ("resolved", "specified"):
                exp["sections"] += 1
                exp["references"] += 1
        return exp

    def _actual_counts(self, root):
        act = Counter()
        for el in root.iter():
            uri, local = _split_tag(el.tag)
            if local == "section":
                act["sections"] += 1
            elif local == "glossentry":
                act["glossentries"] += 1
            elif local in ("table", "informaltable"):
                act["tables"] += 1
            elif local in ("figure",):
                act["figures"] += 1
            elif local == "informalfigure":
                act["figures"] += 1
            elif uri == C.NS_ME and local in ("activity", "material"):
                act["references"] += 1
        return act

    def _check_roundtrip(self, root):
        expected = self._expected_counts()
        actual = self._actual_counts(root)
        for key in sorted(set(expected) | set(actual)):
            if expected.get(key, 0) != actual.get(key, 0):
                self.err("OUT-ROUNDTRIP",
                         f"{key}: source implies {expected.get(key, 0)}, "
                         f"output has {actual.get(key, 0)} — caster defect")

    # -------------------------------------------------------------- entry --

    def run(self):
        root = self._parse()
        if root is None:
            return self.errors, self.report
        self._check_namespaces(root)
        self._check_vocabulary(root)
        self._check_never_emit(root)
        self._check_ids_unique(root)
        self._check_xrefs(root)
        self._check_tokens(root)
        self._check_pending_cast(root)
        if self.plan is not None:
            self._check_structure(root)
            if self.sources is not None:
                self._check_roundtrip(root)
        return self.errors, self.report


def validate_output(xml_text, plan=None, sources=None, cast_report=None):
    return OutputValidator(xml_text, plan, sources, cast_report).run()
