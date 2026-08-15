# Corpus study — findings that bind the caster

Derived mechanically from the four corpus files (see `corpus/README.md`).
Every cast rule in `cast.py` traces to a row here or to the brief. Items
marked **UNVERIFIED** have no corpus witness and are isolated behind
constants so a future finding changes one line.

## Documents

| File | Root | Shape |
|---|---|---|
| `com295T_xml.xml` | `book` | two-tier: 5 week chapters × nested topic chapters; 33 videos, 0 materials; labels authored |
| `2016.*.xml` (Business Ethics) | `book` | one-tier: 13 chapters; **zero `label` attributes anywhere**; 12 activities |
| `1761c.*.xml` (Storytelling) | `book` | two-tier: 5 weeks × topics; 24 videos **all** paired with `me:material`; 205 images all with `alt` |
| `1761a.*.xml` (patch stub) | `be:patches` | same namespace URI bound to prefix `be:` — validators resolve by URI, never prefix |

## Structure

- `book` children order: `me:option`\*, `title`, (`subtitle`), `bookinfo`, `chapter`\*.
- Two-tier: unit `chapter` → `title`, intro `section`, nested lesson `chapter`s (and in Storytelling a terminal
  practice `section` after the lessons). One-tier (Business Ethics): `chapter` → `title`, `section`\*.
- Intro sections: first section of top-level containers is `label=""` + title `Introduction` (COM, Storytelling).
  Business Ethics authors no label at all and titles them "Introduction to …". `label=""` is the only label we emit.
- Terminal activity sections contain exactly `title` + `me:activity` and are titled per course
  ("Quick Check" in COM/Ethics, "Week N Practice Assignment" in Storytelling) → title comes from the manifest
  entry, default constant.
- Section nesting inside a leaf section goes to depth 3 (so headings `##`–`####` are needed, one more level
  than the brief's table).
- `me:option` placement: `author` (email) and `labeldefault:chapter` on `book`;
  `access="purchase_record"` on every **paid** chapter (first chapter never has it; in COM only topics, not weeks).
- `bookinfo` children: `edition`, `authorgroup` (roles Authors/Contributors/Editors), `copyright`,
  (`epigraph`), `abstract`, `revhistory` (platform-generated; **never emit**).
- `me:paracount` on every chapter and section — platform-generated, never emit.

## Ids and references

- Ids are 5-char lowercase `[a-z][a-z0-9]{4}` — except chapters, which carry human-readable ids
  (`chapter01`, `topic01`, `week1`) that are the `xref` targets. Ours: plan-addressed containers get
  `id = address`; everything else gets the deterministic 5-char hash.
- `xref` is an **empty** element (`linkend` + `id`); display text found in the corpus is authored tail text
  (": Storytelling—Clarity with Charm") — never emit; renderer derives it.
- Corpus xrefs target chapters, sections, figures, and tables. One dangling `linkend="chatper01"` (typo) is live
  in Business Ethics — motivates the source-side address check.

## Confirmed element shapes

- **Objectives**: `sidebar class="topics-to-understand"` → `title` "Learning Objectives" + `orderedlist`
  (para for single sentence). Corpus-confirmed (Business Ethics ×12).
- **Summary**: a `section` titled "Summary" (Storytelling ×12). **Not** a sidebar.
- **Admonitions** (`note` ×6, `important` ×8, `warning` ×1): `title` + paras/lists/figures.
  They carry **no attributes at all** — no id, no class.
- **Figure**: `width="NN%"`, `class="figure-no-box"` (universal), optional `floatstyle="left|right"`, id.
  `title` = caption text + nested credit `para style="font-size:8pt"`. `mediaobject` → `imageobject` →
  `imagedata` (`alt`, `fileref`, `id`, `width`, `depth` in pixels). `informalfigure`: class + id, no title.
- **Video**: `informalfigure class="figure-no-box"` → `mediaobject` → `videoobject` →
  `videodata` (`fileref`=numeric asset id, `width`=450 in all 57 corpus instances, `id`,
  `me:duration`=seconds, `me:name`). Storytelling: every video immediately followed by `me:material` sibling
  (24/24). COM predates materials (0/33) — the pairing rule stands for our output.
- **Platform refs**: empty elements; every corpus activity guid ends `1x2` (26), every material `1x3` (24).
- **Table**: `caption` (first child, when present) + `thead` holding `th` **directly** (no `tr`) +
  `tbody` → `tr` → `th` (row header) + `td`. `informaltable`: `tbody` only, `td` cells.
- **Glossentry**: inside `para`; definition is the **trailing text node** after `glossterm`; the entry's own
  tail continues the sentence. No `<glossary>` element in any course.
- **Inline**: italic = `emphasis` (no role), bold = `emphasis role="bold"`; `ulink target="_blank"`;
  `footnote` holds inline content directly (no para wrapper); blockquote appears both bare and
  para-wrapped — we emit para-wrapped (Business Ethics style).

## Live defects observed (why the rules exist)

- `<emphais>` element (Business Ethics) — motivates the output vocabulary check.
- `targrt="_blank"`, `target="blank"`, `noopener`/`noreferrer` attrs — motivates attribute checks.
- `label="Figrue 9.2"` typo and `label="Figure 3.1"` **on a table** (Storytelling) — motivates never-label.
- `xref linkend="chatper01"` dangling — motivates source-side xref validation.
- Duplicated empty `<epigraph id="lc2nj">` in two different courses — course-copy artifact.

## Not witnessed anywhere (UNVERIFIED cast targets, isolated in constants/functions)

- Equations (no `equation`/`informalequation` in any course).
- Flip cards (per brief §5.10 — `PENDING-CAST`, fails output validation).
- Table `source:` field carrier (we mirror the figure-credit para; no witness).
- Worked-example block carrier (we use a classless titled `sidebar`, the Business Ethics case-study shape).
- Whether platform ingest tolerates `guid="PENDING:…"` (brief §5.6) — token format is one constant.
