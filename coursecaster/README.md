# MyEducator Course Caster

Annotated markdown → MyEducator course XML, per the build brief.

**Markdown is the source. XML is a build artifact. The XML is never
hand-edited.** The caster never infers: every construct is explicitly
annotated or derives mechanically from position; everything else fails
loudly with a precise error.

Python 3, stdlib + PyYAML. No network at runtime. Deterministic:
identical input produces byte-identical output.

## Layout

| Path | Deliverable |
|---|---|
| `coursecaster/cast.py` | 1 — caster |
| `coursecaster/source_validator.py` | 2 — source validator (§6, all fatal) |
| `coursecaster/output_validator.py` | 3 — output validator (§7, incl. round-trip counts) |
| `coursecaster/derive.py` | 4 — coverage matrix, term register, reference manifest, example ledger |
| `coursecaster/seed.py` | 5 — seed generator |
| `tests/` | 6 — test suite, incl. corpus round-trip |
| `coursecaster/uncast.py`, `corpuscmp.py` | corpus round-trip harness (test-only) |
| `STUDY.md` | corpus study — every cast rule traces here or to the brief |
| `corpus/` | the four ground-truth samples (§0) |

## Usage

```sh
python3 -m coursecaster seed            plan.yaml sources/
python3 -m coursecaster validate-source plan.yaml sources/ --terms terms.json
python3 -m coursecaster cast            plan.yaml sources/ -o book.xml
python3 -m coursecaster validate-output book.xml --plan plan.yaml --srcdir sources/
python3 -m coursecaster derive terms|coverage|references|examples plan.yaml sources/
```

`cast` runs the source validator first, writes `book.xml` +
`book.xml.report.json` (passthrough report, tokens, pending casts, example
ledger facts), then runs the output validator. Exit codes: 0 ok ·
2 validation failed · 3 build incomplete (`PENDING-CAST` present).

Tests: `python3 -m unittest discover` from this directory. The corpus
round-trip tests skip loudly if `corpus/` lacks the samples.

## Conventions beyond the brief (all mechanical, none inferred)

- **Addresses as ids.** Plan-addressed containers/subsections get
  `id = address` (the corpus uses readable chapter ids as xref targets);
  every other element gets a deterministic 5-char hash of
  (course, address-scope, tag, ordinal) — rebuilds are byte-identical and
  edits to one subsection don't churn ids elsewhere.
- **`*-S0`** names a container's introduction subsection (cast with
  `label=""`, the one label ever emitted); **`*-QZ`** names its terminal
  activity in the manifest (cast last, title from the manifest entry,
  default "Quick Check").
- **Reference blocks carry `address=`** binding them to their manifest
  entry; required whenever status ≠ resolved (the PENDING token needs an
  address). `:::table` takes an optional `address=` to be an xref target.
- **Headings `##`–`####`** nest sections three deep — the corpus nests one
  level deeper than the brief's table (see STUDY.md).
- **`:::example`** (attrs `company= statement= period=`) carries the
  example-ledger facts of §8, which the §4.2 vocabulary otherwise leaves
  with no source.
- A subsection needs both an objective **and** a summary (§6); `*-S0`
  intro files are exempt (corpus intros are welcome paragraphs).

## Corpus-unverified cast targets

Isolated behind constants/functions so one finding changes one line:

- `PENDING:` **token carrier** (§5.6 ⚠): `constants.PENDING_TOKEN_FORMAT`;
  cast logic only calls `pending_token()`/`parse_pending_token()`.
- **Flip cards** (§5.10): no cast target exists. `cast._cast_flipcard`
  emits a `PENDING-CAST` marker; output validation fails while any exist.
- **Equations**: no corpus witness; `informalequation`/`alt` per
  `constants.EQUATION_ALT_ROLE`.
- **Table `source:`** carrier mirrors the figure-credit para; no witness.
- **`:::example`** casts to a classless titled sidebar (the Business
  Ethics case-study shape).

## Corpus round-trip

`tests/test_corpus_roundtrip.py` uncasts each corpus book to an equivalent
annotated source + plan, recasts, and compares element trees ignoring ids
and `me:paracount` plus the explicit normalization rules in
`corpuscmp.py` (authored labels, styling attrs, live defects, markdown's
inability to express content at parent level after a nested section).
Constructs the source vocabulary cannot express ride through as `:::xml`
passthrough — visible in the passthrough report, never silently dropped.
All three books currently match:

| Book | Result | Passthrough blocks |
|---|---|---|
| Business Ethics (no-labels case) | match | 151 |
| Storytelling (material-pairing case) | match | 158 |
| COM 295T (two-tier case) | match | 62 (incl. 33 pre-pairing videos) |
