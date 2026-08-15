"""The caster: source AST + plan → course XML (brief §5).

The caster never infers.  Every emission below traces to a corpus-confirmed
shape (STUDY.md) or a brief rule; where identifiers are missing or a
construct has no cast target, it raises — a guessed element is worse than a
failed build.
"""

from . import constants as C
from .errors import CastError
from .ids import IdAllocator
from .mdparse import parse_inlines
from .srcmodel import (
    Block, BlockQuote, Bold, FootnoteRef, Heading, Italic, Link, ListNode,
    MarkdownTable, Para, TermDef, Text, Xref,
)
from .xmlwrite import El, Raw, serialize


class CastResult:
    def __init__(self, xml: str, report: dict):
        self.xml = xml
        self.report = report


class _Ctx:
    def __init__(self, plan, sources):
        self.plan = plan
        self.sources = sources
        self.manifest = plan.manifest_by_address
        self.ids = IdAllocator(plan.slug)
        self.address = plan.slug          # current address scope for ids
        self.footnotes = {}               # current file's footnote defs
        self.report = {
            "passthrough": [],            # every :::xml block (§7)
            "tokens": [],                 # every PENDING token emitted
            "pending_casts": [],          # flipcards awaiting a cast rule
            "examples": [],
        }

    def iid(self, tag):
        return self.ids.allocate(self.address, tag)


# ------------------------------------------------------------------ inline --

def _add_inlines(ctx, parent, inlines):
    for node in inlines:
        if isinstance(node, Text):
            parent.append(node.value)
        elif isinstance(node, Bold):
            em = El("emphasis", {"role": "bold"})
            _add_inlines(ctx, em, node.children)
            parent.append(em)
        elif isinstance(node, Italic):
            em = El("emphasis")
            _add_inlines(ctx, em, node.children)
            parent.append(em)
        elif isinstance(node, Link):
            ul = El("ulink", {"href": node.url, "target": "_blank"})
            _add_inlines(ctx, ul, node.children)
            parent.append(ul)
        elif isinstance(node, TermDef):
            ge = El("glossentry", {"id": ctx.iid("glossentry")})
            gt = El("glossterm")
            gt.append(node.phrase)
            ge.append(gt)
            # Definition is the trailing text node after glossterm —
            # not a child element (§5.8, corpus-confirmed).
            ge.append(node.definition)
            parent.append(ge)
        elif isinstance(node, Xref):
            # Empty element; label and title derive at render (§5.9).
            parent.append(El("xref", {"linkend": node.address,
                                      "id": ctx.iid("xref")}))
        elif isinstance(node, FootnoteRef):
            fdef = ctx.footnotes.get(node.label)
            if fdef is None:
                raise CastError("CAST-UNDEFINED-FOOTNOTE",
                                f"footnote [^{node.label}] has no definition",
                                address=ctx.address)
            fn = El("footnote", {"id": ctx.iid("footnote")})
            _add_inlines(ctx, fn, fdef.inlines)
            parent.append(fn)
        else:
            raise CastError("CAST-UNKNOWN-INLINE",
                            f"no cast rule for {type(node).__name__}",
                            address=ctx.address)


def _para(ctx, inlines):
    p = El("para", {"id": ctx.iid("para")})
    _add_inlines(ctx, p, inlines)
    return p


# ----------------------------------------------------------- common blocks --

def _cast_list(ctx, node: ListNode):
    lst = El("orderedlist" if node.ordered else "itemizedlist",
             {"id": ctx.iid("orderedlist" if node.ordered else "itemizedlist")})
    for item in node.items:
        li = El("listitem", {"id": ctx.iid("listitem")})
        for child in item.children:
            if isinstance(child, Para):
                li.append(_para(ctx, child.inlines))
            elif isinstance(child, ListNode):
                li.append(_cast_list(ctx, child))
            else:
                raise CastError("CAST-BAD-LISTITEM",
                                f"list item cannot hold {type(child).__name__}",
                                address=ctx.address)
        lst.append(li)
    return lst


