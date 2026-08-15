"""Course plan loader (brief §3.2).

The plan is the ratified skeleton: hierarchy, addresses, titles, and the
reference manifest.  JSON or YAML.  Unknown keys are fatal — a misspelled
key silently ignored is exactly the guessing this pipeline forbids.
"""

import json
from dataclasses import dataclass, field
from typing import Optional

import yaml

from .constants import MANIFEST_KINDS, MANIFEST_OWNERS, MANIFEST_STATUSES
from .errors import PlanError

_CONTAINER_KEYS = {"address", "title", "competency_statement", "competency_zone",
                   "access", "subsections", "lessons"}
_MANIFEST_KEYS = {"address", "kind", "status", "owner", "title", "guid",
                  "instance"}
_PLAN_KEYS = {"slug", "title", "subtitle", "author", "labeldefault_chapter",
              "bookinfo", "units", "manifest", "enforce_intro_terminal"}
_BOOKINFO_KEYS = {"edition", "abstract", "copyright", "authorgroups"}


@dataclass
class ManifestEntry:
    address: str
    kind: str
    status: str
    owner: str
    title: Optional[str] = None
    guid: Optional[str] = None
    instance: Optional[str] = None


@dataclass
class Container:
    address: str
    title: str
    kind: str                      # "unit" | "lesson"
    competency_statement: Optional[str] = None
    competency_zone: Optional[str] = None
    access: Optional[str] = None
    subsections: list = field(default_factory=list)   # addresses
    lessons: list = field(default_factory=list)       # [Container]


@dataclass
class CoursePlan:
    slug: str
    title: str
    subtitle: Optional[str]
    author: Optional[str]
    labeldefault_chapter: Optional[str]
    bookinfo: dict
    units: list                     # [Container]
    manifest: list                  # [ManifestEntry]
    # §7 requires every container to open with an introduction section and
    # close with a terminal activity section.  Uncast corpus plans switch
    # this off because the corpus predates the rule.
    enforce_intro_terminal: bool = True

    def iter_containers(self):
        for u in self.units:
            yield u
            yield from u.lessons

    def container_addresses(self):
        return [c.address for c in self.iter_containers()]

    def subsection_addresses(self):
        out = []
        for c in self.iter_containers():
            out.extend(c.subsections)
        return out

    @property
    def manifest_by_address(self):
        return {m.address: m for m in self.manifest}

    def all_addresses(self):
        """Every address an ``{{xref:}}`` may target: containers,
        subsections, and manifest entries."""
        return (set(self.container_addresses())
                | set(self.subsection_addresses())
                | {m.address for m in self.manifest})


def _require(d, key, where):
    if key not in d or d[key] in (None, ""):
        raise PlanError("PLAN-MISSING-KEY", f"{where} lacks required '{key}'")
    return d[key]


def _check_keys(d, allowed, where):
    unknown = set(d) - allowed
    if unknown:
        raise PlanError("PLAN-UNKNOWN-KEY",
                        f"{where} has unknown key(s): {', '.join(sorted(unknown))}")


def _load_container(d, kind):
    _check_keys(d, _CONTAINER_KEYS, f"{kind} entry")
    addr = _require(d, "address", kind)
    c = Container(
        address=addr,
        title=_require(d, "title", f"{kind} {addr}"),
        kind=kind,
        competency_statement=d.get("competency_statement"),
        competency_zone=d.get("competency_zone"),
        access=d.get("access"),
        subsections=list(d.get("subsections") or []),
    )
    if kind == "lesson" and d.get("lessons"):
        raise PlanError("PLAN-DEPTH", f"lesson {addr} cannot contain lessons")
    for sub in c.subsections:
        if not isinstance(sub, str):
            raise PlanError("PLAN-BAD-SUBSECTION",
                            f"{kind} {addr}: subsections must be addresses")
    c.lessons = [_load_container(x, "lesson") for x in (d.get("lessons") or [])]
    return c


def _load_manifest_entry(d):
    _check_keys(d, _MANIFEST_KEYS, "manifest entry")
    addr = _require(d, "address", "manifest entry")
    kind = _require(d, "kind", f"manifest {addr}")
    status = _require(d, "status", f"manifest {addr}")
    owner = _require(d, "owner", f"manifest {addr}")
    if kind not in MANIFEST_KINDS:
        raise PlanError("PLAN-BAD-KIND", f"manifest {addr}: unknown kind '{kind}'")
    if status not in MANIFEST_STATUSES:
        raise PlanError("PLAN-BAD-STATUS",
                        f"manifest {addr}: unknown status '{status}'")
    if owner not in MANIFEST_OWNERS:
        raise PlanError("PLAN-BAD-OWNER", f"manifest {addr}: unknown owner '{owner}'")
    return ManifestEntry(address=addr, kind=kind, status=status, owner=owner,
                         title=d.get("title"), guid=d.get("guid"),
                         instance=d.get("instance"))


def load_plan_data(data) -> CoursePlan:
    if not isinstance(data, dict):
        raise PlanError("PLAN-BAD-SHAPE", "plan root is not a mapping")
    _check_keys(data, _PLAN_KEYS, "plan")
    bookinfo = data.get("bookinfo") or {}
    _check_keys(bookinfo, _BOOKINFO_KEYS, "bookinfo")
    plan = CoursePlan(
        slug=_require(data, "slug", "plan"),
        title=_require(data, "title", "plan"),
        subtitle=data.get("subtitle"),
        author=data.get("author"),
        labeldefault_chapter=data.get("labeldefault_chapter"),
        bookinfo=bookinfo,
        units=[_load_container(u, "unit") for u in (data.get("units") or [])],
        manifest=[_load_manifest_entry(m) for m in (data.get("manifest") or [])],
        enforce_intro_terminal=bool(data.get("enforce_intro_terminal", True)),
    )
    seen = set()
    for a in (plan.container_addresses() + plan.subsection_addresses()
              + [m.address for m in plan.manifest]):
        if a in seen:
            raise PlanError("PLAN-DUP-ADDRESS", f"address {a} appears twice")
        seen.add(a)
    return plan


def load_plan(path) -> CoursePlan:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if str(path).endswith(".json"):
        data = json.loads(text)
    else:
        data = yaml.safe_load(text)
    return load_plan_data(data)
