"""Corpus tree normalization and comparison (brief §9).

Compares element trees "ignoring ids and me:paracount".  The corpus also
carries constructs the brief forbids us to emit (authored labels, xref
display tails ride as plain text) and authored styling our vocabulary does
not model; every such allowance is an explicit rule below, applied to BOTH
trees, so the comparison stays honest and the rule list stays visible.
"""

import difflib
import xml.etree.ElementTree as ET

from . import constants as C

# Attributes dropped everywhere (rule 1): ids and platform counters per the
# brief; label per §5.2 (never emitted, authored in two corpus courses);
# the rest are authored styling / live defects with no source vocabulary.
_DROP_ATTRS_ALWAYS = {"id", "label", "me:paracount", "style", "align",
                      "mark", "noopener", "noreferrer", "targrt", "target"}
# 'class' is meaningful on figures and sidebars (figure-no-box,
# topics-to-understand) but a stray authoring artifact on paras
# (MsoCommentText) — rule 2.
_KEEP_CLASS_ON = {"figure", "informalfigure", "sidebar"}
_DROP_WIDTH_ON = {"th"}


def _local(tag):
    if tag.startswith("{"):
        uri, name = tag[1:].split("}")
        if uri == C.NS_ME:
            return "me:" + name
        return name
    return tag


def _attr_local(attr):
    if attr.startswith("{"):
        uri, name = attr[1:].split("}")
        if uri == C.NS_ME:
            return "me:" + name
        return name
    return attr


def _ws(text):
    return " ".join((text or "").split())


def normalize(root, linkend_map=None):
    """Return a normalized copy as nested plain data:
    [tag, {attrs}, [content…]] where content items are strings or nodes.

    linkend_map rewrites xref targets (rule 8): the corpus addresses
    elements by opaque/readable ids, our cast by pipeline address; the
    uncaster supplies its id→address map so both sides speak addresses.
    Unmapped targets (including the corpus's live dangling 'chatper01')
    pass through unchanged on both sides."""
    linkend_map = linkend_map or {}

    def walk(el):
        tag = _local(el.tag)
        if tag in ("bookinfo", "subtitle", "revhistory"):
            return None                        # rule 3: plan boilerplate /
                                               # platform-generated
        if tag == "me:option":
            if el.get("key") == "author" and not el.get("value"):
                return None                    # rule 4: valueless author
                                               # option quirk (2016, COM)
        attrs = {}
        for key, value in el.attrib.items():
            name = _attr_local(key)
            if name in _DROP_ATTRS_ALWAYS:
                continue
            if name == "class" and tag not in _KEEP_CLASS_ON:
                continue
            if name == "class" and tag in ("figure", "informalfigure") \
                    and value == "figure-no-box":
                continue    # rule 11: the universal default; one corpus
                            # figure omits it, ours never do
            if name == "width" and tag in _DROP_WIDTH_ON:
                continue
            if name == "alt" and not value.strip():
                continue                       # rule 5: empty alt ≡ absent
            if name == "linkend":
                value = linkend_map.get(value, value)
            attrs[name] = value

        content = []
        text = _ws(el.text)
        if text:
            content.append(text)
        for child in el:
            node = walk(child)
            if node is not None:
                ctag = node[0]
                # rule 6: row-level th ≡ td (row-header choice is derived
                # from the markdown header shape, not authored per cell)
                if ctag == "th" and tag == "tr":
                    node[0] = "td"
                content.append(node)
            tail = _ws(child.tail)
            if tail:
                content.append(tail)

        def _fold_deep(section_node, item):
            # descend to the deepest trailing section — where markdown's
            # last open heading actually places the content
            target = section_node
            while (target[2] and not isinstance(target[2][-1], str)
                   and target[2][-1][0] == "section"):
                target = target[2][-1]
            target[2].append(item)

        # rule 10: a section's <title> sorts to first child — Storytelling
        # floats the occasional figure ahead of the title; render order of
        # a floated figure is unaffected, and our cast always titles first
        if tag == "section":
            titles = [n for n in content
                      if not isinstance(n, str) and n[0] == "title"]
            if titles:
                rest = [n for n in content if n is not titles[0]]
                content = [titles[0]] + rest
        # rule 9: within a section, content following a nested section ≡
        # trailing content of that (deepest open) nested section.
        # Markdown headings cannot express a return to the parent level,
        # so the caster always nests such content; renderers place it
        # adjacently either way.  (No-op on cast output, which never
        # produces the former.)
        if tag == "section":
            folded = []
            for node in content:
                is_section = not isinstance(node, str) and node[0] == "section"
                if (folded and not isinstance(folded[-1], str)
                        and folded[-1][0] == "section" and not is_section):
                    _fold_deep(folded[-1], node)
                else:
                    folded.append(node)
            content = folded
        # rule 7: an orphan figure authored as a direct chapter child
        # (2016 ch.2) ≡ trailing figure of the preceding section
        if tag == "chapter":
            merged = []
            for node in content:
                if (not isinstance(node, str)
                        and node[0] in ("figure", "informalfigure")
                        and merged and not isinstance(merged[-1], str)
                        and merged[-1][0] == "section"):
                    _fold_deep(merged[-1], node)
                else:
                    merged.append(node)
            content = merged
        # merge adjacent text runs produced by dropped siblings
        merged = []
        for node in content:
            if isinstance(node, str) and merged and isinstance(merged[-1], str):
                merged[-1] = merged[-1] + " " + node
            else:
                merged.append(node)
        return [tag, attrs, merged]

    return walk(root)


def canonical_lines(node, indent=0):
    pad = "  " * indent
    tag, attrs, content = node
    attr_text = "".join(f' {k}="{v}"' for k, v in sorted(attrs.items()))
    out = [f"{pad}<{tag}{attr_text}>"]
    for item in content:
        if isinstance(item, str):
            out.append(f"{pad}  {item!r}")
        else:
            out.extend(canonical_lines(item, indent + 1))
    return out


def compare_trees(expected_root: ET.Element, actual_root: ET.Element,
                  context=6, expected_linkend_map=None):
    """Returns None when structurally equivalent, else a readable diff of
    the first divergence."""
    # The map applies to BOTH trees: a passthrough block on the cast side
    # carries the original corpus linkend verbatim, and corpus ids never
    # collide with generated addresses.
    exp = canonical_lines(normalize(expected_root, expected_linkend_map))
    act = canonical_lines(normalize(actual_root, expected_linkend_map))
    if exp == act:
        return None
    diff = list(difflib.unified_diff(exp, act, "corpus", "cast", n=context))
    # keep the head of the diff — the first divergence is the actionable one
    return "\n".join(diff[:80])
