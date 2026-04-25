// Clafrica Mapping for special character shortcuts
export const Clafrica = {
  "aff":"ɑɑ",
  "aff1":"ɑ̀ɑ̀",
  "aff2":"ɑ́ɑ́",
  "aff3":"ɑ̄ɑ̄",
  "ɑɑ1":"ɑ̀ɑ̀",
  "ɑɑ2":"ɑ́ɑ́",
  "ɑɑ3":"ɑ̄ɑ̄",

  // ─── Post-finalization tone mappings ─────────────────────────────────────────
  // After a special char is emitted (auto-finalize or immediate resolve), the
  // user can still append a tone number and get the correctly toned result.
  // a / à á ā
  "à1":"àà",  "à2":"ǎ",   "à3":"a᷅",
  "á1":"â",   "á2":"áá",  "á3":"a᷇",
  "ā2":"a᷄",  "ā3":"āā",
  // A uppercase
  "À2":"Ǎ",   "Á1":"Â",
  // ɑ (from af)
  "ɑ1":"ɑ̀",  "ɑ2":"ɑ́",  "ɑ3":"ɑ̄",  "ɑ5":"ɑ̂",  "ɑ7":"ɑ̌",
  "ɑ̀1":"ɑ̀ɑ̀", "ɑ̀2":"ɑ̌",   "ɑ̀3":"ɑ᷅",
  "ɑ́1":"ɑ̂",  "ɑ́2":"ɑ́ɑ́", "ɑ́3":"ɑ᷇",
  "ɑ̄2":"ɑ᷄",  "ɑ̄3":"ɑ̄ɑ̄",
  // e / è é ē
  "è1":"èè",  "è2":"ě",   "è3":"e᷅",
  "é1":"ê",   "é2":"éé",  "é3":"e᷇",
  "ē2":"e᷄",  "ē3":"ēē",
  "e̠3":"ē̠",
  // ə (from eu)
  "ə1":"ə̀",  "ə2":"ə́",  "ə3":"ə̄",  "ə5":"ə̂",  "ə7":"ə̌",
  "ə̀1":"ə̀ə̀", "ə̀2":"ə̌",   "ə̀3":"ə᷅",
  "ə́1":"ə̂",  "ə́2":"ə́ə́", "ə́3":"ə᷇",
  "ə̄2":"ə᷄",  "ə̄3":"ə̄ə̄",
  // ε/ɛ (from ai)
  "ε1":"ɛ̀",  "ε2":"έ",   "ε3":"ɛ̄",  "ε5":"ɛ̂",  "ε7":"ɛ̌",
  "έ1":"ɛ̂",  "έ2":"έέ",  "έ3":"ɛ᷇",
  "ɛ̀1":"ɛ̀ɛ̀", "ɛ̀2":"ɛ̌",   "ɛ̀3":"ɛ᷅",
  "ɛ̄2":"ɛ᷄",  "ɛ̄3":"ɛ̄ɛ̄",
  // i / ì í ī
  "ì1":"ìì",  "ì2":"ǐ",   "ì3":"i᷅",
  "í1":"î",   "í2":"íí",  "í3":"i᷇",
  "ī2":"i᷄",  "ī3":"īī",
  // iɑ (from iaf)
  "iɑ1":"ìɑ̀", "iɑ2":"íɑ́", "iɑ3":"īɑ̄", "iɑ5":"iɑ̂", "iɑ7":"iɑ̌",
  // ɨ (from i-)
  "ɨ1":"ɨ̀",  "ɨ2":"ɨ́",  "ɨ3":"ɨ̄",  "ɨ5":"ɨ̂",  "ɨ7":"ɨ̌",
  // Ŋ (from N*)
  "Ŋ1":"Ŋ̀",  "Ŋ2":"Ŋ́",  "Ŋ3":"Ŋ̄",  "Ŋ5":"Ŋ̂",  "Ŋ7":"Ŋ̌",
  // o / ò ó ō
  "ò1":"òò",  "ò2":"ǒ",   "ò3":"o᷅",
  "ó1":"ô",   "ó2":"óó",  "ó3":"o᷇",
  "ō2":"o᷄",  "ō3":"ōō",
  "òò2":"ǒǒ", "óó1":"ôô",
  // O uppercase
  "Ò2":"Ǒ",   "Ó1":"Ô",
  // ɔ (from o*)
  "ɔ1":"ɔ̀",  "ɔ2":"ɔ́",  "ɔ3":"ɔ̄",  "ɔ5":"ɔ̂",  "ɔ7":"ɔ̌",
  "ɔ̀1":"ɔ̀ɔ̀", "ɔ̀2":"ɔ̌",   "ɔ̀3":"ɔ᷅",
  "ɔ́1":"ɔ̂",  "ɔ́2":"ɔ́ɔ́", "ɔ́3":"ɔ᷇",
  "ɔ̄2":"ɔ᷄",  "ɔ̄3":"ɔ̄ɔ̄",
  // Ɔ uppercase (from O*)
  "Ɔ1":"Ɔ̀",  "Ɔ2":"Ɔ́",  "Ɔ3":"Ɔ̄",  "Ɔ5":"Ɔ̂",  "Ɔ7":"Ɔ̌",
  // u / ù ú ū
  "ù1":"ùù",  "ù2":"ǔ",   "ù3":"u᷅",
  "ú1":"û",   "ú2":"úú",  "ú3":"u᷇",
  "ū2":"u᷄",  "ū3":"ūū",
  // ʉ (from u- / uu)
  "ʉ1":"ʉ̀",  "ʉ2":"ʉ́",  "ʉ3":"ʉ̄",  "ʉ5":"ʉ̂",  "ʉ7":"ʉ̌",
  "ʉ̀1":"ʉ̀ʉ̀", "ʉ̀2":"ʉ̌",   "ʉ̀3":"ʉ᷅",
  "ʉ́1":"ʉ̂",  "ʉ́2":"ʉ́ʉ́", "ʉ́3":"ʉ᷇",
  "ʉ̄2":"ʉ᷄",  "ʉ̄3":"ʉ̄ʉ̄",
  "c_":"ç",
  "c_ced":"ç",
  "C_":"Ç",
  "C_ced":"Ç",
  "a13":"a᷅",
  "a23":"a᷇",
  "a32":"a᷄",
  "af13":"ɑ᷅",
  "af23":"ɑ᷇",
  "af32":"ɑ᷄",
  "ai13":"ɛ᷅",
  "ai23":"ɛ᷇",
  "ai32":"ɛ᷄",
  "e13":"e᷅",
  "e23":"e᷇",
  "e32":"e᷄",
  "eu13":"ə᷅",
  "eu23":"ə᷇",
  "eu32":"ə᷄",
  "i13":"i᷅",
  "i23":"i᷇",
  "i32":"i᷄",
  "o*13":"ɔ᷅",
  "o*23":"ɔ᷇",
  "o*32":"ɔ᷄",
  "o13":"o᷅",
  "o23":"o᷇",
  "o32":"o᷄",
  "u13":"u᷅",
  "u23":"u᷇",
  "u32":"u᷄",
  "uu13":"ʉ᷅",
  "uu23":"ʉ᷇",
  "uu32":"ʉ᷄",
  "a11":"àà",
  "a22":"áá",
  "a33":"āā",
  "af11":"ɑ̀ɑ̀",
  "af22":"ɑ́ɑ́",
  "af33":"ɑ̄ɑ̄",
  "e11":"èè",
  "e22":"éé",
  "e33":"ēē",
  "eu11":"ə̀ə̀",
  "eu22":"ə́ə́",
  "eu33":"ə̄ə̄",
  "ai11":"ɛ̀ɛ̀",
  "ai22":"έέ",
  "ai33":"ɛ̄ɛ̄",
  "i11":"ìì",
  "i22":"íí",
  "i33":"īī",
  "o11":"òò",
  "o22":"óó",
  "o33":"ōō",
  "o*11":"ɔ̀ɔ̀",
  "o*22":"ɔ́ɔ́",
  "o*33":"ɔ̄ɔ̄",
  "uu11":"ʉ̀ʉ̀",
  "uu22":"ʉ́ʉ́",
  "uu33":"ʉ̄ʉ̄",
  "u11":"ùù",
  "u22":"úú",
  "u33":"ūū",
  "u-11":"ʉ̀ʉ̀",
  "u-22":"ʉ́ʉ́",
  "u-33":"ʉ̄ʉ̄",
  "uuaf1":"ʉ̀ɑ̀",
  "uuaf2":"ʉ́ɑ́",
  "uuaf3":"ʉ̄ɑ̄",
  "o*21":"ɔ̂",
  "o*12":"ɔ̌",
  "af12":"ɑ̌",
  "uuaf5":"ʉɑ̂",
  "uuaf7":"ʉɑ̌",
  "uuaf ":"ʉɑ",
  "eu12":"ə̌",
  "ai12":"ɛ̌",
  "uu12":"ʉ̌",
  "af21":"ɑ̂",
  "eu21":"ə̂",
  "ai21":"ɛ̂",
  "uu21":"ʉ̂",
  "uaf1":"ùɑ̀",
  "iaf1":"ìɑ̀",
  "uaf2":"úɑ́",
  "iaf2":"íɑ́",
  "iaf5":"iɑ̂",
  "iaf7":"iɑ̌",
  "uaf3":"ūɑ̄",
  "iaf3":"īɑ̄",
  "oo12":"ǒǒ",
  "oo21":"ôô",
  "..af":"ɑ̈",
  "..ai":"ɛ̈",
  "..eu":"ə̈",
  "..o*":"ɔ̈",
  "..uu":"ʉ̈",
  "ai1":"ɛ̀",
  "ii1":"ìì",
  "o*2":"ɔ́",
  "o*3":"ɔ̄",
  "o*1":"ɔ̀",
  "uu1":"ʉ̀",
  "eu1":"ə̀",
  "eu2":"ə́",
  "ai2":"έ",
  "uu2":"ʉ́",
  "eu3":"ə̄",
  "uu3":"ʉ̄",
  "a12":"ǎ",
  "iaf":"iɑ",
  "e12":"ě",
  "i12":"ǐ",
  "u12":"ǔ",
  "a21":"â",
  "e21":"ê",
  "i21":"î",
  "u21":"û",
  "aa1":"àà",
  "ua1":"ùà",
  "ia1":"ìà",
  "aff ":"ɑɑ",
  "ee1":"èè",
  "ie1":"ìè",
  "af":"ɑ",
  "af1":"ɑ̀",
  "aa2":"áá",
  "ee2":"éé",
  "ii2":"íí",
  "ie2":"íé",
  "oo2":"óó",
  "ua2":"úá",
  "ia2":"íá",
  "af2":"ɑ́",
  "ii3":"īī",
  "ai3":"ɛ̄",
  "ie3":"īē",
  "ee3":"ēē",
  "oo3":"ōō",
  "ua3":"ūā",
  "ia3":"īā",
  "aa3":"āā",
  "af3":"ɑ̄",
  "o12":"ǒ",
  "oo1":"òò",
  "o21":"ô",
  "o*7":"ɔ̌",
  "o*5":"ɔ̂",
  "af7":"ɑ̌",
  "eu7":"ə̌",
  "ai7":"ɛ̌",
  "uu7":"ʉ̌",
  "af5":"ɑ̂",
  "eu5":"ə̂",
  "ai5":"ɛ̂",
  "uu5":"ʉ̂",
  "oo7":"ǒǒ",
  "oo5":"ôô",
  "..a":"ä",
  "..b":"b̈",
  "..c":"c̈",
  "..d":"d̈",
  "..e":"ë",
  "..f":"f̈",
  "..g":"g̈",
  "..h":"ḧ",
  "..i":"ï",
  "..j":"j̈",
  "..k":"k̈",
  "..l":"l̈",
  "..m":"m̈",
  "..n":"n̈",
  "..o":"ö",
  "..p":"p̈",
  "..q":"q̈",
  "..r":"r̈",
  "..s":"s̈",
  "..t":"ẗ",
  "..u":"ü",
  "..v":"v̈",
  "..w":"ẅ",
  "..x":"ẍ",
  "..y":"ÿ",
  "..z":"z̈",
  ".af":"ɑ̇",
  ".ai":"ε̇",
  ".eu":"ə̇",
  ".o*":"ɔ̇",
  ".uu":"ʉ̇",
  "u1":"ù",
  "u2":"ú",
  "o*":"ɔ",
  "i1":"ì",
  "u3":"ū",
  "a1":"à",
  "e1":"è",
  "n*":"ŋ",
  "i2":"í",
  "e2":"é",
  "a2":"á",
  "i3":"ī",
  "e3":"ē",
  "a3":"ā",
  "o1":"ò",
  "o2":"ó",
  "o3":"ō",
  "a7":"ǎ",
  "e7":"ě",
  "i7":"ǐ",
  "u7":"ǔ",
  "a5":"â",
  "e5":"ê",
  "i5":"î",
  "u5":"û",
  "o7":"ǒ",
  "o5":"ô",
  ".?":"ʔ",
  ".a":"ȧ",
  ".b":"ḃ",
  ".c":"ċ",
  ".d":"ḋ",
  ".e":"ė",
  ".f":"ḟ",
  ".g":"ġ",
  ".h":"ḣ",
  ".i":"i̇",
  ".j":"j̇",
  ".k":"k̇",
  ".l":"l̇",
  ".m":"ṁ",
  ".n":"ṅ",
  ".o":"ȯ",
  ".p":"ṗ",
  ".q":"q̇",
  ".r":"ṙ",
  ".s":"ṡ",
  ".t":"ṫ",
  ".u":"u̇",
  ".v":"v̇",
  ".w":"ẇ",
  ".x":"ẋ",
  ".y":"ẏ",
  ".z":"ż",
  "?.":"ʔ",
  "u-1":"ʉ̀",
  "u-2":"ʉ́",
  "u-3":"ʉ̄",
  "af ":"ɑ",
  "eu":"ə",
  "ai":"ε",
  "uu ":"ʉ",
  "u-5":"ʉ̂",
  "u-7":"ʉ̌",
  "u- ":"ʉ",
  "u-":"ʉ",
  "n1":"ǹ",
  "n2":"ń",
  "n3":"n̄",
  "n7":"ň",
  "n5":"n̂",
  "m1":"m̀",
  "m2":"ḿ",
  "m3":"m̄",
  "m7":"m̌",
  "m5":"m̂",
  "N1":"Ǹ",
  "N2":"Ń",
  "N3":"N̄",
  "N7":"Ň",
  "N5":"N̂",
  "N*1":"Ŋ̀",
  "N*2":"Ŋ́",
  "N*3":"Ŋ̄",
  "N*7":"Ŋ̌",
  "N*5":"Ŋ̂",
  "N*":"Ŋ",
  "M1":"M̀",
  "M2":"Ḿ",
  "M3":"M̄",
  "M7":"M̌",
  "M5":"M̂",
  "A1":"À",
  "A2":"Á",
  "A3":"Ā",
  "A7":"Ǎ",
  "A5":"Â",
  "E1":"È",
  "E2":"É",
  "E3":"Ē",
  "E7":"Ě",
  "E5":"Ê",
  "O1":"Ò",
  "O2":"Ó",
  "O3":"Ō",
  "O7":"Ǒ",
  "O5":"Ô",
  "O*1":"Ɔ̀",
  "O*2":"Ɔ́",
  "O*3":"Ɔ̄",
  "O*7":"Ɔ̌",
  "O*5":"Ɔ̂",
  "O*":"Ɔ",
  "A12":"Ǎ",
  "A21":"Â",
  "O12":"Ǒ",
  "O21":"Ô",
  "e3_":"ē̠",
  "e_3":"ē̠",
  "e_":"e̠",
  "*n":"ɲ",
  "b*":"ɓ",
  "B*":"Ɓ",
  "d*":"ɗ",
  "D*":"Ɗ",
  "*N":"Ɲ",
  "U1":"Ù",
  "U2":"Ú",
  "U3":"Ū",
  "U5":"Û",
  "U7":"Ǔ",
  "I1":"Ì",
  "I2":"Í",
  "I3":"Ī",
  "I5":"Î",
  "I7":"Ǐ",
  "AI1":"Ɛ̀",
  "AI2":"έ",
  "AI3":"Ɛ̄",
  "AI5":"Ɛ̂",
  "AI7":"Ɛ̌",
  "EU1":"Ə̀",
  "EU2":"Ə́",
  "EU3":"Ə̄",
  "EU5":"Ə̂",
  "a~":"ã",
  "i~":"ĩ",
  "u~":"ũ",
  "e~":"ẽ",
  "o~":"õ",
  "ai~":"ɛ̃",
  "o*~":"ɔ̃",
  "af~":"ɑ̃",
  "eq.":"=",
  "pluss":"+",
  "i-":"ɨ",
  "i-1":"ɨ̀",
  "i-2":"ɨ́",
  "i-3":"ɨ̄",
  "i-7":"ɨ̌",
  "i-5":"ɨ̂"
};