def _cast_markdown_table(ctx, node: MarkdownTable):
    # Bare markdown table → informaltable with tbody only (§5.7).
    tbl = El("informaltable", {"id": ctx.iid("informaltable")})
    tbody = El("tbody")
    if node.header:
        tr = El("tr")
        for cell in node.header:
            th = El("th")
            _add_inlines(ctx, th, cell)
            tr.append(th)
        tbody.append(tr)
    for row in node.rows:
        tr = El("tr")
        for cell in row:
            td = El("td")
            _add_inlines(ctx, td, cell)
            tr.append(td)
        tbody.append(tr)
    tbl.append(tbody)
    return tbl


def _cast_blockquote(ctx, node: BlockQuote):
    bq = El("blockquote", {"id": ctx.iid("blockquote")})
    for child in node.children:
        for el in _cast_node(ctx, child):
            bq.append(el)
    return bq


# --------------------------------------------------------- reference logic --

def _ref_entry(ctx, block, needs_kind):
    """Resolve a reference block against the manifest.  Returns
    (entry_or_None, status).  Consistency itself is the source validator's
    job; the caster still refuses to proceed on contradictions."""
    addr = block.attrs.get("address")
    status = block.attrs.get("status", "resolved")
    entry = ctx.manifest.get(addr) if addr else None
    if addr and entry is None:
        raise CastError("CAST-REF-UNKNOWN",
                        f"address {addr} is not in the manifest",
                        address=ctx.address, line=block.line)
    if entry is not None:
        if entry.status != status:
            raise CastError(
                "CAST-STATUS-MISMATCH",
                f"block says status={status}, manifest says {entry.status}",
                address=addr)
        if entry.kind != needs_kind:
            raise CastError(
                "CAST-KIND-MISMATCH",
                f"manifest {addr} is kind={entry.kind}, block is {needs_kind}",
                address=addr)
        status = entry.status
    if status not in ("resolved",) and addr is None:
        raise CastError(
            "CAST-REF-NO-ADDRESS",
            f":::{needs_kind} with status={status} needs a manifest address= "
            "to carry its PENDING token", address=ctx.address, line=block.line)
    return entry, status, addr


def _token(ctx, addr, kind, element):
    tok = C.pending_token(addr)
    ctx.report["tokens"].append({"address": addr, "kind": kind,
                                 "element": element})
    return tok


# ----------------------------------------------------------------- figures --

def _figure_title(ctx, block):
    t = El("title")
    _add_inlines(ctx, t, parse_inlines(block.fields["title"]))
    credit = block.fields.get("credit")
    if credit:
        # The image credit is a <para> nested inside <title> (§5.4).
        p = El("para", {"style": C.CREDIT_PARA_STYLE, "id": ctx.iid("para")})
        _add_inlines(ctx, p, parse_inlines(credit))
        t.append(p)
    return t


def _cast_figure(ctx, block):
    entry, status, addr = _ref_entry(ctx, block, "figure")
    if status in ("proposed", "omitted"):
        return []
    formal = block.attrs.get("formal", "true") != "false"
    if status == "specified":
        fileref = _token(ctx, addr, "figure", "imagedata")
    else:
        fileref = block.attrs.get("src")
        if not fileref:
            raise CastError("CAST-FIGURE-NO-SRC",
                            "resolved figure lacks src=", address=ctx.address,
                            line=block.line)
    alt = block.fields.get("alt")
    if alt is None:
        raise CastError("CAST-FIGURE-NO-ALT", "figure lacks alt",
                        address=ctx.address, line=block.line)

    if formal:
        if "title" not in block.fields:
            raise CastError("CAST-FIGURE-NO-TITLE",
                            "formal figure lacks title (use formal=false)",
                            address=ctx.address, line=block.line)
        attrs = {}
        if block.attrs.get("displaywidth"):
            attrs["width"] = block.attrs["displaywidth"]
        attrs["class"] = C.FIGURE_DEFAULT_CLASS
        if block.attrs.get("floatstyle"):
            attrs["floatstyle"] = block.attrs["floatstyle"]
        attrs["id"] = addr if addr else ctx.iid("figure")
        fig = El("figure", attrs)
        fig.append(_figure_title(ctx, block))
    else:
        attrs = {}
        if block.attrs.get("displaywidth"):
            attrs["width"] = block.attrs["displaywidth"]
        attrs["class"] = C.FIGURE_DEFAULT_CLASS
        if block.attrs.get("floatstyle"):
            attrs["floatstyle"] = block.attrs["floatstyle"]
        attrs["id"] = addr if addr else ctx.iid("informalfigure")
        fig = El("informalfigure", attrs)
    mo = El("mediaobject", {"id": ctx.iid("mediaobject")})
    io = El("imageobject")
    data = {"alt": alt, "fileref": fileref, "id": ctx.iid("imagedata")}
    # Pixel dimensions of the asset: emit when known, omit otherwise (§5.4).
    if block.attrs.get("width"):
        data["width"] = block.attrs["width"]
    if block.attrs.get("depth"):
        data["depth"] = block.attrs["depth"]
    io.append(El("imagedata", data))
    mo.append(io)
    fig.append(mo)
    return [fig]


