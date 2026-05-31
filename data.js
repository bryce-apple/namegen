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

  /* ----- more real-world families ----- */

  korean: {
    label: "Korean",
    onsets: ["", "g", "n", "d", "r", "m", "b", "s", "j", "ch", "k", "t", "p", "h", "gw", "hw"],
    nuclei: ["a", "e", "i", "o", "u", "eo", "ae", "ya", "yo", "eu", "wa"],
    codas: ["", "", "n", "ng", "k", "l", "m", "p"],
    givenSyllables: [2, 2],
    surnameSyllables: [1, 1],
    surnameSuffixes: [],
  },
  turkic: {
    label: "Turkic (Turkish/Central Asian)",
    onsets: ["", "b", "c", "d", "g", "h", "k", "l", "m", "n", "p", "r", "s", "sh", "t", "v", "y", "z"],
    nuclei: ["a", "e", "i", "o", "u", "ai", "ay", "ya"],
    codas: ["", "", "n", "r", "k", "l", "m", "z", "t"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["oglu", "kan", "demir", "han", "bek"],
  },
  finnic: {
    label: "Finnic (Finnish/Estonian)",
    onsets: ["", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v"],
    nuclei: ["a", "e", "i", "o", "u", "y", "aa", "ee", "ii", "uo", "ie"],
    codas: ["", "", "n", "s", "t", "r", "l", "kk", "ll"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["nen", "la", "inen", "maki", "virta"],
  },
  hebraic: {
    label: "Hebraic (Hebrew)",
    onsets: ["", "b", "g", "d", "h", "v", "z", "ch", "t", "y", "k", "l", "m", "n", "s", "sh", "r", "tz"],
    nuclei: ["a", "e", "i", "o", "u", "ai", "ei"],
    codas: ["", "", "l", "n", "m", "r", "ch", "v", "t"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["el", "iah", "on", "it", "ai"],
  },
  germanic: {
    label: "Germanic (German/Dutch)",
    onsets: ["", "b", "br", "d", "f", "fr", "g", "gr", "h", "k", "kl", "l", "m", "n", "p", "r", "s", "sch", "st", "t", "v", "w", "z", "sp"],
    nuclei: ["a", "e", "i", "o", "u", "au", "ei", "ie", "eu"],
    codas: ["", "", "n", "r", "t", "ch", "ng", "lz", "rg", "nn"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["mann", "berg", "stein", "feld", "hardt", "bach"],
  },
  persian: {
    label: "Persian (Farsi)",
    onsets: ["", "b", "p", "t", "d", "j", "ch", "kh", "r", "z", "zh", "s", "sh", "gh", "f", "q", "k", "g", "l", "m", "n", "h", "v", "y"],
    nuclei: ["a", "e", "i", "o", "u", "aa", "ee", "ou"],
    codas: ["", "", "n", "r", "sh", "m", "d", "z"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["i", "zadeh", "pour", "yan", "far"],
  },
  thai: {
    label: "Thai (Southeast Asian)",
    onsets: ["", "b", "p", "ph", "t", "th", "d", "k", "kh", "ng", "ch", "s", "n", "m", "r", "l", "w", "y", "j"],
    nuclei: ["a", "e", "i", "o", "u", "ai", "ao", "ua", "ia", "ae"],
    codas: ["", "", "n", "ng", "m", "t", "k", "p"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 4],
    surnameSuffixes: ["chai", "porn", "wong", "sak", "kul"],
  },
  polynesian: {
    label: "Polynesian (Hawaiian/Maori)",
    onsets: ["", "h", "k", "l", "m", "n", "p", "w", "t", "r", "ng"],
    nuclei: ["a", "e", "i", "o", "u", "a", "i", "u", "ai", "au", "oa"],
    codas: [""],
    givenSyllables: [3, 4],
    surnameSyllables: [2, 3],
    surnameSuffixes: [],
  },
  mongolic: {
    label: "Mongolic",
    onsets: ["", "b", "g", "d", "j", "z", "kh", "m", "n", "l", "r", "s", "sh", "t", "ts", "ch"],
    nuclei: ["a", "e", "i", "o", "u", "uu", "aa", "oo"],
    codas: ["", "", "n", "g", "r", "l", "kh", "ts"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["bold", "baatar", "khan", "jin", "suren"],
  },
  vietnamese: {
    label: "Vietnamese",
    onsets: ["", "b", "c", "d", "g", "h", "k", "l", "m", "n", "ng", "nh", "p", "ph", "q", "r", "s", "t", "th", "tr", "v", "x"],
    nuclei: ["a", "e", "i", "o", "u", "y", "ai", "ao", "oa", "uy", "ie"],
    codas: ["", "", "n", "ng", "nh", "c", "t", "p", "m"],
    givenSyllables: [1, 2],
    surnameSyllables: [1, 1],
    surnameSuffixes: [],
  },
  nahuatl: {
    label: "Nahuatl (Mesoamerican)",
    onsets: ["", "tl", "tz", "ch", "x", "m", "n", "p", "t", "k", "c", "hu", "qu", "l", "y", "z"],
    nuclei: ["a", "e", "i", "o", "a", "i"],
    codas: ["", "", "tl", "tz", "n", "l", "x", "c"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["tzin", "tl", "atl", "cotl"],
  },
  quechua: {
    label: "Quechua (Andean)",
    onsets: ["", "p", "t", "k", "q", "ch", "s", "h", "m", "n", "l", "ll", "r", "w", "y"],
    nuclei: ["a", "i", "u", "ay", "aw"],
    codas: ["", "", "n", "q", "s", "r", "y"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["mama", "yupanqui", "huaman", "quispe"],
  },
  inuit: {
    label: "Inuit (Arctic)",
    onsets: ["", "k", "q", "t", "n", "m", "p", "s", "l", "g", "v", "j", "ng"],
    nuclei: ["a", "i", "u", "aa", "ii", "uu"],
    codas: ["", "", "k", "q", "t", "n", "ng", "p"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["nuk", "tuq", "lik", "ssuk"],
  },

  /* ----- fantasy races ----- */

  dwarvish: {
    label: "Dwarvish (fantasy)",
    onsets: ["", "b", "br", "d", "dr", "g", "gr", "k", "kr", "th", "t", "tr", "v", "z", "n", "m", "r"],
    nuclei: ["a", "o", "u", "i", "ai", "ou"],
    codas: ["", "", "r", "n", "k", "m", "in", "ur", "ar", "im", "grim", "ek"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 2],
    surnameSuffixes: ["beard", "forge", "hammer", "stone", "axe", "delve"],
  },
  orcish: {
    label: "Orcish (fantasy)",
    onsets: ["", "g", "gr", "k", "kr", "m", "n", "r", "sh", "th", "z", "b", "d", "gh", "gn"],
    nuclei: ["a", "o", "u", "aa", "uu"],
    codas: ["", "", "g", "k", "sh", "r", "z", "gh", "rk", "gz", "ash", "nak"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 2],
    surnameSuffixes: ["fang", "maw", "tusk", "skull", "gore", "rend"],
  },
  draconic: {
    label: "Draconic (fantasy)",
    onsets: ["", "v", "vr", "k", "kr", "th", "s", "sh", "z", "x", "n", "r", "g", "gh", "ss"],
    nuclei: ["a", "e", "i", "ae", "ia", "aa", "y"],
    codas: ["", "", "x", "ss", "th", "r", "n", "rax", "zar", "ith", "oth"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["rax", "thyr", "zoth", "wyrm", "scale", "maw"],
  },
  fae: {
    label: "Fae (sylvan, fantasy)",
    onsets: ["", "f", "fl", "l", "m", "n", "s", "sh", "th", "v", "w", "wh", "br", "gl", "ph"],
    nuclei: ["a", "e", "i", "ae", "ia", "ie", "ei", "ee", "oo", "ai"],
    codas: ["", "", "l", "n", "ll", "sh", "th", "w", "ren", "lyn", "sel"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["thistle", "blossom", "willow", "dew", "bramble", "fen"],
  },
  infernal: {
    label: "Infernal (demonic, fantasy)",
    onsets: ["", "b", "d", "g", "k", "m", "n", "r", "s", "v", "z", "th", "kr", "gr", "x"],
    nuclei: ["a", "e", "o", "u", "aa", "ae", "ai"],
    codas: ["", "", "l", "r", "z", "th", "x", "oth", "gor", "eth", "nax"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["bane", "thorn", "grave", "dross", "ash", "scourge"],
  },
  celestial: {
    label: "Celestial (angelic, fantasy)",
    onsets: ["", "s", "sh", "th", "m", "n", "l", "r", "v", "z", "h", "el", "ra", "mi"],
    nuclei: ["a", "e", "i", "ae", "ia", "ie", "ei", "io", "au"],
    codas: ["", "", "l", "el", "iel", "ah", "on", "im"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["iel", "phim", "halo", "dawn", "song", "light"],
  },

  /* ----- sci-fi / otherworldly ----- */

  synthetic: {
    label: "Synthetic (android, sci-fi)",
    onsets: ["", "k", "kr", "n", "v", "x", "z", "t", "tr", "dr", "s", "q"],
    nuclei: ["a", "e", "i", "o", "y", "ay", "ix"],
    codas: ["", "", "x", "n", "k", "tron", "dex", "vex", "on", "ix"],
    givenSyllables: [2, 3],
    surnameSyllables: [1, 2],
    surnameSuffixes: ["-Prime", "-Core", "-Drive", "-Node", "-Mk"],
  },
  xenoid: {
    label: "Xenoid (alien/insectoid, sci-fi)",
    onsets: ["", "k", "kr", "x", "z", "zh", "ch", "t", "ts", "q", "ss", "thr"],
    nuclei: ["a", "i", "ee", "ix", "aa", "y", "e"],
    codas: ["", "", "k", "x", "ss", "zt", "kt", "ix", "thk"],
    givenSyllables: [2, 3],
    surnameSyllables: [1, 2],
    surnameSuffixes: ["zix", "kkt", "xul", "rrk", "zhar"],
  },
  aquan: {
    label: "Aquan (oceanic, fantasy/sci-fi)",
    onsets: ["", "l", "m", "n", "r", "s", "sh", "th", "v", "w", "fl", "gl", "ph"],
    nuclei: ["a", "e", "i", "o", "u", "aa", "oo", "ua", "ai", "ee"],
    codas: ["", "", "l", "n", "r", "sh", "th", "mar", "len", "ril", "oon"],
    givenSyllables: [2, 3],
    surnameSyllables: [2, 3],
    surnameSuffixes: ["tide", "wave", "deep", "current", "coral", "mere"],
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
  "South Korea": "korean",
  "Turkey": "turkic",
  "Kazakhstan": "turkic",
  "Finland": "finnic",
  "Estonia": "finnic",
  "Israel": "hebraic",
  "Germany": "germanic",
  "Netherlands": "germanic",
  "Austria": "germanic",
  "Iran": "persian",
  "Thailand": "thai",
  "New Zealand": "polynesian",
  "Samoa": "polynesian",
  "Tonga": "polynesian",
  "Mongolia": "mongolic",
  "Vietnam": "vietnamese",
  "Mexico": "nahuatl",
  "Peru": "quechua",
  "Bolivia": "quechua",
  "Greenland": "inuit",
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

/*
 * Physical-description data. DESCRIPTORS holds the default (human-like) pools.
 * SPECIES_PROFILES overrides specific pools/nouns for non-human language
 * families so their descriptions stay coherent (e.g. Orcs aren't "blond").
 * Anything a profile omits falls back to the DESCRIPTORS default.
 */
const DESCRIPTORS = {
  genders: ["man", "woman", "person"],
  ages: [
    "in their late teens", "in their twenties", "in their thirties",
    "in their forties", "middle-aged", "in their sixties", "elderly",
  ],
  // Plain adjectives/phrases that read naturally after the gender clause.
  heights: ["short", "of medium height", "tall", "petite", "on the taller side", "lanky"],
  builds: [
    "slender", "lean", "average", "stocky", "broad-shouldered", "muscular",
    "wiry", "heavyset", "willowy", "compact", "sturdy", "athletic",
  ],
  hairColors: [
    "black", "dark brown", "brown", "chestnut", "auburn", "red",
    "blond", "sandy", "grey", "silver", "white",
  ],
  hairStyles: [
    "close-cropped", "short", "shoulder-length", "long", "curly", "wavy",
    "straight", "braided", "tousled", "neatly tied-back",
  ],
  eyeColors: ["brown", "dark brown", "hazel", "green", "blue", "grey", "amber"],
  skinTones: [
    "pale", "fair", "light", "olive", "tan", "light brown", "brown",
    "dark brown", "deep brown", "bronze", "ruddy",
  ],
  // Optional, low-key distinguishing features.
  features: [
    "a faint scar across one cheek", "a scattering of freckles",
    "a crooked nose", "high cheekbones", "a warm, easy smile",
    "weathered, calloused hands", "a small mole near one eye",
    "laugh lines", "a strong jaw", "a gap-toothed grin",
    "tired but kind eyes", "a few old scars on the hands",
  ],
};

// Beards are only offered for the "man" gender on human-like profiles.
const MASC_FEATURES = [
  "a neatly kept beard", "a short beard", "a thick beard",
  "light stubble", "a long braided beard",
];

// Hair tends to grey with age; these replace the colour for older characters.
const OLDER_AGES = ["middle-aged", "in their sixties", "elderly"];
const GREY_HAIRS = ["grey", "silver", "white", "steel grey", "salt-and-pepper"];

const SPECIES_PROFILES = {
  elvish: {
    builds: ["slender", "willowy", "lithe", "lean", "graceful"],
    signatureFeature: "gracefully pointed ears",
    signatureChance: 0.85,
  },
  fae: {
    builds: ["slight", "slender", "willowy", "petite", "delicate"],
    heights: ["short", "petite", "small and quick", "of slight build"],
    signatureFeature: "delicately pointed ears",
    signatureChance: 0.85,
  },
  celestial: {
    skinTones: ["luminous", "pale gold", "fair", "softly radiant", "ivory"],
    eyeColors: ["gold", "pale blue", "silver", "amber"],
    hairColors: ["golden", "silver-white", "white", "pale blond"],
    signatureFeature: "a faint glow about them",
    signatureChance: 0.5,
  },
  infernal: {
    skinTones: ["ashen", "dusky red", "slate grey", "dark", "reddish"],
    eyeColors: ["red", "amber", "black", "burning gold"],
    hairColors: ["black", "dark red", "ash grey"],
    signatureFeature: "small curved horns",
    signatureChance: 0.75,
  },
  orcish: {
    humanlike: false,
    genders: ["man", "woman", "warrior"],
    builds: ["broad-shouldered", "muscular", "heavyset", "powerfully built", "thickset"],
    heights: ["tall", "towering", "broad and heavy", "imposing"],
    skinTones: ["mossy green", "grey-green", "ashen grey", "olive green", "slate grey"],
    eyeColors: ["yellow", "amber", "red", "dark"],
    hairColors: ["black", "dark grey", "coarse black"],
    signatureFeature: "prominent lower tusks",
    signatureChance: 0.85,
  },
  dwarvish: {
    builds: ["stocky", "broad-shouldered", "sturdy", "barrel-chested", "compact"],
    heights: ["short", "short and broad", "of compact stature", "low and solid"],
    signatureFeature: "a long, braided beard",
    signatureChance: 0.7,
  },
  draconic: {
    humanlike: false,
    genders: ["man", "woman", "dragonkin"],
    skinNoun: "scales",
    skinTones: ["crimson", "emerald", "obsidian", "bronze", "ivory", "slate-blue", "gold"],
    eyeNoun: "slit-pupiled eyes",
    eyeColors: ["gold", "amber", "green", "red"],
    hairless: true,
    signatureFeature: "short, curved horns",
    signatureChance: 0.7,
  },
  xenoid: {
    humanlike: false,
    genders: ["being", "creature", "drone"],
    skinNoun: "chitin",
    skinTones: ["mottled grey", "iridescent", "pale green", "bone-white", "dark"],
    eyeNoun: "compound eyes",
    eyeColors: ["black", "dark", "glassy"],
    hairless: true,
    signatureFeature: "a hard, segmented carapace",
    signatureChance: 0.6,
  },
  synthetic: {
    humanlike: false,
    genders: ["android", "unit", "construct"],
    ages: ["a current-gen model", "a late-model unit", "an aging model", "a prototype build", "a refurbished chassis"],
    builds: ["sleek", "heavy-framed", "slender", "industrial", "compact"],
    heights: ["tall", "of standard height", "compact", "imposing"],
    skinNoun: "plating",
    skinTones: ["matte grey", "brushed steel", "white", "gunmetal", "bronze"],
    eyeNoun: "optical lenses",
    eyeColors: ["blue", "amber", "red", "green", "white"],
    hairless: true,
    signatureFeature: "a softly glowing status light",
    signatureChance: 0.5,
  },
  aquan: {
    skinTones: ["blue-grey", "teal", "pale blue", "sea-green", "silver"],
    eyeColors: ["sea-green", "blue", "silver", "dark"],
    hairColors: ["dark", "blue-black", "silver", "pale green"],
    signatureFeature: "faint gill-lines along the neck",
    signatureChance: 0.6,
  },
};