/** Only Latin-ASCII shortcut spellings (af7, n*, …) are case-aliased; Unicode keys (à2 vs À2) stay exact. */
const isAsciiOnlyShortcut = (s: string): boolean => !/[^\x00-\x7F]/.test(s);

/** Resolve ASCII shortcut keys case-insensitively (keyboards often send AF7 instead of af7). */
const resolveClafricaKey = (token: string): keyof typeof Clafrica | null => {
  if (token in Clafrica) return token as keyof typeof Clafrica;
  if (isAsciiOnlyShortcut(token)) {
    const lower = token.toLowerCase();
    if (lower !== token && lower in Clafrica) return lower as keyof typeof Clafrica;
  }
  return null;
};

/**
 * Applies Clafrica mapping to transform input text with shortcut keys
 * into the corresponding special characters
 * 
 * @param input - The input text with potential shortcut keys
 * @returns The transformed text with special characters
 */
const applyClafricaMappingToToken = (token: string): string => {
  if (!token) return token;

  const direct = resolveClafricaKey(token);
  if (direct) {
    return Clafrica[direct];
  }

  const letterWithTwoNumbersPattern = /^([a-zA-Z]+\*?)([1-9])([1-9])$/;
  const twoNumberMatch = token.match(letterWithTwoNumbersPattern);

  if (twoNumberMatch) {
    const [, letters, num1, num2] = twoNumberMatch;
    const combinedKey = `${letters}${num1}${num2}`;
    const resolved = resolveClafricaKey(combinedKey);
    if (resolved) {
      return Clafrica[resolved];
    }
  }

  const letterWithNumberPattern = /^([a-zA-Z]+\*?)([1-9])$/;
  const oneNumberMatch = token.match(letterWithNumberPattern);

  if (oneNumberMatch) {
    const [, letters, num] = oneNumberMatch;
    const combinedKey = `${letters}${num}`;
    const resolved = resolveClafricaKey(combinedKey);
    if (resolved) {
      return Clafrica[resolved];
    }
  }

  const allKeys = Object.keys(Clafrica).sort((a, b) => b.length - a.length);

  for (const key of allKeys) {
    if (token === key) {
      return Clafrica[key as keyof typeof Clafrica];
    }
  }

  let result = token;
  let changed = true;

  while (changed) {
    changed = false;

    for (const key of allKeys) {
      if (key.length > result.length) continue;

      const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const insens = isAsciiOnlyShortcut(key);
      const probe = insens ? new RegExp(escapedKey, 'i') : new RegExp(escapedKey);
      if (!probe.test(result)) continue;

      const value = Clafrica[key as keyof typeof Clafrica];
      const regex = new RegExp(escapedKey, insens ? 'gi' : 'g');
      const newResult = result.replace(regex, value);

      if (newResult !== result) {
        result = newResult;
        changed = true;
        break;
      }
    }
  }

  return result;
};