# ------------------------------------------------------------------ video --

def _cast_video(ctx, block):
    """One component, two siblings: video first, then me:material (§5.5)."""
    entry, status, addr = _ref_entry(ctx, block, "video")
    if status in ("proposed", "omitted"):
        return []
    if status == "specified":
        fileref = _token(ctx, addr, "video", "videodata")
        guid = _token(ctx, addr, "video", "me:material")
    else:
        fileref = block.attrs.get("asset")
        guid = block.attrs.get("guid") or (entry.guid if entry else None)
        if not fileref or not guid:
            raise CastError(
                "CAST-VIDEO-UNRESOLVED",
                "resolved video needs asset= (numeric id) and guid= (material)",
                address=ctx.address, line=block.line)
        if not guid.endswith(C.GUID_SUFFIXES["material"]) and \
                C.parse_pending_token(guid) is None:
            raise CastError("CAST-GUID-SUFFIX",
                            f"material guid {guid} lacks "
                            f"{C.GUID_SUFFIXES['material']} suffix",
                            address=ctx.address, line=block.line)
    inf = El("informalfigure",
             {"class": C.FIGURE_DEFAULT_CLASS,
              "id": addr if addr else ctx.iid("informalfigure")})
    mo = El("mediaobject", {"id": ctx.iid("mediaobject")})
    vo = El("videoobject")
    data = {"fileref": fileref,
            "width": block.attrs.get("width", C.VIDEO_DEFAULT_WIDTH),
            "id": ctx.iid("videodata")}
    if block.attrs.get("duration"):
        data["me:duration"] = block.attrs["duration"]   # seconds; runtime derives
    if block.attrs.get("name"):
        data["me:name"] = block.attrs["name"]
    vo.append(El("videodata", data))
    mo.append(vo)
    inf.append(mo)
    mat = El("me:material", {"guid": guid, "id": ctx.iid("me:material")})
    return [inf, mat]


# --------------------------------------------------------------- activity --

def _cast_activity_guid(ctx, entry, block_guid, addr, line=None):
    status = entry.status if entry else "resolved"
    if status in ("proposed", "omitted"):
        return None
    if status == "specified":
        return _token(ctx, addr, "activity", "me:activity")
    guid = block_guid or (entry.guid if entry else None)
    if not guid:
        raise CastError("CAST-ACTIVITY-NO-GUID",
                        "resolved activity lacks guid", address=addr or ctx.address,
                        line=line)
    if not guid.endswith(C.GUID_SUFFIXES["activity"]):
        raise CastError("CAST-GUID-SUFFIX",
                        f"activity guid {guid} lacks "
                        f"{C.GUID_SUFFIXES['activity']} suffix",
                        address=addr or ctx.address, line=line)
    return guid


def _cast_activity(ctx, block):
    entry, status, addr = _ref_entry(ctx, block, "activity")
    guid = _cast_activity_guid(ctx, entry, block.attrs.get("guid"), addr,
                               block.line)
    if guid is None:
        return []
    return [El("me:activity", {"guid": guid, "id": ctx.iid("me:activity")})]


