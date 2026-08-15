"""Error types.  Every failure is fatal and precise (brief §6, §10)."""


class CasterError(Exception):
    """Base for all pipeline failures."""

    def __init__(self, code: str, message: str, *, address: str = None,
                 path: str = None, line: int = None):
        self.code = code
        self.address = address
        self.path = path
        self.line = line
        loc = []
        if path:
            loc.append(str(path))
        if line is not None:
            loc.append(f"line {line}")
        if address:
            loc.append(f"address {address}")
        prefix = f"[{code}]"
        if loc:
            prefix += " " + ", ".join(loc) + ":"
        super().__init__(f"{prefix} {message}")
        self.bare_message = message


class SourceError(CasterError):
    """A markdown source or register defect (source validator)."""


class PlanError(CasterError):
    """A course-plan defect."""


class CastError(CasterError):
    """The caster met a construct it refuses to guess about."""


class OutputError(CasterError):
    """Built XML failed post-build validation."""


class ErrorCollector:
    """Collects errors so a validation run reports everything at once,
    then fails.  Every collected error is still fatal to the build."""

    def __init__(self):
        self.errors = []

    def add(self, err: CasterError):
        self.errors.append(err)

    def error(self, cls, code, message, **kw):
        self.add(cls(code, message, **kw))

    @property
    def ok(self):
        return not self.errors

    def raise_if_any(self):
        if self.errors:
            summary = "\n".join(str(e) for e in self.errors)
            raise CasterError(
                "VALIDATION-FAILED",
                f"{len(self.errors)} fatal finding(s):\n{summary}",
            )