const ALL_CLAFRICA_KEYS = Object.keys(Clafrica).sort((a, b) => b.length - a.length);
const AMBIGUOUS_CLAFRICA_KEYS = new Set(
  ALL_CLAFRICA_KEYS.filter((key) =>
    ALL_CLAFRICA_KEYS.some((otherKey) => otherKey.length > key.length && otherKey.startsWith(key))
  )
);

const getLongestTrailingPrefix = (token: string): string | null => {
  let longestSuffix: string | null = null;
  const lowerToken = token.toLowerCase();

  for (let index = 0; index < token.length; index += 1) {
    const suffix = token.slice(index);
    const suffixLower = lowerToken.slice(index);
    const asciiSuffix = isAsciiOnlyShortcut(suffix);
    if (
      ALL_CLAFRICA_KEYS.some((key) => {
        if (key.startsWith(suffix)) return true;
        if (asciiSuffix && isAsciiOnlyShortcut(key) && key.toLowerCase().startsWith(suffixLower)) {
          return true;
        }
        return false;
      })
    ) {
      if (!longestSuffix || suffix.length > longestSuffix.length) {
        longestSuffix = suffix;
      }
    }
  }

  return longestSuffix;
};

const COMBINING_LOW_TONE_MARK_REGEX = /\u0300/g;

