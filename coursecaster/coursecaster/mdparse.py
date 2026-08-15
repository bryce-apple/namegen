"""Annotated-markdown parser (brief §3.1, §4).

Produces the source AST in ``srcmodel``.  The parser is structurally
lenient where the source validator is the mandated authority (unknown block
types parse and are then rejected by validation), and loud where structure
itself is broken (unterminated fence, missing frontmatter): those make the
file unreadable and fail immediately.

Blocks do not nest, except that ``:::note``-family bodies may contain a
``:::figure`` (brief §4.1).  Heading levels ``##``–``####`` map to nested
sections — the corpus nests sections three deep inside a leaf section, one
level deeper than the brief's table (STUDY.md).
"""

import re

import yaml

from .blocks import BLOCK_SPECS, BODY_MARKDOWN, BODY_NONE, BODY_RAW, BODY_TABLE
from .errors import SourceError
from .srcmodel import (
    Block, BlockQuote, Bold, FootnoteDefinition, FootnoteRef, Heading, Italic,
    Link, ListItem, ListNode, MarkdownTable, Para, SourceDoc, TermDef, Text,
    Xref,
)

FENCE_RE = re.compile(r"^:::([a-z]+)\s*(.*)$")
ATTR_RE = re.compile(r'([A-Za-z_]+)=(?:"([^"]*)"|(\S+))')
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")
FOOTDEF_RE = re.compile(r"^\[\^([^\]\s]+)\]:\s*(.*)$")
FIELD_RE = re.compile(r"^([a-z_]+):\s*(.*)$")
XREF_RE = re.compile(r"\{\{xref:([A-Za-z0-9._\-]+)\}\}")
TERM_RE = re.compile(r"\{\{term:([^|{}]+)\|(.+?)\}\}", re.S)
FOOTREF_RE = re.compile(r"\[\^([^\]\s]+)\]")
LINK_RE = re.compile(r"\[((?:[^\]\\]|\\.)*)\]\(([^)\s]+)\)")
TABLE_SEP_RE = re.compile(r"^:?-{3,}:?$")


# ------------------------------------------------------------------ inline --

def parse_inlines(s: str, path=None, line=0):
    out, buf, i, n = [], [], 0, len(s)

    def flush():
        if buf:
            out.append(Text("".join(buf)))
            del buf[:]

    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            buf.append(s[i + 1])
            i += 2
            continue
        if s.startswith("{{", i):
            m = TERM_RE.match(s, i)
            if m:
                flush()
                out.append(TermDef(m.group(1).strip(), m.group(2).strip()))
                i = m.end()
                continue
            m = XREF_RE.match(s, i)
            if m:
                flush()
                out.append(Xref(m.group(1)))
                i = m.end()
                continue
            raise SourceError(
                "SRC-BAD-INLINE",
                f"unrecognised '{{{{…}}}}' construct at {s[i:i+40]!r}",
                path=path, line=line,
            )
        if s.startswith("[^", i):
            m = FOOTREF_RE.match(s, i)
            if m:
                flush()
                out.append(FootnoteRef(m.group(1)))
                i = m.end()
                continue
        if c == "[":
            m = LINK_RE.match(s, i)
            if m:
                flush()
                out.append(Link(parse_inlines(m.group(1), path, line), m.group(2)))
                i = m.end()
                continue
        if s.startswith("**", i):
            j = s.find("**", i + 2)
            if j != -1 and s[i + 2:j].strip():
                flush()
                out.append(Bold(parse_inlines(s[i + 2:j], path, line)))
                i = j + 2
                continue
        if c == "*":
            j = s.find("*", i + 1)
            if j != -1 and s[i + 1:j].strip() and "\n" not in s[i + 1:j]:
                flush()
                out.append(Italic(parse_inlines(s[i + 1:j], path, line)))
                i = j + 1
                continue
        buf.append(c)
        i += 1
    flush()
    return out


# ------------------------------------------------------------- frontmatter --

