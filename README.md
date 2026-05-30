# Namegen

A simple browser app that generates character names for fictional universes —
either completely at random or based on parameters you choose.

## Parameters

- **Country of origin** — e.g. Japan, Norway, Kenya (or *Any*)
- **Language of origin** — the phoneme family used to build the name (or *Any*)
- **Era** — Archaic, Current, or Futuristic
- **Genre** — Fantasy or Sci-Fi

Each parameter has an **Any (random)** option, so you can pin some and randomize
the rest. The **🎲 Completely random** checkbox ignores all parameters and
randomizes everything per name.

## How it works

Generation is fully **procedural and offline** — no network calls and no API
keys. Names are assembled from per-language phoneme pools (`onset + nucleus +
coda` syllables), then flavored by era and genre with titles, epithets, or
sci-fi designations (e.g. `VX-7`).

## Running it

It's a static site — just open `index.html` in a browser. For clipboard
features to work in all browsers, serve it locally instead:

```sh
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Project layout

- `index.html` — markup and controls
- `style.css` — styling
- `data.js` — languages, country→language mappings, and era/genre flavor data
- `app.js` — generation logic and UI wiring

## Extending

Add a new language by adding an entry to `LANGUAGES` in `data.js` (define
`onsets`, `nuclei`, `codas`, syllable ranges, and optional surname affixes).
Map countries to it in `COUNTRIES`.

## Roadmap

- Export a spreadsheet (CSV/XLSX) of generated names with their attributes.
