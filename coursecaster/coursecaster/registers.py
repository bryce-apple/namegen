"""Register loaders (brief §3.3).

The term register is the uniqueness control the source validator enforces:
term → defining address.  Matching is case-folded — the corpus capitalises
glossary terms by sentence position ("Ethics" / "ethics").
JSON only; registers are computed artifacts (see derive.py), never typed.
"""

import json

from .errors import SourceError


class TermRegister:
    def __init__(self, mapping: dict):
        self.by_term = {}
        for term, address in mapping.items():
            key = term.casefold()
            if key in self.by_term:
                raise SourceError(
                    "SRC-TERM-DUP",
                    f"term '{term}' assigned twice in register")
            self.by_term[key] = (term, address)

    def address_of(self, phrase: str):
        hit = self.by_term.get(phrase.casefold())
        return hit[1] if hit else None

    def __len__(self):
        return len(self.by_term)


def load_term_register(path) -> TermRegister:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SourceError("SRC-BAD-REGISTER",
                          f"term register {path} is not an object")
    return TermRegister(data)