def split_frontmatter(text: str, path=None):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise SourceError("SRC-NO-FRONTMATTER",
                          "file does not start with '---' frontmatter",
                          path=path, line=1)
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm_text = "\n".join(lines[1:idx])
            try:
                fm = yaml.safe_load(fm_text)
            except yaml.YAMLError as e:
                raise SourceError("SRC-BAD-FRONTMATTER", f"unparseable frontmatter: {e}",
                                  path=path, line=1)
            if not isinstance(fm, dict):
                raise SourceError("SRC-BAD-FRONTMATTER",
                                  "frontmatter is not a mapping", path=path, line=1)
            return fm, lines[idx + 1:], idx + 2
    raise SourceError("SRC-BAD-FRONTMATTER", "unterminated frontmatter",
                      path=path, line=1)


# ------------------------------------------------------------------ tables --

def _split_row(line: str):
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def _parse_table(lines, i, path, base):
    start = i
    rows = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        rows.append((_split_row(lines[i]), base + i))
        i += 1
    header, body = [], []
    if len(rows) >= 2 and all(TABLE_SEP_RE.match(c) for c in rows[1][0]):
        header = [parse_inlines(c, path, rows[0][1]) for c in rows[0][0]]
        body_rows = rows[2:]
    else:
        body_rows = rows
    for cells, ln in body_rows:
        body.append([parse_inlines(c, path, ln) for c in cells])
    return MarkdownTable(header, body, line=base + start), i


# ------------------------------------------------------------------ blocks --