export function stripLowToneMarks(input: string): string {
  return input
    .normalize("NFD")
    .replace(COMBINING_LOW_TONE_MARK_REGEX, "")
    .normalize("NFC");
}

const getLongestTrailingExactKey = (token: string): string | null => {
  let longestSuffix: string | null = null;

  for (let index = 0; index < token.length; index += 1) {
    const suffix = token.slice(index);
    if (resolveClafricaKey(suffix)) {
      if (!longestSuffix || suffix.length > longestSuffix.length) {
        longestSuffix = suffix;
      }
    }
  }

  return longestSuffix;
};

type ApplyClafricaMappingOptions = {
  preserveAmbiguousTrailingToken?: boolean;
};

const getAmbiguousTrailingSuffix = (token: string): string | null => {
  let longestSuffix: string | null = null;

  for (let index = 0; index < token.length; index += 1) {
    const suffix = token.slice(index);
    const canonical = resolveClafricaKey(suffix);
    if (canonical && AMBIGUOUS_CLAFRICA_KEYS.has(canonical)) {
      if (!longestSuffix || suffix.length > longestSuffix.length) {
        longestSuffix = suffix;
      }
    }
  }

  return longestSuffix;
};

const applyLiveClafricaMappingToTrailingToken = (token: string): string => {
  if (!token) {
    return token;
  }

  const canonical = resolveClafricaKey(token);
  if (canonical) {
    if (AMBIGUOUS_CLAFRICA_KEYS.has(canonical)) {
      return token;
    }
    return Clafrica[canonical];
  }

  const exactTrailingKey = getLongestTrailingExactKey(token);
  const exactCanonical = exactTrailingKey ? resolveClafricaKey(exactTrailingKey) : null;
  if (exactTrailingKey && exactCanonical && !AMBIGUOUS_CLAFRICA_KEYS.has(exactCanonical)) {
    const prefix = token.slice(0, token.length - exactTrailingKey.length);
    return `${applyClafricaMappingToToken(prefix)}${Clafrica[exactCanonical]}`;
  }

  const ambiguousSuffix = getAmbiguousTrailingSuffix(token);
  if (ambiguousSuffix) {
    const prefix = token.slice(0, token.length - ambiguousSuffix.length);
    return `${applyClafricaMappingToToken(prefix)}${ambiguousSuffix}`;
  }

  const prefixSuffix = getLongestTrailingPrefix(token);
  if (prefixSuffix) {
    const prefix = token.slice(0, token.length - prefixSuffix.length);
    return `${applyClafricaMappingToToken(prefix)}${prefixSuffix}`;
  }

  return applyClafricaMappingToToken(token);
};

