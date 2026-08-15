"""Command-line entry: python -m coursecaster <command> …

Exit codes: 0 ok · 1 usage/internal · 2 validation failed · 3 build
incomplete (PENDING-CAST markers present).
"""

import argparse
import json
import sys
from pathlib import Path

from .cast import cast_course
from .derive import (coverage_matrix, example_ledger, reference_manifest,
                     term_register)
from .errors import CasterError
from .mdparse import parse_source
from .output_validator import validate_output
from .plan import load_plan
from .registers import load_term_register
from .seed import seed_course
from .source_validator import validate_sources


def load_sources(srcdir):
    sources = {}
    for path in sorted(Path(srcdir).glob("*.md")):
        sources[path.stem] = parse_source(path)
    return sources


def _write_json(data, out):
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if out:
        Path(out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _fail(errors):
    for e in errors.errors:
        print(str(e), file=sys.stderr)
    print(f"FAILED: {len(errors.errors)} fatal finding(s)", file=sys.stderr)
    return 2


def cmd_seed(args):
    plan = load_plan(args.plan)
    written, warnings = seed_course(plan, args.outdir)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"seeded {len(written)} file(s) into {args.outdir}")
    return 0


def cmd_validate_source(args):
    plan = load_plan(args.plan)
    sources = load_sources(args.srcdir)
    register = load_term_register(args.terms) if args.terms else None
    errors = validate_sources(plan, sources, register)
    if not errors.ok:
        return _fail(errors)
    print(f"source OK: {len(sources)} file(s)")
    return 0


def cmd_cast(args):
    plan = load_plan(args.plan)
    sources = load_sources(args.srcdir)
    register = load_term_register(args.terms) if args.terms else None
    errors = validate_sources(plan, sources, register)
    if not errors.ok:
        return _fail(errors)
    result = cast_course(plan, sources)
    Path(args.output).write_text(result.xml, encoding="utf-8")
    _write_json(result.report, args.output + ".report.json")
    out_errors, report = validate_output(result.xml, plan, sources,
                                         result.report)
    for item in report["passthrough"]:
        print(f"passthrough: {item['address']} line {item['line']}: "
              f"{item['preview']}", file=sys.stderr)
    if not out_errors.ok:
        rc = _fail(out_errors)
        return 3 if report["incomplete"] else rc
    print(f"cast OK: {args.output}")
    return 0


def cmd_validate_output(args):
    xml_text = Path(args.xml).read_text(encoding="utf-8")
    plan = load_plan(args.plan) if args.plan else None
    sources = load_sources(args.srcdir) if args.srcdir else None
    cast_report = None
    report_path = Path(args.xml + ".report.json")
    if report_path.exists():
        cast_report = json.loads(report_path.read_text(encoding="utf-8"))
    errors, report = validate_output(xml_text, plan, sources, cast_report)
    for item in report["passthrough"]:
        print(f"passthrough: {item['address']} line {item['line']}: "
              f"{item['preview']}")
    if not errors.ok:
        rc = _fail(errors)
        return 3 if report["incomplete"] else rc
    print("output OK")
    return 0


def cmd_derive(args):
    plan = load_plan(args.plan)
    sources = load_sources(args.srcdir)
    fn = {
        "terms": lambda: term_register(sources),
        "coverage": lambda: coverage_matrix(plan, sources),
        "references": lambda: reference_manifest(plan, sources),
        "examples": lambda: example_ledger(sources),
    }[args.what]
    _write_json(fn(), args.output)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="coursecaster")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="emit skeleton .md files from a plan")
    s.add_argument("plan")
    s.add_argument("outdir")
    s.set_defaults(fn=cmd_seed)

    s = sub.add_parser("validate-source", help="pre-build checks on markdown")
    s.add_argument("plan")
    s.add_argument("srcdir")
    s.add_argument("--terms", help="term register JSON")
    s.set_defaults(fn=cmd_validate_source)

    s = sub.add_parser("cast", help="markdown → course XML")
    s.add_argument("plan")
    s.add_argument("srcdir")
    s.add_argument("-o", "--output", required=True)
    s.add_argument("--terms", help="term register JSON")
    s.set_defaults(fn=cmd_cast)

    s = sub.add_parser("validate-output", help="post-build checks on XML")
    s.add_argument("xml")
    s.add_argument("--plan")
    s.add_argument("--srcdir")
    s.set_defaults(fn=cmd_validate_output)

    s = sub.add_parser("derive", help="computed registers and matrices")
    s.add_argument("what", choices=["terms", "coverage", "references",
                                    "examples"])
    s.add_argument("plan")
    s.add_argument("srcdir")
    s.add_argument("-o", "--output")
    s.set_defaults(fn=cmd_derive)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except CasterError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
