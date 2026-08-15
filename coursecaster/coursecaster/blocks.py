"""The annotation block vocabulary (brief §4.2).

The single authority on which block types exist, which attributes and
fields each accepts, and which are required.  Parser, source validator and
caster all consult this table; nothing else defines vocabulary.
"""

# body modes
BODY_MARKDOWN = "markdown"   # parsed as markdown (paras, lists, inner figure)
BODY_RAW = "raw"             # verbatim text (equation LaTeX, xml passthrough)
BODY_NONE = "none"           # fields only
BODY_TABLE = "table"         # fields + a markdown table

NOTE_FAMILY = ("note", "important", "warning", "caution")

# Reference blocks point at platform objects tracked in the manifest.
# ``address=`` binds the block to its manifest entry; the brief's attribute
# lists omit it, but the PENDING token and reconciliation (§5.6, §7) need a
# manifest address, so it is part of the vocabulary and the seed generator
# writes it.  Required whenever status is not ``resolved``.
REFERENCE_BLOCKS = ("figure", "video", "activity")

BLOCK_SPECS = {
    "objective": {
        "attrs": {"zone"},
        "required_attrs": {"zone"},
        "fields": set(),
        "body": BODY_MARKDOWN,
    },
    "summary": {
        "attrs": set(),
        "required_attrs": set(),
        "fields": set(),
        "body": BODY_MARKDOWN,
    },
    **{
        name: {
            "attrs": {"title"},
            "required_attrs": {"title"},
            "fields": set(),
            "body": BODY_MARKDOWN,
        }
        for name in NOTE_FAMILY
    },
    "figure": {
        "attrs": {"formal", "status", "owner", "src", "address",
                  "width", "depth", "displaywidth", "floatstyle"},
        "required_attrs": set(),
        "fields": {"title", "alt", "credit", "brief"},
        "body": BODY_NONE,
    },
    "video": {
        "attrs": {"status", "owner", "address", "asset", "guid",
                  "duration", "name", "width"},
        "required_attrs": set(),
        "fields": {"title", "target_duration", "brief", "material_brief"},
        "body": BODY_NONE,
    },
    "activity": {
        "attrs": {"instance", "status", "owner", "guid", "address"},
        "required_attrs": set(),
        "fields": set(),
        "body": BODY_NONE,
    },
    "table": {
        "attrs": set(),
        "required_attrs": set(),
        "fields": {"caption", "source"},
        "body": BODY_TABLE,
    },
    "flipcard": {
        "attrs": {"anchor"},
        "required_attrs": {"anchor"},
        "fields": {"q", "a"},
        "body": BODY_NONE,
    },
    "equation": {
        "attrs": set(),
        "required_attrs": set(),
        "fields": set(),
        "body": BODY_RAW,
    },
    "xml": {
        "attrs": set(),
        "required_attrs": set(),
        "fields": set(),
        "body": BODY_RAW,
    },
    # Worked-example block backing the example ledger (§8).  The brief's
    # §4.2 table omits it while §8 requires "worked examples with company,
    # statement, and fiscal period" to be derivable; this block is the
    # mechanical carrier for those facts.  Cast target UNVERIFIED.
    "example": {
        "attrs": {"company", "statement", "period"},
        "required_attrs": {"company", "statement", "period"},
        "fields": {"title"},
        "body": BODY_MARKDOWN,
    },
}
