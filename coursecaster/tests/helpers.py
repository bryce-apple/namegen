"""Shared fixtures: a small course exercising every construct."""

from coursecaster.mdparse import parse_text
from coursecaster.plan import load_plan_data

PLAN_DATA = {
    "slug": "PFMA",
    "title": "Financial Statement Analysis",
    "author": "author@example.com",
    "labeldefault_chapter": "Unit {chapter-index}",
    "bookinfo": {
        "edition": "1",
        "copyright": {"year": 2026, "holder": "MyEducator"},
        "abstract": "A course.",
    },
    "units": [
        {
            "address": "PFMA-U01",
            "title": "The Accounting Cycle",
            "competency_statement": "The graduate identifies things.",
            "competency_zone": "theirs",
            "subsections": ["PFMA-U01-S0"],
            "lessons": [
                {
                    "address": "PFMA-U01-L1",
                    "title": "Accounting Information",
                    "access": "purchase_record",
                    "subsections": ["PFMA-U01-L1-S0", "PFMA-U01-L1-S1"],
                },
            ],
        },
    ],
    "manifest": [
        {"address": "PFMA-U01-QZ", "kind": "activity", "status": "resolved",
         "owner": "platform", "guid": "g2ec4e2b6b5a20001x2"},
        {"address": "PFMA-U01-L1-QZ", "kind": "activity",
         "status": "specified", "owner": "platform"},
        {"address": "PFMA-U01-L1-S1-F1", "kind": "figure",
         "status": "specified", "owner": "pipeline"},
        {"address": "PFMA-U01-L1-S1-V1", "kind": "video",
         "status": "specified", "owner": "pipeline"},
        {"address": "PFMA-U01-L1-S1-A1", "kind": "activity",
         "status": "proposed", "owner": "unassigned"},
    ],
}

INTRO_U = """\
---
address: PFMA-U01-S0
title: Introduction
---

Welcome to the unit.
"""

INTRO_L = """\
---
address: PFMA-U01-L1-S0
title: Introduction
---

Welcome to the lesson.
"""

CONTENT = """\
---
address: PFMA-U01-L1-S1
title: Details of the Financial Statements
serves: [C1-S1]
obligation: spine
instances: [PCME-1.2.1]
terms_first_use: [classified balance sheet]
---

:::objective zone=theirs
- Understand the balance sheet.
- Interpret comparative statements.
:::

A {{term:classified balance sheet|A balance sheet grouped into classes.}} \
organizes accounts. See {{xref:PFMA-U01-L1-S1-F1}} with **bold** and \
*italic* care.[^1]

## Reading the Statement

Detail with a [link](https://example.com/ref).

> Quoted wisdom about statements.

| Statement | Purpose |
| --- | --- |
| Balance sheet | Position |

:::figure formal=true status=specified owner=pipeline address=PFMA-U01-L1-S1-F1
title: A classified balance sheet.
alt: A balance sheet with sections highlighted.
brief: Diagram the classification.
:::

:::video status=specified owner=pipeline address=PFMA-U01-L1-S1-V1
title: Statements overview
target_duration: 90
brief: Walk through the statements.
material_brief: Reading guide.
:::

:::activity status=proposed owner=unassigned address=PFMA-U01-L1-S1-A1
:::

:::note title="Why it matters"
Analysts compare items.

:::figure formal=false src=images/ratio.png width=1280 depth=720
alt: A ratio calculation.
:::
:::

:::table
caption: A comparison of statements.
source: Adapted from worksheet C1.

| | Timing |
| --- | --- |
| Balance sheet | Point in time |
:::

:::equation
E = mc^2
:::

:::example company=Acme statement=balance-sheet period=FY2025
title: Acme's classified balance sheet
Acme groups current assets first.
:::

:::summary
The statements interlock.
:::

[^1]: Author, A. (2026). *Statements*. MyEducator.
"""

SOURCE_TEXTS = {
    "PFMA-U01-S0": INTRO_U,
    "PFMA-U01-L1-S0": INTRO_L,
    "PFMA-U01-L1-S1": CONTENT,
}


def sample_plan():
    return load_plan_data({k: v for k, v in PLAN_DATA.items()})


def sample_sources(overrides=None):
    texts = dict(SOURCE_TEXTS)
    if overrides:
        texts.update(overrides)
    return {addr: parse_text(text, addr + ".md")
            for addr, text in texts.items()}
