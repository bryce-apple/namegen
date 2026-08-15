"""Seed generator (brief §2.5): skeleton .md files from a course plan.

Frontmatter is generated here, not hand-written (§3.1).  Content bodies are
explicit TODO stubs — the seed never invents content, and stub files pass
the structural source checks so a freshly seeded course builds end to end.
"""

from pathlib import Path

from . import constants as C

_INTRO_BODY = """\
TODO: introduction for {title}.
"""

_CONTENT_BODY = """\
:::objective zone=ours
TODO: objective for {address}.
:::

TODO: body for {address}.

:::summary
TODO: summary for {address}.
:::
"""


def _frontmatter(address, title):
    return (
        "---\n"
        f"address:     {address}\n"
        f"title:       {title}\n"
        "serves:      []\n"
        "obligation:  spine\n"
        "instances:   []\n"
        "terms_first_use: []\n"
        "---\n\n"
    )


def seed_course(plan, outdir):
    """Emit one skeleton file per planned subsection.  Returns
    (written_paths, warnings).  Warnings flag containers that will fail the
    §7 structure rule — missing *-S0 intro or *-QZ manifest entry — so the
    plan gets fixed before authoring starts, not after."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    warnings = []
    manifest = plan.manifest_by_address
    for container in plan.iter_containers():
        subs = container.subsections
        if plan.enforce_intro_terminal:
            if not (subs and subs[0].endswith(C.INTRO_ADDRESS_SUFFIX)):
                warnings.append(
                    f"{container.address}: first subsection is not an "
                    f"introduction (*{C.INTRO_ADDRESS_SUFFIX})")
            qz = container.address + C.TERMINAL_ACTIVITY_SUFFIX
            if qz not in manifest:
                warnings.append(
                    f"{container.address}: manifest lacks terminal activity "
                    f"{qz}")
        for addr in subs:
            path = outdir / f"{addr}.md"
            if path.exists():
                continue    # never clobber authored work
            if addr.endswith(C.INTRO_ADDRESS_SUFFIX):
                text = _frontmatter(addr, C.INTRODUCTION_SECTION_TITLE) + \
                    _INTRO_BODY.format(title=container.title)
            else:
                text = _frontmatter(addr, f"TODO title for {addr}") + \
                    _CONTENT_BODY.format(address=addr)
            path.write_text(text, encoding="utf-8")
            written.append(str(path))
    return written, warnings
