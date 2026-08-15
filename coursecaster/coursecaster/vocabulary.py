"""Output vocabulary (brief §7).

OBSERVED: every element local-name seen in the corpus study (STUDY.md),
including live defects' *containers* but not the defects themselves —
``emphais`` stays out so the check would catch it, as a schema would have.

EMITTED_EXTRAS: elements our caster emits that no corpus course happens to
contain (equations have no witness; the PENDING-CAST remark by design).
Anything outside the union is reported.
"""

OBSERVED = {
    # containers & text
    "book", "chapter", "section", "para", "title", "subtitle", "sidebar",
    "blockquote", "epigraph",
    # lists
    "itemizedlist", "orderedlist", "listitem",
    # figures & media
    "figure", "informalfigure", "mediaobject", "imageobject", "imagedata",
    "videoobject", "videodata",
    # tables
    "table", "informaltable", "caption", "thead", "tbody", "tr", "th", "td",
    # glossary & inline
    "glossentry", "glossterm", "emphasis", "footnote", "ulink", "xref",
    "sub", "br",
    # admonitions
    "note", "important", "warning", "caution",
    # bookinfo
    "bookinfo", "edition", "authorgroup", "author", "personname", "firstname",
    "surname", "email", "affiliation", "orgname", "personblurb", "copyright",
    "year", "holder", "abstract", "date",
    # platform-generated (present in corpus; we never emit them — see
    # NEVER_EMIT_ELEMENTS)
    "revhistory", "revision", "revnumber", "revremark",
    # me: namespace
    "option", "activity", "material", "patches",
}

EMITTED_EXTRAS = {
    "informalequation", "alt",     # UNVERIFIED cast target for :::equation
    "remark",                      # PENDING-CAST marker carrier (§5.10)
}

VOCABULARY = OBSERVED | EMITTED_EXTRAS

# §5.11 — never in OUR output (they are corpus-observed platform artifacts).
NEVER_EMIT_ELEMENTS = {"revhistory", "revision", "revnumber", "revremark",
                       "glossary"}
