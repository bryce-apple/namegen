"""Source AST node types.

The parser produces these; the caster consumes them.  Nothing here is
inferred — every node corresponds to explicit annotation or mechanical
markdown structure.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------- inline ----

@dataclass
class Text:
    value: str


@dataclass
class Bold:
    children: list


@dataclass
class Italic:
    children: list


@dataclass
class Link:
    children: list
    url: str


@dataclass
class TermDef:
    """``{{term:phrase|definition}}`` — glossary entry at first use."""
    phrase: str
    definition: str


@dataclass
class Xref:
    """``{{xref:ADDRESS}}`` — cross-reference by address."""
    address: str


@dataclass
class FootnoteRef:
    label: str


# ----------------------------------------------------------------- block ----

@dataclass
class Para:
    inlines: list
    line: int = 0


@dataclass
class Heading:
    level: int          # 2 for ##, 3 for ###
    inlines: list
    text: str           # raw heading text (for anchors)
    line: int = 0


@dataclass
class ListItem:
    children: list      # Para / ListNode


@dataclass
class ListNode:
    ordered: bool
    items: list         # [ListItem]
    line: int = 0


@dataclass
class BlockQuote:
    children: list
    line: int = 0


@dataclass
class MarkdownTable:
    """A bare markdown table (no :::table wrapper) → informaltable."""
    header: list        # [inlines] — may be empty
    rows: list          # [[inlines]]
    line: int = 0


@dataclass
class FootnoteDefinition:
    label: str
    inlines: list
    line: int = 0


@dataclass
class Block:
    """A ``:::type`` annotated block."""
    type: str
    attrs: dict                 # key=value attributes from the fence line
    fields: dict                # ``field: value`` leading lines
    body: list = field(default_factory=list)   # parsed body nodes
    raw_body: str = ""          # verbatim body text (equation, xml)
    table: Optional[MarkdownTable] = None      # for :::table
    footnotes: dict = field(default_factory=dict)  # defs authored in body
    line: int = 0


@dataclass
class SourceDoc:
    path: str
    frontmatter: dict
    children: list
    footnotes: dict             # label -> FootnoteDefinition