# ------------------------------------------------------------------ tables --

def _cast_table_block(ctx, block):
    if block.table is None:
        raise CastError("CAST-TABLE-EMPTY", ":::table holds no markdown table",
                        address=ctx.address, line=block.line)
    # Tables take <caption>; figures take <title> (§5.7).
    tbl = El("table", {"id": block.attrs.get("address") or ctx.iid("table")})
    caption = block.fields.get("caption")
    if caption:
        cap = El("caption")
        _add_inlines(ctx, cap, parse_inlines(caption))
        source = block.fields.get("source")
        if source:
            # UNVERIFIED carrier: mirrors the figure-credit para (STUDY.md).
            p = El("para", {"style": C.CREDIT_PARA_STYLE, "id": ctx.iid("para")})
            _add_inlines(ctx, p, parse_inlines(source))
            cap.append(p)
        tbl.append(cap)
    md = block.table
    row_headers = bool(md.header) and md.header[0] == []
    if md.header:
        # thead holds th directly — no tr (corpus-confirmed).
        thead = El("thead")
        for cell in md.header:
            th = El("th")
            _add_inlines(ctx, th, cell)
            thead.append(th)
        tbl.append(thead)
    tbody = El("tbody")
    for row in md.rows:
        tr = El("tr")
        for col, cell in enumerate(row):
            tag = "th" if (row_headers and col == 0) else "td"
            cel = El(tag)
            _add_inlines(ctx, cel, cell)
            tr.append(cel)
        tbody.append(tr)
    tbl.append(tbody)
    return [tbl]


# ------------------------------------------------- unresolved cast targets --

def _cast_flipcard(ctx, block):
    """Flip cards have no known cast target (§5.10).  Emit a PENDING-CAST
    marker; output validation fails while any exist.  This function is the
    single place a real cast rule will replace."""
    ctx.report["pending_casts"].append(
        {"type": "flipcard", "address": ctx.address, "line": block.line,
         "anchor": block.attrs.get("anchor")})
    marker = El("remark", {"role": C.PENDING_CAST_MARKER})
    marker.append(f"flipcard anchor={block.attrs.get('anchor')}")
    return [marker]


def _cast_equation(ctx, block):
    # UNVERIFIED: no corpus course contains an equation (STUDY.md).
    eq = El("informalequation", {"id": ctx.iid("informalequation")})
    alt = El("alt", {"role": C.EQUATION_ALT_ROLE})
    alt.append(block.raw_body)
    eq.append(alt)
    return [eq]


# ----------------------------------------------------------- framed blocks --

def _cast_objective(ctx, block):
    sb = El("sidebar", {"class": C.OBJECTIVE_SIDEBAR_CLASS,
                        "id": ctx.iid("sidebar")})
    t = El("title")
    t.append(C.OBJECTIVE_SIDEBAR_TITLE)
    sb.append(t)
    items = []
    for node in block.body:
        if isinstance(node, ListNode):
            items.extend(node.items)
        elif isinstance(node, Para):
            items.append(node)
        else:
            raise CastError("CAST-OBJECTIVE-BODY",
                            f"objective body cannot hold {type(node).__name__}",
                            address=ctx.address, line=block.line)
    if len(items) == 1:
        # A single-sentence objective emits <para>, not <orderedlist> (§5.3).
        node = items[0]
        inl = node.inlines if isinstance(node, Para) else node.children[0].inlines
        sb.append(_para(ctx, inl))
    else:
        ol = El("orderedlist", {"id": ctx.iid("orderedlist")})
        for item in items:
            li = El("listitem", {"id": ctx.iid("listitem")})
            if isinstance(item, Para):
                li.append(_para(ctx, item.inlines))
            else:
                for child in item.children:
                    if isinstance(child, Para):
                        li.append(_para(ctx, child.inlines))
            ol.append(li)
        sb.append(ol)
    return [sb]


def _cast_summary(ctx, block):
    # A section titled "Summary" — Storytelling shape, not a sidebar
    # (STUDY.md).
    sec = El("section", {"id": ctx.iid("section")})
    t = El("title")
    t.append(C.SUMMARY_SECTION_TITLE)
    sec.append(t)
    for node in block.body:
        for el in _cast_node(ctx, node):
            sec.append(el)
    return [sec]


