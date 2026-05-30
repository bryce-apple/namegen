/*
 * data.js — name-generation data for Namegen.
 *
 * Everything is plain data so it is easy to read and extend:
 *   - LANGUAGES: phoneme building blocks per language family.
 *   - COUNTRIES: maps a country to its default language.
 *   - ERAS / GENRES: flavor layers (titles, suffixes, designations).
 *
 * A "language" describes how to assemble a syllable. Words are built from
 * syllables of the form  onset + nucleus + coda  where onset/coda may be
 * empty (an empty string "" is included in the pools to allow that).
 */

const LANGUAGES = {
  common: {
    label: "Common (English-like)",
    onsets: ["", "b", "br", "c", "cr", "d", "dr", "f", "fr", "g", "gr", "h", "j", "k", "l", "m", "n", "p", "pr", "r", "s", "sh", "st", "t", "th", "tr", "v", "w"],
    nuclei: ["a", "e", "i", "o", "u", "ai", "ea", "ee", "ou", "y"],
    codas: ["", "", "n", "r", "l", "s", "th", "rd", "n", "ld", "m", "k"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["ton", "well", "field", "wood", "ford", "ley", "worth", "more", "ridge"],
  },
  japanese: {
    label: "Japanese",
    onsets: ["", "k", "s", "t", "n", "h", "m", "y", "r", "w", "g", "z", "d", "b", "p", "ch", "sh", "ts", "ky", "ry", "ny"],
    nuclei: ["a", "i", "u", "e", "o", "a", "o"],
    codas: ["", "", "", "n"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["moto", "yama", "kawa", "da", "shi", "naga", "saki", "bara"],
  },
  slavic: {
    label: "Slavic (Russian-like)",
    onsets: ["", "b", "v", "g", "d", "zh", "z", "k", "l", "m", "n", "p", "r", "s", "t", "f", "kh", "sl", "st", "vl", "gr", "dr", "pr"],
    nuclei: ["a", "e", "i", "o", "u", "y", "ya", "ye"],
    codas: ["", "", "v", "n", "r", "k", "sk", "l", "m"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["ov", "ev", "in", "sky", "ova", "enko", "vich"],
  },
  arabic: {
    label: "Arabic",
    onsets: ["", "b", "t", "th", "j", "h", "kh", "d", "r", "z", "s", "sh", "f", "q", "k", "l", "m", "n", "w", "y", "gh"],
    nuclei: ["a", "i", "u", "aa", "ee", "ai", "a", "i"],
    codas: ["", "", "n", "r", "m", "d", "l", "f", "z"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["i", "ani", "awi", "uri", "iyya"],
  },
  norse: {
    label: "Norse (Scandinavian)",
    onsets: ["", "b", "bj", "br", "d", "f", "fr", "g", "gr", "h", "hr", "k", "kn", "l", "m", "n", "r", "s", "sk", "st", "sv", "t", "th", "v"],
    nuclei: ["a", "e", "i", "o", "u", "au", "ei", "ja", "o"],
    codas: ["", "", "n", "r", "rd", "ld", "lf", "k", "ng", "th"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 2],
    surnameSuffixes: ["son", "sson", "dottir", "gard", "vik", "stad"],
  },
  greek: {
    label: "Greek",
    onsets: ["", "d", "th", "k", "kr", "l", "m", "n", "p", "ph", "pr", "r", "s", "st", "t", "ch", "x", "z"],
    nuclei: ["a", "e", "i", "o", "u", "ia", "eo", "ou"],
    codas: ["", "", "n", "s", "r", "kl", "th", "x"],
    givenSyllables: [2, 3],
    surnameSyllables: [3, 4],
    surnameSuffixes: ["opoulos", "idis", "akis", "iadis", "os", "atos"],
  },
  romance: {
    label: "Romance (Latin/Spanish/Italian)",
    onsets: ["", "b", "c", "d", "f", "g", "l", "m", "n", "p", "r", "s", "t", "v", "br", "cr", "gr", "tr", "fl", "gl"],
    nuclei: ["a", "e", "i", "o", "u", "ia", "io", "ue", "a", "o"],
    codas: ["", "", "n", "r", "l", "s", "nt"],
    givenSyllables: [2, 3],
    surnameSyllables: [3, 3],
    surnameSuffixes: ["ez", "ino", "elli", "ardo", "ano", "ucci", "on"],
  },
  sanskrit: {
    label: "Sanskrit (Indian)",
    onsets: ["", "b", "bh", "ch", "d", "dh", "g", "h", "j", "k", "kr", "l", "m", "n", "p", "pr", "r", "s", "sh", "t", "v", "y"],
    nuclei: ["a", "i", "u", "aa", "ee", "ai", "a", "i", "u"],
    codas: ["", "", "n", "m", "r", "sh", "th"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["an", "esh", "raj", "veer", "endra", "ali"],
  },
  sinitic: {
    label: "Sinitic (Chinese-like)",
    onsets: ["", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x", "zh", "ch", "sh", "r", "z", "c", "s", "y", "w"],
    nuclei: ["a", "e", "i", "o", "u", "ai", "ao", "ei", "ou", "ia", "uo"],
    codas: ["", "", "n", "ng"],
    givenSyllables: [1, 2],
    surnameSyllables: [1, 1],
    surnameSuffixes: [],
  },
  bantu: {
    label: "Bantu (Swahili-like)",
    onsets: ["", "m", "mw", "n", "nd", "ng", "nj", "b", "d", "f", "g", "j", "k", "l", "p", "s", "t", "w", "z", "ch"],
    nuclei: ["a", "e", "i", "o", "u", "a", "o"],
    codas: ["", "", "", "n"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["a", "o", "we", "ni"],
  },
  celtic: {
    label: "Celtic (Gaelic-like)",
    onsets: ["", "b", "br", "c", "cr", "d", "f", "g", "l", "m", "n", "r", "s", "t", "bh", "mh", "ch", "gl", "fl"],
    nuclei: ["a", "e", "i", "o", "u", "ai", "ae", "ei", "io", "ea"],
    codas: ["", "", "n", "r", "ll", "gh", "dh", "nn", "rt"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnamePrefixes: ["Mac", "O'", "Mc"],
    surnameSuffixes: ["an", "ach", "aidh", "gan"],
  },
  elvish: {
    label: "Elvish (high-fantasy)",
    onsets: ["", "c", "d", "f", "g", "l", "m", "n", "r", "s", "t", "th", "v", "el", "gal", "cel", "thal"],
    nuclei: ["a", "e", "i", "o", "ae", "ia", "ie", "ea", "io"],
    codas: ["", "", "l", "n", "r", "th", "s", "el", "wen", "dil"],
    givenSyllables: [2, 4],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["wen", "dil", "ion", "las", "riel", "mir"],
  },
};

// Country -> default language. "Any" is handled in app.js.
const COUNTRIES = {
  "United States": "common",
  "United Kingdom": "common",
  "Ireland": "celtic",
  "Scotland": "celtic",
  "Wales": "celtic",
  "Japan": "japanese",
  "China": "sinitic",
  "Russia": "slavic",
  "Poland": "slavic",
  "Ukraine": "slavic",
  "Saudi Arabia": "arabic",
  "Egypt": "arabic",
  "Morocco": "arabic",
  "Norway": "norse",
  "Sweden": "norse",
  "Iceland": "norse",
  "Denmark": "norse",
  "Greece": "greek",
  "Italy": "romance",
  "Spain": "romance",
  "France": "romance",
  "Portugal": "romance",
  "India": "sanskrit",
  "Nepal": "sanskrit",
  "Kenya": "bantu",
  "Tanzania": "bantu",
  "Nigeria": "bantu",
};

/*
 * Flavor layers. Each genre+era combination contributes optional titles,
 * epithets, or designations that are appended to the assembled name.
 */
const ERAS = ["archaic", "current", "futuristic"];
const GENRES = ["fantasy", "scifi"];

const FLAVOR = {
  fantasy: {
    archaic: {
      // chance (0-1) of adding an epithet, and the pool to draw from
      epithetChance: 0.6,
      epithets: [
        "the Elder", "the Wise", "the Old", "the Grey", "the Sigh of Dawn",
        "of the Hollow Vale", "of the Ashen Crown", "the Unbroken",
        "the Lorekeeper", "of the First Flame", "the Twiceborn",
      ],
    },
    current: {
      epithetChance: 0.25,
      epithets: [
        "the Wanderer", "the Bold", "Hedgewise", "of the Low Road",
        "the Quiet", "Stormtouched", "the Free", "of the Riverfolk",
      ],
    },
    futuristic: {
      epithetChance: 0.4,
      epithets: [
        "of the Spire", "the Aetherborn", "Voidwarden", "of the Glass Citadel",
        "the Last Mage", "Starbound", "of the Sunken Arcology",
      ],
    },
  },
  scifi: {
    archaic: {
      // "archaic" sci-fi = early colonial / retro-future flavor
      epithetChance: 0.45,
      epithets: [
        "the Pioneer", "of the First Wave", "Colonist", "of Old Terra",
        "the Surveyor", "of the Frontier Fleet",
      ],
      designationChance: 0.3,
    },
    current: {
      epithetChance: 0.2,
      epithets: [
        "the Pilot", "of the Orbital Guard", "Specialist", "the Operator",
        "of Deep Station", "the Engineer",
      ],
      designationChance: 0.4,
    },
    futuristic: {
      epithetChance: 0.3,
      epithets: [
        "of the Hegemony", "Synthborn", "Voidwalker", "of the Outer Reach",
        "the Augmented", "of the Helix Collective", "Quantum-rated",
      ],
      designationChance: 0.75,
    },
  },
};

// Designation tokens for sci-fi callsigns / unit IDs (e.g. "VX-7", "Unit 23").
const SCIFI_DESIGNATIONS = {
  prefixes: ["VX", "KR", "ZeroOne", "Helix", "Nyx", "Unit", "Strain", "Mk", "Echo", "Tau"],
  separators: ["-", "-", " ", "/"],
};
