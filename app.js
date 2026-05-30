/*
 * app.js — UI wiring and procedural name generation for Namegen.
 *
 * Depends on data.js (LANGUAGES, COUNTRIES, ERAS, GENRES, FLAVOR, ...).
 * All generation is deterministic-free (uses Math.random) and runs locally.
 */

/* ---------- small random helpers ---------- */
const rnd = (n) => Math.floor(Math.random() * n);
const pick = (arr) => arr[rnd(arr.length)];
const chance = (p) => Math.random() < p;
const randInt = (min, max) => min + rnd(max - min + 1);
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);

/* ---------- word assembly ---------- */

// Build a single pronounceable word from a language's phoneme pools.
function buildWord(lang, [minSyl, maxSyl]) {
  const syllables = randInt(minSyl, maxSyl);
  let word = "";
  for (let i = 0; i < syllables; i++) {
    const onset = pick(lang.onsets);
    const nucleus = pick(lang.nuclei);
    // Codas are more likely on the final syllable, sparse elsewhere.
    const wantCoda = i === syllables - 1 ? chance(0.6) : chance(0.25);
    const coda = wantCoda ? pick(lang.codas) : "";
    word += onset + nucleus + coda;
  }
  // Tidy up: collapse any accidental triple letters.
  word = word.replace(/(.)\1\1+/g, "$1$1");
  return cap(word);
}

// Build a surname using language-specific prefixes/suffixes when present.
function buildSurname(lang) {
  let base = buildWord(lang, lang.surnameSyllables);

  if (lang.surnameSuffixes && lang.surnameSuffixes.length && chance(0.7)) {
    base += pick(lang.surnameSuffixes);
  }
  if (lang.surnamePrefixes && lang.surnamePrefixes.length && chance(0.5)) {
    base = pick(lang.surnamePrefixes) + cap(base);
  }
  return cap(base);
}

// Optional sci-fi designation like "VX-7" or "Unit 23".
function buildDesignation() {
  const prefix = pick(SCIFI_DESIGNATIONS.prefixes);
  const sep = pick(SCIFI_DESIGNATIONS.separators);
  const num = chance(0.5) ? randInt(1, 99) : randInt(100, 999);
  return `${prefix}${sep}${num}`;
}

/* ---------- full name generation ---------- */

function resolveLanguage(languageKey, countryKey) {
  // Explicit language wins; otherwise fall back to the country's default.
  if (languageKey && languageKey !== "any") return languageKey;
  if (countryKey && countryKey !== "any" && COUNTRIES[countryKey]) {
    return COUNTRIES[countryKey];
  }
  return pick(Object.keys(LANGUAGES));
}

// Pick a country whose default language matches, so metadata stays coherent.
function countryForLanguage(langKey) {
  const matches = Object.keys(COUNTRIES).filter((c) => COUNTRIES[c] === langKey);
  return matches.length ? pick(matches) : "—";
}

// Generate one character entry from resolved parameters.
function generateOne(params) {
  const langKey = resolveLanguage(params.language, params.country);
  const lang = LANGUAGES[langKey];
  const country =
    params.country !== "any" ? params.country : countryForLanguage(langKey);
  const era = params.era === "any" ? pick(ERAS) : params.era;
  const genre = params.genre === "any" ? pick(GENRES) : params.genre;

  const given = buildWord(lang, lang.givenSyllables);
  const surname = buildSurname(lang);
  let fullName = `${given} ${surname}`;

  const flavor = FLAVOR[genre][era];

  // Sci-fi designation (callsign / unit ID).
  if (flavor.designationChance && chance(flavor.designationChance)) {
    fullName += ` ${buildDesignation()}`;
  }

  // Epithet / title for both genres.
  if (flavor.epithetChance && chance(flavor.epithetChance)) {
    fullName += `, ${pick(flavor.epithets)}`;
  }

  return {
    name: fullName,
    given,
    surname,
    country,
    language: lang.label,
    era,
    genre: genre === "scifi" ? "Sci-Fi" : "Fantasy",
  };
}

/* ---------- DOM wiring ---------- */

const els = {};
let lastResults = [];

function populateSelects() {
  // Country dropdown.
  const country = els.country;
  country.appendChild(makeOption("any", "Any (random)"));
  Object.keys(COUNTRIES)
    .sort()
    .forEach((c) => country.appendChild(makeOption(c, c)));

  // Language dropdown.
  const language = els.language;
  language.appendChild(makeOption("any", "Any (random)"));
  Object.entries(LANGUAGES).forEach(([key, def]) =>
    language.appendChild(makeOption(key, def.label))
  );
}

function makeOption(value, label) {
  const opt = document.createElement("option");
  opt.value = value;
  opt.textContent = label;
  return opt;
}

function readParams() {
  if (els.randomAll.checked) {
    return { country: "any", language: "any", era: "any", genre: "any" };
  }
  return {
    country: els.country.value,
    language: els.language.value,
    era: els.era.value,
    genre: els.genre.value,
  };
}

function render(results) {
  const list = els.results;
  list.innerHTML = "";
  results.forEach((r) => {
    const li = document.createElement("li");
    li.className = "result";

    const name = document.createElement("span");
    name.className = "result__name";
    name.textContent = r.name;

    const meta = document.createElement("span");
    meta.className = "result__meta";
    meta.textContent = `${r.country} · ${r.language} · ${cap(r.era)} · ${r.genre}`;

    const copy = document.createElement("button");
    copy.className = "result__copy";
    copy.type = "button";
    copy.title = "Copy name";
    copy.textContent = "Copy";
    copy.addEventListener("click", () => copyText(r.name, copy));

    const text = document.createElement("div");
    text.className = "result__text";
    text.appendChild(name);
    text.appendChild(meta);

    li.appendChild(text);
    li.appendChild(copy);
    list.appendChild(li);
  });

  els.emptyState.style.display = results.length ? "none" : "";
  els.copyAll.disabled = results.length === 0;
}

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    const original = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => (btn.textContent = original), 1200);
  } catch {
    // Clipboard API unavailable (e.g. file:// in some browsers) — ignore quietly.
  }
}

function handleGenerate() {
  const params = readParams();
  let count = parseInt(els.count.value, 10);
  if (!Number.isFinite(count)) count = 8;
  count = Math.min(50, Math.max(1, count));
  els.count.value = count;

  lastResults = Array.from({ length: count }, () => generateOne(params));
  render(lastResults);
}

function handleCopyAll() {
  if (!lastResults.length) return;
  copyText(lastResults.map((r) => r.name).join("\n"), els.copyAll);
}

function init() {
  [
    "country", "language", "era", "genre", "count",
    "randomAll", "generate", "copyAll", "results", "emptyState",
  ].forEach((id) => (els[id] = document.getElementById(id)));

  populateSelects();

  els.generate.addEventListener("click", handleGenerate);
  els.copyAll.addEventListener("click", handleCopyAll);

  // Disable parameter fields when "completely random" is on.
  els.randomAll.addEventListener("change", () => {
    const disabled = els.randomAll.checked;
    ["country", "language", "era", "genre"].forEach(
      (id) => (els[id].disabled = disabled)
    );
  });

  // Generate an initial batch so the page is not empty.
  handleGenerate();
}

document.addEventListener("DOMContentLoaded", init);
