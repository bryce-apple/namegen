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

/* ---------- physical description ---------- */

const buildArticle = (word) => (/^[aeiou]/i.test(word) ? "An" : "A");

// Join a short list naturally: ["a","b"] -> "a and b".
function joinList(items) {
  if (items.length <= 1) return items.join("");
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`;
}

// Merge a species profile (if any) over the default descriptor pools.
function resolveProfile(langKey) {
  const p = SPECIES_PROFILES[langKey] || {};
  return {
    genders: p.genders || DESCRIPTORS.genders,
    ages: p.ages || DESCRIPTORS.ages,
    heights: p.heights || DESCRIPTORS.heights,
    builds: p.builds || DESCRIPTORS.builds,
    hairColors: p.hairColors || DESCRIPTORS.hairColors,
    hairStyles: p.hairStyles || DESCRIPTORS.hairStyles,
    eyeColors: p.eyeColors || DESCRIPTORS.eyeColors,
    skinTones: p.skinTones || DESCRIPTORS.skinTones,
    skinNoun: p.skinNoun || "skin",
    eyeNoun: p.eyeNoun || "eyes",
    hairless: !!p.hairless,
    humanlike: p.humanlike !== false,
    signatureFeature: p.signatureFeature || null,
    signatureChance: p.signatureChance || 0,
  };
}

// Build a basic physical description, species-aware and grammar-safe.
function describe(langKey, genre) {
  const P = resolveProfile(langKey);
  const gender = pick(P.genders);
  const age = pick(P.ages);
  const height = pick(P.heights);
  const build = pick(P.builds);

  let hairColor = pick(P.hairColors);
  if (!P.hairless && OLDER_AGES.includes(age) && chance(0.6)) {
    hairColor = pick(GREY_HAIRS);
  }
  const hairStyle = pick(P.hairStyles);
  const eyeColor = pick(P.eyeColors);
  const skinTone = pick(P.skinTones);

  // At most one understated distinguishing feature.
  let feature = "";
  if (P.signatureFeature && chance(P.signatureChance)) {
    feature = P.signatureFeature;
  } else if (P.humanlike && gender === "man" && !P.hairless && chance(0.35)) {
    feature = pick(MASC_FEATURES);
  } else if (P.humanlike && chance(0.4)) {
    feature = pick(DESCRIPTORS.features);
  }
  if (!feature && genre === "scifi" && chance(0.15)) {
    feature = "a small cybernetic implant at one temple";
  }

  const hair = P.hairless ? "" : `${hairStyle} ${hairColor}`;
  const eyes = `${eyeColor} ${P.eyeNoun}`;
  const skin = `${skinTone} ${P.skinNoun}`;

  // Sentence 1: who they are. Sentence 2: colouring + optional feature.
  const s1 = `${buildArticle(build)} ${build} ${gender}, ${age}, ${height}.`;
  const traits = [];
  if (hair) traits.push(`${hair} hair`);
  traits.push(eyes);
  let s2 = `They have ${joinList(traits)}, with ${skin}`;
  s2 += feature ? `, and ${feature}.` : ".";

  return {
    summary: `${s1} ${s2}`,
    gender, age, height, build, hair, eyes, skin, feature,
  };
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
    description: params.describe ? describe(langKey, genre) : null,
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
  const describe = els.describe.checked;
  if (els.randomAll.checked) {
    return { country: "any", language: "any", era: "any", genre: "any", describe };
  }
  return {
    country: els.country.value,
    language: els.language.value,
    era: els.era.value,
    genre: els.genre.value,
    describe,
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
    if (r.description) {
      const desc = document.createElement("span");
      desc.className = "result__desc";
      desc.textContent = r.description.summary;
      text.appendChild(desc);
    }
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
    "randomAll", "describe", "generate", "copyAll", "results", "emptyState",
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