def _cast_admonition(ctx, block):
    # Admonitions carry no attributes at all in the corpus — no id, no
    # class (STUDY.md).  Required <title>, then paragraphs/lists/figures.
    adm = El(block.type)
    t = El("title")
    t.append(block.attrs["title"])
    adm.append(t)
    for node in block.body:
        for el in _cast_node(ctx, node):
            adm.append(el)
    return [adm]


def _cast_example(ctx, block):
    # UNVERIFIED carrier: classless titled sidebar — the Business Ethics
    # case-study shape (STUDY.md).  Ledger facts ride in the report.
    ctx.report["examples"].append({
        "address": ctx.address, "line": block.line,
        "company": block.attrs["company"],
        "statement": block.attrs["statement"],
        "period": block.attrs["period"],
    })
    sb = El("sidebar", {"id": ctx.iid("sidebar")})
    t = El("title")
    t.append(block.fields.get("title") or f"Example: {block.attrs['company']}")
    sb.append(t)
    for node in block.body:
        for el in _cast_node(ctx, node):
            sb.append(el)
    return [sb]


def _cast_xml_passthrough(ctx, block):
    ctx.report["passthrough"].append({
        "address": ctx.address, "line": block.line,
        "preview": " ".join(block.raw_body.split())[:120],
    })
    return [Raw(block.raw_body)]


_BLOCK_CASTS = {
    "objective": _cast_objective,
    "summary": _cast_summary,
    "note": _cast_admonition,
    "important": _cast_admonition,
    "warning": _cast_admonition,
    "caution": _cast_admonition,
    "figure": _cast_figure,
    "video": _cast_video,
    "activity": _cast_activity,
    "table": _cast_table_block,
    "flipcard": _cast_flipcard,
    "equation": _cast_equation,
    "xml": _cast_xml_passthrough,
    "example": _cast_example,
}


def _cast_node(ctx, node):
    if isinstance(node, Para):
        return [_para(ctx, node.inlines)]
    if isinstance(node, ListNode):
        return [_cast_list(ctx, node)]
    if isinstance(node, BlockQuote):
        return [_cast_blockquote(ctx, node)]
    if isinstance(node, MarkdownTable):
        return [_cast_markdown_table(ctx, node)]
    if isinstance(node, Block):
        fn = _BLOCK_CASTS.get(node.type)
        if fn is None:
            raise CastError("CAST-UNKNOWN-BLOCK",
                            f"no cast rule for :::{node.type}",
                            address=ctx.address, line=node.line)
        return fn(ctx, node)
    raise CastError("CAST-UNKNOWN-NODE",
                    f"no cast rule for {type(node).__name__}",
                    address=ctx.address)


# --------------------------------------------------------------- sections --

def _cast_subsection(ctx, address):
    doc = ctx.sources.get(address)
    if doc is None:
        raise CastError("CAST-MISSING-SOURCE",
                        f"no source file for subsection {address}",
                        address=address)
    ctx.address = address
    ctx.footnotes = doc.footnotes
    attrs = {"id": address}
    if address.endswith(C.INTRO_ADDRESS_SUFFIX):
        # The one label we ever emit (§5.2).
        attrs = {"label": C.INTRO_LABEL_VALUE, "id": address}
    sec = El("section", attrs)
    t = El("title")
    t.append(doc.frontmatter.get("title", ""))
    sec.append(t)

    # Headings ##..#### open nested sections at depths 1..3 (STUDY.md).
    stack = [(0, sec)]
    for node in doc.children:
        if isinstance(node, Heading):
            depth = node.level - 1        # ## → depth 1
            if depth < 1 or depth > 3:
                raise CastError("CAST-BAD-HEADING",
                                f"heading level {node.level} has no cast rule "
                                "(## to #### allowed)",
                                address=address, line=node.line)
            while stack and stack[-1][0] >= depth:
                stack.pop()
            if not stack or stack[-1][0] != depth - 1:
                raise CastError("CAST-HEADING-JUMP",
                                f"heading level {node.level} skips a level",
                                address=address, line=node.line)
            sub = El("section", {"id": ctx.iid("section")})
            st = El("title")
            _add_inlines(ctx, st, node.inlines)
            sub.append(st)
            stack[-1][1].append(sub)
            stack.append((depth, sub))
        elif isinstance(node, Block) and node.type == "summary":
            # Summary is a section-level sibling in the corpus (Storytelling
            # closes every topic with one) — always a direct child of the
            # subsection root, never nested under an open heading.
            for el in _cast_node(ctx, node):
                sec.append(el)
        else:
            for el in _cast_node(ctx, node):
                stack[-1][1].append(el)
    return sec


