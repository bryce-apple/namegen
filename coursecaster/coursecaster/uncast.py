"""Corpus uncaster: course XML → (plan, sources) for the round-trip test
(brief §9).

For each corpus book this derives an equivalent annotated-markdown source
and course plan, casts them, and the test compares the result against the
original tree under corpuscmp's normalization.  The uncaster maps every
construct the source vocabulary can express; anything it cannot express
becomes a ``:::xml`` passthrough block — the brief's own mechanism for
unrecognised markup — so nothing is silently dropped and the passthrough
report shows exactly what rode through verbatim.

The uncaster is a test harness, not a deliverable authoring path: corpus
books predate our source rules (missing alt, unpaired COM videos, authored
xref display tails), so the harness casts without running the source
validator.  The round-trip verifies the CASTER, not corpus compliance.
"""

import json
import re
import xml.etree.ElementTree as ET

from . import constants as C
from .plan import CoursePlan, Container, ManifestEntry

# So passthrough fragments serialize with the book-level prefixes they will
# inherit once cast back into a document.
ET.register_namespace("me", C.NS_ME)
ET.register_namespace("xi", C.NS_XI)


def _local(tag):
    if tag.startswith("{"):
        uri, name = tag[1:].split("}")
        if uri == C.NS_ME:
            return "me:" + name
        if uri == C.NS_XI:
            return "xi:" + name
        return name
    return tag


def _me(name):
    return f"{{{C.NS_ME}}}{name}"


def _txt(s):
    if not s:
        return ""
    collapsed = " ".join(s.split())
    if not collapsed:
        return " " if s else ""
    lead = " " if s[:1].isspace() else ""
    trail = " " if s[-1:].isspace() else ""
    return lead + collapsed + trail


_ESCAPE = set("\\*[]{}|")


def _esc(text):
    return "".join("\\" + ch if ch in _ESCAPE else ch for ch in text)


def _esc_line_start(line):
    if re.match(r"^(#|>|-|\d+\.|\||:::)", line):
        return "\\" + line
    return line


def _raw_xml(el):
    text = ET.tostring(el, encoding="unicode")
    # Drop redeclared namespaces: the fragment inherits the book-level
    # bindings once cast back into the document.
    return re.sub(r'\s+xmlns(:\w+)?="[^"]*"', "", text).strip()


class _Unexpressible(Exception):
    """The construct has no source-vocabulary mapping — caller falls back
    to a ``:::xml`` passthrough."""


