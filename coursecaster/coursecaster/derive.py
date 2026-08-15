"""Derivation scripts (brief §8).  Computed, never typed.

Each function returns a JSON-serializable structure; the CLI writes it with
sorted keys and no timestamps, so identical input yields identical bytes.
"""

from .errors import ErrorCollector, SourceError
from .source_validator import _iter_blocks, _iter_inlines
from .srcmodel import TermDef


def term_register(sources):
    """All glossary entries with addresses; enforces course-wide uniqueness.
    Internal control — never shipped (§5.8)."""
    errors = ErrorCollector()
    register = {}
    for addr in sorted(sources):
        doc = sources[addr]
        for node in _iter_inlines(doc.children):
            if isinstance(node, TermDef):
                key = node.phrase.casefold()
                if key in register:
                    errors.error(
                        SourceError, "SRC-TERM-DUP",
                        f"term '{node.phrase}' defined at "
                        f"{register[key]['address']} and again at {addr}")
                else:
                    register[key] = {
                        "term": node.phrase,
                        "address": addr,
                        "definition": node.definition,
                    }
    errors.raise_if_any()
    return {v["term"]: {"address": v["address"], "definition": v["definition"]}
            for v in register.values()}


def coverage_matrix(plan, sources):
    """Skills × subsections from the trace records in frontmatter:
    ``serves`` rows claim type 'serves', ``instances`` rows claim type
    'instance'; depth is the subsection's obligation."""
    matrix = {}
    for addr in sorted(sources):
        fm = sources[addr].frontmatter
        depth = fm.get("obligation")
        for skill in fm.get("serves") or []:
            matrix.setdefault(skill, {})[addr] = {
                "claim": "serves", "depth": depth}
        for instance in fm.get("instances") or []:
            matrix.setdefault(instance, {})[addr] = {
                "claim": "instance", "depth": depth}
    return {"skills": {k: matrix[k] for k in sorted(matrix)},
            "subsections": sorted(sources)}


def reference_manifest(plan, sources):
    """Every reference block with status and owner, joined against the
    plan manifest."""
    referenced_by = {}
    inline_refs = []
    for addr in sorted(sources):
        for block in _iter_blocks(sources[addr].children):
            if block.type in ("figure", "video", "activity"):
                ref_addr = block.attrs.get("address")
                record = {
                    "kind": block.type,
                    "status": block.attrs.get("status", "resolved"),
                    "owner": block.attrs.get("owner"),
                    "used_at": addr,
                    "line": block.line,
                }
                if ref_addr:
                    referenced_by.setdefault(ref_addr, []).append(addr)
                    record["address"] = ref_addr
                inline_refs.append(record)
    entries = []
    for m in plan.manifest:
        entries.append({
            "address": m.address,
            "kind": m.kind,
            "status": m.status,
            "owner": m.owner,
            "referenced_by": referenced_by.get(m.address, []),
        })
    return {"manifest": entries, "blocks": inline_refs}


def example_ledger(sources):
    """Worked examples with company, statement, and fiscal period."""
    out = []
    for addr in sorted(sources):
        for block in _iter_blocks(sources[addr].children):
            if block.type == "example":
                out.append({
                    "address": addr,
                    "line": block.line,
                    "company": block.attrs.get("company"),
                    "statement": block.attrs.get("statement"),
                    "period": block.attrs.get("period"),
                    "title": block.fields.get("title"),
                })
    return {"examples": out}