def _cast_terminal_section(ctx, container):
    addr = container.address + C.TERMINAL_ACTIVITY_SUFFIX
    entry = ctx.manifest.get(addr)
    if entry is None:
        return None
    if entry.kind != "activity":
        raise CastError("CAST-KIND-MISMATCH",
                        f"terminal manifest entry {addr} must be kind=activity",
                        address=addr)
    ctx.address = addr
    guid = _cast_activity_guid(ctx, entry, None, addr)
    if guid is None:
        return None
    sec = El("section", {"id": addr})
    t = El("title")
    t.append(entry.title or C.TERMINAL_ACTIVITY_SECTION_TITLE)
    sec.append(t)
    sec.append(El("me:activity", {"guid": guid, "id": ctx.iid("me:activity")}))
    return sec


def _cast_container(ctx, container):
    ctx.address = container.address
    ch = El("chapter", {"id": container.address})
    if container.access:
        ch.append(El("me:option", {"key": C.ACCESS_OPTION_KEY,
                                   "value": container.access}))
    t = El("title")
    t.append(container.title)
    ch.append(t)
    for sub in container.subsections:
        ch.append(_cast_subsection(ctx, sub))
    for lesson in container.lessons:
        ch.append(_cast_container(ctx, lesson))
    term = _cast_terminal_section(ctx, container)
    if term is not None:
        ch.append(term)
    return ch


# --------------------------------------------------------------- bookinfo --

def _cast_bookinfo(ctx, info):
    bi = El("bookinfo")
    if info.get("edition"):
        e = El("edition")
        e.append(str(info["edition"]))
        bi.append(e)
    for group in info.get("authorgroups", []):
        ag = El("authorgroup", {"role": group["role"]})
        for person in group.get("authors", []):
            au = El("author")
            for key, tag in (("firstname", "firstname"), ("surname", "surname"),
                             ("email", "email")):
                if person.get(key):
                    el = El(tag)
                    el.append(person[key])
                    au.append(el)
            ag.append(au)
        bi.append(ag)
    if info.get("copyright"):
        cp = El("copyright")
        y = El("year")
        y.append(str(info["copyright"]["year"]))
        cp.append(y)
        h = El("holder")
        h.append(info["copyright"]["holder"])
        cp.append(h)
        bi.append(cp)
    if info.get("abstract"):
        ab = El("abstract")
        ab.append(_para(ctx, [Text(info["abstract"])]))
        bi.append(ab)
    # revhistory is platform-generated — never emitted (§5.11).
    return bi


# ------------------------------------------------------------------ entry --

def cast_course(plan, sources) -> CastResult:
    ctx = _Ctx(plan, sources)
    book = El("book", {"xmlns:xi": C.NS_XI, "xmlns:me": C.NS_ME})
    if plan.author:
        book.append(El("me:option", {"key": "author", "value": plan.author}))
    if plan.labeldefault_chapter:
        book.append(El("me:option", {"key": "labeldefault:chapter",
                                     "value": plan.labeldefault_chapter}))
    t = El("title")
    t.append(plan.title)
    book.append(t)
    if plan.subtitle:
        st = El("subtitle")
        st.append(plan.subtitle)
        book.append(st)
    book.append(_cast_bookinfo(ctx, plan.bookinfo))
    for unit in plan.units:
        book.append(_cast_container(ctx, unit))
    return CastResult(serialize(book), ctx.report)
