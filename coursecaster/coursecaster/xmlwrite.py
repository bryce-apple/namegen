"""Deterministic XML tree + serializer.

We do not use ElementTree for writing: byte-identical output requires full
control of attribute order, escaping, indentation, and namespace prefixes.
Attribute order is insertion order (cast code is deterministic), with ``id``
always last, matching corpus style
(``<figure width="50%" class="figure-no-box" ... id="z87gr">``).
"""


class Raw:
    """Verbatim XML passthrough (``:::xml`` blocks).  Well-formedness is
    checked by the output validator, which parses the whole document."""

    def __init__(self, xml: str):
        self.xml = xml


class El:
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = dict(attrs) if attrs else {}
        self.children = list(children) if children else []  # El | str | Raw

    def append(self, child):
        self.children.append(child)
        return child

    def set(self, key, value):
        self.attrs[key] = value

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, El):
                yield from c.iter()

    def text_content(self):
        out = []
        for c in self.children:
            if isinstance(c, str):
                out.append(c)
            elif isinstance(c, El):
                out.append(c.text_content())
        return "".join(out)


def escape_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_attr(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# Elements rendered inline (no child indentation): anything that carries
# mixed/flowing content.  Note <title> holds a nested credit <para> inline
# in the corpus (brief §5.4).
_INLINE = {
    "para", "title", "emphasis", "ulink", "glossterm", "glossentry",
    "footnote", "xref", "caption", "th", "td", "alt", "remark",
}


def _has_text(el: El) -> bool:
    return any(isinstance(c, str) and c != "" for c in el.children)


def _render_open(el: El) -> str:
    attrs = dict(el.attrs)
    tail = {}
    if "id" in attrs:
        tail["id"] = attrs.pop("id")
    parts = [el.tag]
    for k, v in {**attrs, **tail}.items():
        parts.append(f'{k}="{escape_attr(str(v))}"')
    return "<" + " ".join(parts)


def _render_inline(el: El) -> str:
    open_tag = _render_open(el)
    if not el.children:
        return open_tag + "/>"
    body = []
    for c in el.children:
        if isinstance(c, str):
            body.append(escape_text(c))
        elif isinstance(c, Raw):
            body.append(c.xml.strip())
        else:
            body.append(_render_inline(c))
    return f"{open_tag}>{''.join(body)}</{el.tag}>"


def _render_block(el: El, indent: int, out: list):
    pad = "  " * indent
    if el.tag in _INLINE or _has_text(el):
        out.append(pad + _render_inline(el))
        return
    open_tag = _render_open(el)
    if not el.children:
        out.append(f"{pad}{open_tag}/>")
        return
    out.append(pad + open_tag + ">")
    for c in el.children:
        if isinstance(c, str):
            if c:
                out.append("  " * (indent + 1) + escape_text(c))
        elif isinstance(c, Raw):
            for line in c.xml.strip().splitlines():
                out.append("  " * (indent + 1) + line)
        else:
            _render_block(c, indent + 1, out)
    out.append(f"{pad}</{el.tag}>")


def serialize(root: El) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>']
    _render_block(root, 0, out)
    return "\n".join(out) + "\n"
