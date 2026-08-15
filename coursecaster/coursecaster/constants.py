"""Central constants for the course caster.

Everything here is a deliberate, single-point-of-change decision. In
particular the PENDING token carrier is unverified against platform ingest
(brief §5.6) and must remain swappable without touching cast logic.
"""

# ---------------------------------------------------------------------------
# Pending-reference token (brief §5.6).
#
# UNVERIFIED: whether platform ingest tolerates a non-GUID ``guid`` value.
# This format string is the single configurable constant for the carrier.
# An alternative carrier (XML comment, sidecar file) can be swapped in by
# changing PENDING_TOKEN_FORMAT / pending_token() / parse_pending_token()
# only; cast logic calls these helpers and never builds tokens itself.
# ---------------------------------------------------------------------------
PENDING_TOKEN_FORMAT = "PENDING:{address}"
PENDING_TOKEN_PREFIX = "PENDING:"


def pending_token(address: str) -> str:
    return PENDING_TOKEN_FORMAT.format(address=address)


def parse_pending_token(value: str):
    """Return the address carried by a pending token, or None."""
    if value.startswith(PENDING_TOKEN_PREFIX):
        return value[len(PENDING_TOKEN_PREFIX):]
    return None


# Marker emitted for constructs whose cast target is unknown (brief §5.10).
# Output validation must fail while any of these are present.
PENDING_CAST_MARKER = "PENDING-CAST"

# ---------------------------------------------------------------------------
# Namespaces.  The corpus binds the Textbook namespace to ``me:`` but the
# patch document binds the same URI to ``be:`` — validators resolve by URI,
# never by prefix (brief §7).
# ---------------------------------------------------------------------------
NS_ME = "http://www.bookeducator.com/Textbook"
NS_XI = "http://www.w3.org/2001/XInclude"

# ---------------------------------------------------------------------------
# Manifest vocabulary (brief §3.2 / §5.6).
# ---------------------------------------------------------------------------
MANIFEST_STATUSES = ("resolved", "specified", "proposed", "omitted")
MANIFEST_OWNERS = ("pipeline", "platform", "partner", "unassigned")
MANIFEST_KINDS = ("activity", "material", "video", "figure")

# GUID type suffixes (brief §5.6): the trailing segment encodes object type.
GUID_SUFFIXES = {
    "activity": "1x2",
    "material": "1x3",
}

# ---------------------------------------------------------------------------
# Cast targets.  "corpus" = confirmed by corpus study (see STUDY.md);
# "UNVERIFIED" = no corpus witness, kept here so a finding changes one line.
# ---------------------------------------------------------------------------
OBJECTIVE_SIDEBAR_CLASS = "topics-to-understand"          # corpus (2016 ×12)
OBJECTIVE_SIDEBAR_TITLE = "Learning Objectives"           # corpus (2016 ×12)
SUMMARY_SECTION_TITLE = "Summary"                         # corpus (1761c ×12): a section, not a sidebar
INTRODUCTION_SECTION_TITLE = "Introduction"               # corpus (COM, 1761c)
TERMINAL_ACTIVITY_SECTION_TITLE = "Quick Check"           # corpus majority; manifest `title` overrides
FIGURE_DEFAULT_CLASS = "figure-no-box"                    # corpus (universal, 326/327)
CREDIT_PARA_STYLE = "font-size:8pt"                       # corpus (220 credit paras)
VIDEO_DEFAULT_WIDTH = "450"                               # corpus (57/57 videodata)
ACCESS_OPTION_KEY = "access"                              # corpus: me:option on paid chapters
EQUATION_ALT_ROLE = "latex"                               # UNVERIFIED: no equation in any corpus course

# Address conventions (mechanical, enforced — never inferred):
#   *-S0  : introduction subsection of its container (cast with label="")
#   *-QZ  : terminal activity of its container (manifest entry, cast last)
INTRO_ADDRESS_SUFFIX = "-S0"
TERMINAL_ACTIVITY_SUFFIX = "-QZ"

# Only label ever allowed in output: the empty label on introduction
# sections (brief §5.2).
INTRO_LABEL_VALUE = ""