const finalizeClafricaToken = (token: string): string => {
  if (!token) {
    return token;
  }

  let current = token;
  let changed = true;

  while (changed) {
    changed = false;

    const exactTrailingKey = getLongestTrailingExactKey(current);
    const exactCanonical = exactTrailingKey ? resolveClafricaKey(exactTrailingKey) : null;
    if (exactTrailingKey && exactCanonical) {
      const prefix = current.slice(0, current.length - exactTrailingKey.length);
      const next = `${applyClafricaMappingToToken(prefix)}${Clafrica[exactCanonical]}`;

      if (next !== current) {
        current = next;
        changed = true;
        continue;
      }
    }

    const fullyMapped = applyClafricaMappingToToken(current);
    if (fullyMapped !== current) {
      current = fullyMapped;
      changed = true;
    }
  }

  return current;
};

export const applyClafricaMapping = (
  input: string,
  options: ApplyClafricaMappingOptions = {}
): string => {
  if (!input) return input;

  const { preserveAmbiguousTrailingToken = false } = options;
  const segments = input.split(/(\s+)/);
  const trailingTokenIndex = !/\s$/.test(input) ? segments.length - 1 : -1;

  return segments
    .map((segment, index) => {
      if (/\s+/.test(segment)) {
        return segment;
      }

      if (
        preserveAmbiguousTrailingToken &&
        index === trailingTokenIndex
      ) {
        return applyLiveClafricaMappingToTrailingToken(segment);
      }

      return applyClafricaMappingToToken(segment);
    })
    .join('');
};