class Uncaster:
    def __init__(self, root, slug="CORPUS"):
        self.root = root
        self.slug = slug
        self.addr_map = {}          # corpus id -> generated address
        self.manifest = []
        self.sources = {}           # address -> markdown text
        self._fn = 0                # footnote counter (per file, reset)

    # ------------------------------------------------------------- inline --

    def _inline(self, el, *, top=False):
        """Uncast mixed content of a para/title/cell to markdown text."""
        parts = [_esc(_txt(el.text))]
        for child in el:
            tag = _local(child.tag)
            if tag == "emphasis":
                role = child.get("role")
                if role not in (None, "bold"):
                    raise _Unexpressible(f"emphasis role={role}")
                if len(child):        # nested markup inside emphasis
                    raise _Unexpressible("nested markup inside emphasis")
                inner = _esc(" ".join((child.text or "").split()))
                if not inner:
                    raise _Unexpressible("empty emphasis")
                parts.append(f"**{inner}**" if role == "bold" else f"*{inner}*")
            elif tag == "ulink":
                label = self._inline(child)
                href = child.get("href", "")
                if ")" in href or " " in href or not href.strip() or not label:
                    raise _Unexpressible("irregular link")
                parts.append(f"[{label}]({href})")
            elif tag == "glossentry":
                gt = child.find("glossterm")
                if gt is None or len(gt) or len(child) != 1 \
                        or (child.text or "").strip():
                    raise _Unexpressible("irregular glossentry")
                phrase = " ".join((gt.text or "").split())
                definition = " ".join((gt.tail or "").split())
                parts.append(f"{{{{term:{_esc(phrase)}|{_esc(definition)}}}}}")
            elif tag == "xref":
                target = child.get("linkend", "")
                parts.append(
                    f"{{{{xref:{self.addr_map.get(target, target)}}}}}")
            elif tag == "footnote":
                self._fn += 1
                label = f"f{self._fn}"
                self._footnotes.append((label, self._inline(child)))
                parts.append(f"[^{label}]")
            else:
                raise _Unexpressible(f"inline <{tag}>")
            parts.append(_esc(_txt(child.tail)))
        return "".join(parts).strip()

    # -------------------------------------------------------------- blocks --

    def _para_md(self, el):
        if el.get("class") or any(_local(c.tag) in ("sub", "br") for c in el):
            raise _Unexpressible("styled para / sub / br")
        return _esc_line_start(self._inline(el, top=True))

    def _list_md(self, el, indent=0):
        ordered = _local(el.tag) == "orderedlist"
        lines = []
        for item in el:
            if _local(item.tag) != "listitem":
                raise _Unexpressible(f"<{_local(item.tag)}> in list")
            paras = [c for c in item if _local(c.tag) == "para"]
            sublists = [c for c in item
                        if _local(c.tag) in ("itemizedlist", "orderedlist")]
            if len(paras) != 1 or len(paras) + len(sublists) != len(item):
                raise _Unexpressible("irregular listitem")
            marker = "1." if ordered else "-"
            lines.append("  " * indent + f"{marker} {self._inline(paras[0])}")
            for sub in sublists:
                lines.extend(self._list_md(sub, indent + 1))
        return lines

    def _figure_block(self, el, address=None):
        tag = _local(el.tag)
        mos = [c for c in el if _local(c.tag) == "mediaobject"]
        if len(mos) != 1:
            raise _Unexpressible("figure without single mediaobject")
        ios = [c for c in mos[0] if _local(c.tag) == "imageobject"]
        if len(ios) != 1 or len(list(mos[0])) != 1:
            raise _Unexpressible("non-image mediaobject")
        data = ios[0].find("imagedata")
        if data is None:
            raise _Unexpressible("imageobject without imagedata")
        attrs = []
        fields = []
        if tag == "informalfigure":
            attrs.append("formal=false")
            if el.find("title") is not None:
                raise _Unexpressible("informalfigure with title")
        else:
            title = el.find("title")
            if title is None:
                raise _Unexpressible("formal figure without title")
            if any(_local(c.tag) != "para" for c in title):
                raise _Unexpressible("irregular figure title")
            credit_paras = list(title)
            if len(credit_paras) > 1:
                raise _Unexpressible("multiple credit paras")
            title_text = _esc(_txt(title.text)).strip()
            if not title_text:
                raise _Unexpressible("empty figure title")
            fields.append(f"title: {title_text}")
            if credit_paras:
                if _txt(credit_paras[0].tail).strip():
                    raise _Unexpressible("text after credit para")
                fields.append(f"credit: {self._inline(credit_paras[0])}")
        if address:
            attrs.append(f"address={address}")
        if el.get("width"):
            attrs.append(f"displaywidth={el.get('width')}")
        if el.get("floatstyle"):
            attrs.append(f"floatstyle={el.get('floatstyle')}")
        src = data.get("fileref", "")
        if '"' in src:
            raise _Unexpressible("quote in fileref")
        attrs.append(f'src="{src}"')
        if data.get("width"):
            attrs.append(f"width={data.get('width')}")
        if data.get("depth"):
            attrs.append(f"depth={data.get('depth')}")
        fields.append(f"alt: {data.get('alt', '')}")
        head = ":::figure" + ("" if not attrs else " " + " ".join(attrs))
        return [head] + fields + [":::"]

    def _video_block(self, el, material):
        mos = list(el)
        vo = mos[0].find("videoobject") if mos else None
        data = vo.find("videodata") if vo is not None else None
        if data is None:
            raise _Unexpressible("video without videodata")
        attrs = [f'asset={data.get("fileref")}',
                 f'guid={material.get("guid")}']
        if data.get("width"):
            attrs.append(f"width={data.get('width')}")
        if data.get(_me("duration")):
            attrs.append(f"duration={data.get(_me('duration'))}")
        name = data.get(_me("name"))
        if name:
            attrs.append(f'name="{name}"')
        return [":::video " + " ".join(attrs), ":::"]

    def _table_block(self, el, address=None):
        caption = None
        header = None
        rows = []
        for child in el:
            tag = _local(child.tag)
            if tag == "caption":
                if len(child):
                    raise _Unexpressible("caption with child elements")
                caption = self._inline(child)
            elif tag == "thead":
                header = [self._cell(c) for c in child]
            elif tag == "tbody":
                for tr in child:
                    rows.append([self._cell(c) for c in tr])
            else:
                raise _Unexpressible(f"<{tag}> in table")
        lines = [":::table" + (f" address={address}" if address else "")]
        if caption:
            lines.append(f"caption: {caption}")
        lines.append("")
        if header:
            lines.append("| " + " | ".join(header) + " |")
            lines.append("|" + "|".join(" --- " for _ in header) + "|")
        for row in rows:
            lines.append("| " + " | ".join(row) + " |")
        lines.append(":::")
        return lines

    def _cell(self, el):
        if _local(el.tag) not in ("th", "td"):
            raise _Unexpressible(f"<{_local(el.tag)}> as cell")
        return self._inline(el)

    def _admonition_block(self, el):
        title = el.find("title")
        if title is None or len(title):
            raise _Unexpressible("admonition without plain title")
        text = " ".join((title.text or "").split())
        if '"' in text:
            raise _Unexpressible("quote in admonition title")
        lines = [f':::{_local(el.tag)} title="{text}"']
        for child in el:
            tag = _local(child.tag)
            if tag == "title":
                continue
            lines.append("")
            lines.extend(self._node_md(child, allow_inner_figure=True))
        lines.append(":::")
        return lines

    def _objective_block(self, el):
        lines = [":::objective zone=theirs"]
        for child in el:
            tag = _local(child.tag)
            if tag == "title":
                continue
            lines.append("")
            if tag in ("orderedlist", "itemizedlist"):
                lines.extend(self._list_md(child))
            elif tag == "para":
                lines.append(self._para_md(child))
            else:
                raise _Unexpressible(f"<{tag}> in objectives sidebar")
        lines.append(":::")
        return lines

    # --------------------------------------------------------- dispatcher --

    def _node_md(self, el, allow_inner_figure=False):
        tag = _local(el.tag)
        try:
            if tag == "para":
                return [self._para_md(el)]
            if tag in ("itemizedlist", "orderedlist"):
                return self._list_md(el)
            if tag == "blockquote":
                children = list(el)
                if children and all(_local(c.tag) == "para" for c in children) \
                        and not _txt(el.text).strip():
                    out = []
                    for i, p in enumerate(children):
                        if i:
                            out.append(">")
                        out.append("> " + self._inline(p))
                    return out
                raise _Unexpressible("bare-content blockquote")
            if tag == "figure" or (tag == "informalfigure"
                                   and el.find("mediaobject/videoobject")
                                   is None):
                return self._figure_block(el, self.addr_map.get(el.get("id")))
            if tag == "table":
                return self._table_block(el, self.addr_map.get(el.get("id")))
            if tag == "informaltable":
                bodies = [c for c in el if _local(c.tag) == "tbody"]
                if len(bodies) != 1 or len(list(el)) != 1:
                    raise _Unexpressible("irregular informaltable")
                rows = [[self._cell(c) for c in tr] for tr in bodies[0]]
                if not rows or any(_local(c.tag) == "th"
                                   for tr in bodies[0] for c in tr):
                    raise _Unexpressible("informaltable with th")
                # No separator line: the parser reads header-less rows as
                # body-only, which casts back to tbody-only (§5.7).
                return ["| " + " | ".join(r) + " |" for r in rows]
            if tag in ("note", "important", "warning", "caution"):
                return self._admonition_block(el)
            if tag == "sidebar" and el.get("class") == C.OBJECTIVE_SIDEBAR_CLASS:
                return self._objective_block(el)
            if tag == "me:activity":
                return [f":::activity guid={el.get('guid')}", ":::"]
            raise _Unexpressible(f"<{tag}>")
        except _Unexpressible:
            return [":::xml", _raw_xml(el), ":::"]

    # ---------------------------------------------------------- structure --

    def _pre_map_ids(self):
        """First pass: assign addresses to xref-able elements so inline
        uncasting can rewrite linkends."""
        # Only xref-targeted figures/tables need addresses (and, for
        # figures, manifest entries) — everything else keeps hash ids.
        self._targeted = {el.get("linkend") for el in self.root.iter()
                          if _local(el.tag) == "xref"}
        unit_i = 0
        for unit in self._chapters(self.root):
            unit_i += 1
            u_addr = f"{self.slug}-U{unit_i:02d}"
            self.addr_map[unit.get("id", "")] = u_addr
            lesson_i = 0
            self._map_sections(unit, u_addr)
            for lesson in self._chapters(unit):
                lesson_i += 1
                l_addr = f"{u_addr}-L{lesson_i:02d}"
                self.addr_map[lesson.get("id", "")] = l_addr
                self._map_sections(lesson, l_addr)

    def _map_sections(self, chapter, parent_addr):
        sec_i = 0
        for sec in chapter:
            if _local(sec.tag) != "section":
                continue
            sec_i += 1
            s_addr = f"{parent_addr}-S{sec_i:02d}"
            if sec.get("id"):
                self.addr_map[sec.get("id")] = s_addr
            f_i = t_i = 0
            for el in sec.iter():
                tag = _local(el.tag)
                if tag == "figure" and el.get("id") in self._targeted:
                    f_i += 1
                    addr = f"{s_addr}-F{f_i}"
                    self.addr_map[el.get("id")] = addr
                    self.manifest.append(ManifestEntry(
                        address=addr, kind="figure", status="resolved",
                        owner="partner"))
                elif tag == "table" and el.get("id") in self._targeted:
                    t_i += 1
                    self.addr_map[el.get("id")] = f"{s_addr}-T{t_i}"

    @staticmethod
    def _chapters(el):
        return [c for c in el if _local(c.tag) == "chapter"]

    @staticmethod
    def _is_terminal_activity(sec):
        children = list(sec)
        return (len(children) == 2
                and _local(children[0].tag) == "title"
                and _local(children[1].tag) == "me:activity")

    def _section_file(self, sec, address):
        self._fn = 0
        self._footnotes = []
        title_el = sec.find("title")
        title = " ".join((title_el.text or "").split()) if title_el is not None \
            else ""
        lines = ["---", f"address: {address}", f"title: {json.dumps(title)}",
                 "---", ""]
        body = self._section_body(sec, depth=0)
        lines.extend(body)
        if self._footnotes:
            lines.append("")
            for label, text in self._footnotes:
                lines.append(f"[^{label}]: {text}")
        self.sources[address] = "\n".join(lines) + "\n"

    def _section_body(self, sec, depth):
        lines = []
        children = list(sec)
        i = 0
        while i < len(children):
            el = children[i]
            tag = _local(el.tag)
            if tag == "title":
                i += 1
                continue
            if tag == "section":
                heading_el = el.find("title")
                try:
                    heading = self._inline(heading_el) \
                        if heading_el is not None else ""
                except _Unexpressible:
                    heading = " ".join(
                        "".join(heading_el.itertext()).split())
                lines.append("")
                lines.append("#" * (depth + 2) + " " + heading)
                lines.extend(self._section_body(el, depth + 1))
                i += 1
                continue
            if tag == "informalfigure" \
                    and el.find("mediaobject/videoobject") is not None:
                nxt = children[i + 1] if i + 1 < len(children) else None
                if nxt is not None and _local(nxt.tag) == "me:material":
                    try:
                        block = self._video_block(el, nxt)
                    except _Unexpressible:
                        block = [":::xml", _raw_xml(el), _raw_xml(nxt), ":::"]
                    lines.append("")
                    lines.extend(block)
                    i += 2
                    continue
                # COM videos predate the pairing rule — passthrough keeps
                # them verbatim and visible in the report.
                lines.append("")
                lines.extend([":::xml", _raw_xml(el), ":::"])
                i += 1
                continue
            lines.append("")
            lines.extend(self._node_md(el))
            i += 1
        return lines

    def _container(self, chapter, address, kind):
        title_el = chapter.find("title")
        cont = Container(
            address=address,
            title=" ".join((title_el.text or "").split())
            if title_el is not None else "",
            kind=kind,
        )
        for opt in chapter:
            if _local(opt.tag) == "me:option" \
                    and opt.get("key") == C.ACCESS_OPTION_KEY:
                cont.access = opt.get("value")
        children = [c for c in chapter
                    if _local(c.tag) in ("section", "chapter")]
        # terminal activity section → manifest *-QZ entry
        terminal = None
        if children and _local(children[-1].tag) == "section" \
                and self._is_terminal_activity(children[-1]):
            terminal = children.pop()
        # Ordered walk.  Sections must precede nested chapters — the corpus
        # shape our container model casts; anything else fails the harness
        # loudly.  An orphan figure authored as a direct chapter child
        # (2016 ch.2) joins the section preceding it in document order —
        # mirrored by corpuscmp rule 7.
        seen_chapter = False
        sec_i = 0
        lesson_i = 0
        last_s_addr = None
        for el in chapter:
            tag = _local(el.tag)
            if el is terminal or tag in ("title", "me:option"):
                continue
            if tag == "chapter":
                seen_chapter = True
                lesson_i += 1
                if kind == "lesson":
                    raise ValueError("chapter nested three deep")
                cont.lessons.append(
                    self._container(el, f"{address}-L{lesson_i:02d}", "lesson"))
            elif tag == "section":
                if seen_chapter:
                    raise ValueError(
                        f"section after nested chapters in {address}")
                sec_i += 1
                last_s_addr = f"{address}-S{sec_i:02d}"
                cont.subsections.append(last_s_addr)
                self._section_file(el, last_s_addr)
            elif tag in ("figure", "informalfigure") and last_s_addr:
                self._fn = 0
                self._footnotes = []
                extra = self._node_md(el)
                self.sources[last_s_addr] += "\n" + "\n".join(extra) + "\n"
            else:
                raise ValueError(f"<{tag}> as direct chapter child in "
                                 f"{address}")
        if terminal is not None:
            act = terminal.find(_me("activity"))
            title_el = terminal.find("title")
            self.manifest.append(ManifestEntry(
                address=address + C.TERMINAL_ACTIVITY_SUFFIX,
                kind="activity", status="resolved", owner="platform",
                title=" ".join((title_el.text or "").split())
                if title_el is not None else None,
                guid=act.get("guid")))
        return cont

    # -------------------------------------------------------------- entry --

    def run(self):
        if _local(self.root.tag) != "book":
            raise ValueError(f"not a book: <{_local(self.root.tag)}>")
        self._pre_map_ids()
        author = None
        labeldefault = None
        for opt in self.root:
            if _local(opt.tag) == "me:option":
                if opt.get("key") == "author" and opt.get("value") and not author:
                    author = opt.get("value")
                elif opt.get("key") == "labeldefault:chapter":
                    labeldefault = opt.get("value")
        title_el = self.root.find("title")
        units = []
        unit_i = 0
        for chapter in self._chapters(self.root):
            unit_i += 1
            units.append(self._container(chapter, f"{self.slug}-U{unit_i:02d}",
                                         "unit"))
        plan = CoursePlan(
            slug=self.slug,
            title=" ".join((title_el.text or "").split())
            if title_el is not None else "",
            subtitle=None,
            author=author,
            labeldefault_chapter=labeldefault,
            bookinfo={},
            units=units,
            manifest=self.manifest,
            enforce_intro_terminal=False,   # corpus predates the §7 rule
        )
        return plan, self.sources


def uncast_book(xml_path, slug="CORPUS"):
    root = ET.parse(xml_path).getroot()
    return Uncaster(root, slug).run()
