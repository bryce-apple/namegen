# Corpus — ground truth for the caster

Place the four sample XML files from the build brief (§0) in this
directory. They are the ground truth for output shape; the build cannot be
verified without them, and implementation of the cast rules is deliberately
paused until they are studied.

| File | Course | Use |
|---|---|---|
| `com295T_xml.xml` | Business Communication | Two-tier chapters, authored labels, video-heavy, alt on all images |
| `2016_*.xml` (Business Ethics) | Business Ethics | One-tier chapters, zero authored labels, tables, partial alt |
| `1761c_*.xml` (Storytelling) | Storytelling | Two-tier, `me:material`, 205 images |
| `1761a_*.xml` | patch stub | Second document type; not a course |

The corpus round-trip test suite will discover any `*.xml` files here
automatically once implemented.