export const finalizeClafricaInput = (input: string): string => {
  if (!input) return input;

  return input
    .split(/(\s+)/)
    .map((segment) => (/\s+/.test(segment) ? segment : finalizeClafricaToken(segment)))
    .join('');
};

const INSERT_PALETTE_MAX = 96;

/**
 * Distinct short outputs from the Clafrica table for click-to-insert in the UI
 * (letters and digraphs produced by the mapping).
 */
const buildClafricaInsertPalette = (): string[] => {
  const unique = new Set<string>();
  for (const v of Object.values(Clafrica)) {
    if (typeof v !== 'string' || !v) continue;
    if (v.length >= 1 && v.length <= 4) {
      unique.add(v);
    }
  }
  return Array.from(unique)
    .sort((a, b) => a.length - b.length || a.localeCompare(b, 'en'))
    .slice(0, INSERT_PALETTE_MAX);
};

export const CLAFRICA_INSERT_PALETTE: readonly string[] = buildClafricaInsertPalette();

/**
 * Cleans a word by removing trailing punctuation and converting to lowercase
 * 
 * @param word - The word to clean
 * @returns The cleaned word
 */
export const cleanWord = (word: string): string => {
  return word
    .trim()
    .toLowerCase()
    .replace(/[’]/g, "'")
    .replace(/^[\/.,!?;:()"/`\s]+|[\/.,!?;:()"/`\s]+$/g, '')
    .replace(/^'+/, '');
};
