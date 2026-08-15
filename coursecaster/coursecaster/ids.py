"""Deterministic five-character element ids (brief §5.12).

Corpus ids are opaque five-character strings beginning with a letter
(``r09g9``, ``x65sc``, ``ba0c7``).  Ours are a stable hash of the pipeline
address plus the element's tag and per-address ordinal — never a counter —
so a rebuild of identical input is byte-identical, and edits to one
subsection do not churn ids in another.

Whether the platform reassigns ids on ingest is unverified; if it does,
ours are stripped at no cost.
"""

import hashlib

_FIRST = "abcdefghijklmnopqrstuvwxyz"
_REST = "abcdefghijklmnopqrstuvwxyz0123456789"


def _encode(digest: bytes) -> str:
    n = int.from_bytes(digest[:8], "big")
    first = _FIRST[n % 26]
    n //= 26
    rest = []
    for _ in range(4):
        rest.append(_REST[n % 36])
        n //= 36
    return first + "".join(rest)


def stable_id(seed: str) -> str:
    return _encode(hashlib.sha256(seed.encode("utf-8")).digest())


class IdAllocator:
    """Allocates document-unique ids.

    Seed = ``course|address|tag|ordinal-within-address`` where the ordinal
    counts prior same-tag elements under the same address scope.  Collisions
    across the document are resolved by deterministic re-hashing, so the
    result depends only on the input, never on run order or clock.
    """

    def __init__(self, course_slug: str):
        self.course = course_slug
        self._used = set()
        self._ordinals = {}

    def allocate(self, address: str, tag: str) -> str:
        key = (address, tag)
        ordinal = self._ordinals.get(key, 0)
        self._ordinals[key] = ordinal + 1
        seed = f"{self.course}|{address}|{tag}|{ordinal}"
        candidate = stable_id(seed)
        salt = 0
        while candidate in self._used:
            salt += 1
            candidate = stable_id(f"{seed}|{salt}")
        self._used.add(candidate)
        return candidate