def _parse_attrs(rest: str, path, line):
    attrs = {}
    remainder = rest.strip()
    while remainder:
        m = ATTR_RE.match(remainder)
        if not m:
            raise SourceError("SRC-BAD-FENCE",
                              f"unparseable attribute text {remainder!r}",
                              path=path, line=line)
        attrs[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
        remainder = remainder[m.end():].strip()
    return attrs


def _capture_block(lines, i, btype, path, base):
    """Collect body lines of the fence opened at lines[i]; returns
    (body_lines, next_index).  Raw bodies end at the first bare ``:::``;
    markdown bodies track one level of inner fences (note-family figure)."""
    raw = BLOCK_SPECS.get(btype, {}).get("body") == BODY_RAW
    body = []
    depth = 0
    j = i + 1
    while j < len(lines):
        stripped = lines[j].strip()
        if stripped == ":::":
            if depth > 0 and not raw:
                depth -= 1
                body.append(lines[j])
            else:
                return body, j + 1
        elif not raw and FENCE_RE.match(stripped):
            depth += 1
            body.append(lines[j])
        else:
            body.append(lines[j])
        j += 1
    raise SourceError("SRC-UNTERMINATED-BLOCK",
                      f":::{btype} block never closed", path=path, line=base + i)


def _parse_block(lines, i, path, base, inner=False):
    fence_line = base + i
    m = FENCE_RE.match(lines[i].strip())
    btype = m.group(1)
    attrs = _parse_attrs(m.group(2), path, fence_line)
    body_lines, nxt = _capture_block(lines, i, btype, path, base)
    spec = BLOCK_SPECS.get(btype)
    blk = Block(btype, attrs, {}, line=fence_line)

    if spec is None:
        blk.raw_body = "\n".join(body_lines)
        return blk, nxt

    # Leading ``field: value`` lines (blank lines between them allowed);
    # the field region ends at the first non-blank line that is not a field.
    k = 0
    if spec["fields"]:
        while k < len(body_lines):
            stripped = body_lines[k].strip()
            if not stripped:
                k += 1
                continue
            fm = FIELD_RE.match(stripped)
            if fm and fm.group(1) in spec["fields"]:
                blk.fields[fm.group(1)] = fm.group(2).strip()
                k += 1
            else:
                break
    rest = body_lines[k:]

    mode = spec["body"]
    if mode == BODY_RAW:
        blk.raw_body = "\n".join(rest).strip("\n")
    elif mode == BODY_MARKDOWN:
        if inner:
            raise SourceError("SRC-NESTED-BLOCK",
                              f":::{btype} cannot nest inside another block",
                              path=path, line=fence_line)
        blk.body, blk.footnotes = _parse_nodes(rest, base + i + 1 + k, path,
                                               inner=True)
    elif mode == BODY_TABLE:
        j = 0
        while j < len(rest) and not rest[j].strip():
            j += 1
        if j < len(rest) and rest[j].lstrip().startswith("|"):
            blk.table, j = _parse_table(rest, j, path, base + i + 1 + k)
        leftover = "\n".join(rest[j:]).strip()
        if leftover:
            blk.raw_body = leftover
    else:  # BODY_NONE
        leftover = "\n".join(rest).strip()
        if leftover:
            blk.raw_body = leftover
    return blk, nxt


# ------------------------------------------------------------------- lists --

def _parse_list(lines, i, path, base):
    entries = []
    while i < len(lines):
        m = LIST_RE.match(lines[i])
        if m:
            entries.append([len(m.group(1)), m.group(2) != "-" and m.group(2) != "*",
                            m.group(3), base + i])
            i += 1
        elif lines[i].strip() and lines[i].startswith("  ") and entries and \
                not LIST_RE.match(lines[i].strip()):
            entries[-1][2] += " " + lines[i].strip()
            i += 1
        else:
            break

    def build(pos, indent):
        node = ListNode(ordered=entries[pos][1], items=[], line=entries[pos][3])
        while pos < len(entries):
            ind, _, text, ln = entries[pos]
            if ind < indent:
                break
            if ind > indent:
                sub, pos = build(pos, ind)
                target = node.items[-1] if node.items else None
                if target is None:
                    target = ListItem([])
                    node.items.append(target)
                target.children.append(sub)
                continue
            node.items.append(ListItem([Para(parse_inlines(text, path, ln), ln)]))
            pos += 1
        return node, pos

    node, _ = build(0, entries[0][0])
    return node, i


# ---------------------------------------------------------------- document --

def _is_structural(line: str) -> bool:
    s = line.strip()
    return bool(
        not s
        or FENCE_RE.match(s) or s == ":::"
        or HEADING_RE.match(line)
        or LIST_RE.match(line)
        or FOOTDEF_RE.match(line)
        or s.startswith(">")
        or s.startswith("|")
    )


def _parse_nodes(lines, base, path, inner=False):
    nodes = []
    footnotes = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s == ":::":
            raise SourceError("SRC-STRAY-FENCE", "'::: ' closes no open block",
                              path=path, line=base + i)
        fm = FENCE_RE.match(s)
        if fm:
            blk, i = _parse_block(lines, i, path, base, inner=inner)
            for label, fdef in blk.footnotes.items():
                if label in footnotes:
                    raise SourceError("SRC-DUP-FOOTNOTE",
                                      f"footnote [^{label}] defined twice",
                                      path=path, line=fdef.line)
                footnotes[label] = fdef
            blk.footnotes = {}
            nodes.append(blk)
            continue
        hm = HEADING_RE.match(line)
        if hm:
            text = hm.group(2)
            nodes.append(Heading(len(hm.group(1)),
                                 parse_inlines(text, path, base + i),
                                 text, line=base + i))
            i += 1
            continue
        fd = FOOTDEF_RE.match(line)
        if fd:
            label = fd.group(1)
            if label in footnotes:
                raise SourceError("SRC-DUP-FOOTNOTE",
                                  f"footnote [^{label}] defined twice",
                                  path=path, line=base + i)
            footnotes[label] = FootnoteDefinition(
                label, parse_inlines(fd.group(2), path, base + i), line=base + i)
            i += 1
            continue
        if s.startswith(">"):
            start = i
            quoted = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quoted.append(lines[i].strip()[1:].lstrip())
                i += 1
            inner_nodes, extra = _parse_nodes(quoted, base + start, path, inner=True)
            if extra:
                raise SourceError("SRC-BAD-QUOTE",
                                  "footnote definition inside blockquote",
                                  path=path, line=base + start)
            nodes.append(BlockQuote(inner_nodes, line=base + start))
            continue
        if s.startswith("|"):
            table, i = _parse_table(lines, i, path, base)
            nodes.append(table)
            continue
        lm = LIST_RE.match(line)
        if lm:
            node, i = _parse_list(lines, i, path, base)
            nodes.append(node)
            continue
        start = i
        para_lines = [s]
        i += 1
        while i < len(lines) and not _is_structural(lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        nodes.append(Para(parse_inlines(" ".join(para_lines), path, base + start),
                          line=base + start))
    return nodes, footnotes


def parse_text(text: str, path: str) -> SourceDoc:
    fm, body_lines, body_start = split_frontmatter(text, path)
    nodes, footnotes = _parse_nodes(body_lines, body_start, path)
    return SourceDoc(path=path, frontmatter=fm, children=nodes,
                     footnotes=footnotes)


def parse_source(path) -> SourceDoc:
    with open(path, encoding="utf-8") as f:
        return parse_text(f.read(), str(path))
