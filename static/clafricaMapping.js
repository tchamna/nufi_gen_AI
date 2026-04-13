// clafricaMapping.ts
var Clafrica = {
  "aff": "\u0251\u0251",
  "aff1": "\u0251\u0300\u0251\u0300",
  "aff2": "\u0251\u0301\u0251\u0301",
  "aff3": "\u0251\u0304\u0251\u0304",
  "\u0251\u02511": "\u0251\u0300\u0251\u0300",
  "\u0251\u02512": "\u0251\u0301\u0251\u0301",
  "\u0251\u02513": "\u0251\u0304\u0251\u0304",
  // ─── Post-finalization tone mappings ─────────────────────────────────────────
  // After a special char is emitted (auto-finalize or immediate resolve), the
  // user can still append a tone number and get the correctly toned result.
  // a / à á ā
  "\xE01": "\xE0\xE0",
  "\xE02": "\u01CE",
  "\xE03": "a\u1DC5",
  "\xE11": "\xE2",
  "\xE12": "\xE1\xE1",
  "\xE13": "a\u1DC7",
  "\u01012": "a\u1DC4",
  "\u01013": "\u0101\u0101",
  // A uppercase
  "\xC02": "\u01CD",
  "\xC11": "\xC2",
  // ɑ (from af)
  "\u02511": "\u0251\u0300",
  "\u02512": "\u0251\u0301",
  "\u02513": "\u0251\u0304",
  "\u02515": "\u0251\u0302",
  "\u02517": "\u0251\u030C",
  "\u0251\u03001": "\u0251\u0300\u0251\u0300",
  "\u0251\u03002": "\u0251\u030C",
  "\u0251\u03003": "\u0251\u1DC5",
  "\u0251\u03011": "\u0251\u0302",
  "\u0251\u03012": "\u0251\u0301\u0251\u0301",
  "\u0251\u03013": "\u0251\u1DC7",
  "\u0251\u03042": "\u0251\u1DC4",
  "\u0251\u03043": "\u0251\u0304\u0251\u0304",
  // e / è é ē
  "\xE81": "\xE8\xE8",
  "\xE82": "\u011B",
  "\xE83": "e\u1DC5",
  "\xE91": "\xEA",
  "\xE92": "\xE9\xE9",
  "\xE93": "e\u1DC7",
  "\u01132": "e\u1DC4",
  "\u01133": "\u0113\u0113",
  "e\u03203": "\u0113\u0320",
  // ə (from eu)
  "\u02591": "\u0259\u0300",
  "\u02592": "\u0259\u0301",
  "\u02593": "\u0259\u0304",
  "\u02595": "\u0259\u0302",
  "\u02597": "\u0259\u030C",
  "\u0259\u03001": "\u0259\u0300\u0259\u0300",
  "\u0259\u03002": "\u0259\u030C",
  "\u0259\u03003": "\u0259\u1DC5",
  "\u0259\u03011": "\u0259\u0302",
  "\u0259\u03012": "\u0259\u0301\u0259\u0301",
  "\u0259\u03013": "\u0259\u1DC7",
  "\u0259\u03042": "\u0259\u1DC4",
  "\u0259\u03043": "\u0259\u0304\u0259\u0304",
  // ε/ɛ (from ai)
  "\u03B51": "\u025B\u0300",
  "\u03B52": "\u03AD",
  "\u03B53": "\u025B\u0304",
  "\u03B55": "\u025B\u0302",
  "\u03B57": "\u025B\u030C",
  "\u03AD1": "\u025B\u0302",
  "\u03AD2": "\u03AD\u03AD",
  "\u03AD3": "\u025B\u1DC7",
  "\u025B\u03001": "\u025B\u0300\u025B\u0300",
  "\u025B\u03002": "\u025B\u030C",
  "\u025B\u03003": "\u025B\u1DC5",
  "\u025B\u03042": "\u025B\u1DC4",
  "\u025B\u03043": "\u025B\u0304\u025B\u0304",
  // i / ì í ī
  "\xEC1": "\xEC\xEC",
  "\xEC2": "\u01D0",
  "\xEC3": "i\u1DC5",
  "\xED1": "\xEE",
  "\xED2": "\xED\xED",
  "\xED3": "i\u1DC7",
  "\u012B2": "i\u1DC4",
  "\u012B3": "\u012B\u012B",
  // iɑ (from iaf)
  "i\u02511": "\xEC\u0251\u0300",
  "i\u02512": "\xED\u0251\u0301",
  "i\u02513": "\u012B\u0251\u0304",
  "i\u02515": "i\u0251\u0302",
  "i\u02517": "i\u0251\u030C",
  // ɨ (from i-)
  "\u02681": "\u0268\u0300",
  "\u02682": "\u0268\u0301",
  "\u02683": "\u0268\u0304",
  "\u02685": "\u0268\u0302",
  "\u02687": "\u0268\u030C",
  // Ŋ (from N*)
  "\u014A1": "\u014A\u0300",
  "\u014A2": "\u014A\u0301",
  "\u014A3": "\u014A\u0304",
  "\u014A5": "\u014A\u0302",
  "\u014A7": "\u014A\u030C",
  // o / ò ó ō
  "\xF21": "\xF2\xF2",
  "\xF22": "\u01D2",
  "\xF23": "o\u1DC5",
  "\xF31": "\xF4",
  "\xF32": "\xF3\xF3",
  "\xF33": "o\u1DC7",
  "\u014D2": "o\u1DC4",
  "\u014D3": "\u014D\u014D",
  "\xF2\xF22": "\u01D2\u01D2",
  "\xF3\xF31": "\xF4\xF4",
  // O uppercase
  "\xD22": "\u01D1",
  "\xD31": "\xD4",
  // ɔ (from o*)
  "\u02541": "\u0254\u0300",
  "\u02542": "\u0254\u0301",
  "\u02543": "\u0254\u0304",
  "\u02545": "\u0254\u0302",
  "\u02547": "\u0254\u030C",
  "\u0254\u03001": "\u0254\u0300\u0254\u0300",
  "\u0254\u03002": "\u0254\u030C",
  "\u0254\u03003": "\u0254\u1DC5",
  "\u0254\u03011": "\u0254\u0302",
  "\u0254\u03012": "\u0254\u0301\u0254\u0301",
  "\u0254\u03013": "\u0254\u1DC7",
  "\u0254\u03042": "\u0254\u1DC4",
  "\u0254\u03043": "\u0254\u0304\u0254\u0304",
  // Ɔ uppercase (from O*)
  "\u01861": "\u0186\u0300",
  "\u01862": "\u0186\u0301",
  "\u01863": "\u0186\u0304",
  "\u01865": "\u0186\u0302",
  "\u01867": "\u0186\u030C",
  // u / ù ú ū
  "\xF91": "\xF9\xF9",
  "\xF92": "\u01D4",
  "\xF93": "u\u1DC5",
  "\xFA1": "\xFB",
  "\xFA2": "\xFA\xFA",
  "\xFA3": "u\u1DC7",
  "\u016B2": "u\u1DC4",
  "\u016B3": "\u016B\u016B",
  // ʉ (from u- / uu)
  "\u02891": "\u0289\u0300",
  "\u02892": "\u0289\u0301",
  "\u02893": "\u0289\u0304",
  "\u02895": "\u0289\u0302",
  "\u02897": "\u0289\u030C",
  "\u0289\u03001": "\u0289\u0300\u0289\u0300",
  "\u0289\u03002": "\u0289\u030C",
  "\u0289\u03003": "\u0289\u1DC5",
  "\u0289\u03011": "\u0289\u0302",
  "\u0289\u03012": "\u0289\u0301\u0289\u0301",
  "\u0289\u03013": "\u0289\u1DC7",
  "\u0289\u03042": "\u0289\u1DC4",
  "\u0289\u03043": "\u0289\u0304\u0289\u0304",
  "c_": "\xE7",
  "c_ced": "\xE7",
  "C_": "\xC7",
  "C_ced": "\xC7",
  "a13": "a\u1DC5",
  "a23": "a\u1DC7",
  "a32": "a\u1DC4",
  "af13": "\u0251\u1DC5",
  "af23": "\u0251\u1DC7",
  "af32": "\u0251\u1DC4",
  "ai13": "\u025B\u1DC5",
  "ai23": "\u025B\u1DC7",
  "ai32": "\u025B\u1DC4",
  "e13": "e\u1DC5",
  "e23": "e\u1DC7",
  "e32": "e\u1DC4",
  "eu13": "\u0259\u1DC5",
  "eu23": "\u0259\u1DC7",
  "eu32": "\u0259\u1DC4",
  "i13": "i\u1DC5",
  "i23": "i\u1DC7",
  "i32": "i\u1DC4",
  "o*13": "\u0254\u1DC5",
  "o*23": "\u0254\u1DC7",
  "o*32": "\u0254\u1DC4",
  "o13": "o\u1DC5",
  "o23": "o\u1DC7",
  "o32": "o\u1DC4",
  "u13": "u\u1DC5",
  "u23": "u\u1DC7",
  "u32": "u\u1DC4",
  "uu13": "\u0289\u1DC5",
  "uu23": "\u0289\u1DC7",
  "uu32": "\u0289\u1DC4",
  "a11": "\xE0\xE0",
  "a22": "\xE1\xE1",
  "a33": "\u0101\u0101",
  "af11": "\u0251\u0300\u0251\u0300",
  "af22": "\u0251\u0301\u0251\u0301",
  "af33": "\u0251\u0304\u0251\u0304",
  "e11": "\xE8\xE8",
  "e22": "\xE9\xE9",
  "e33": "\u0113\u0113",
  "eu11": "\u0259\u0300\u0259\u0300",
  "eu22": "\u0259\u0301\u0259\u0301",
  "eu33": "\u0259\u0304\u0259\u0304",
  "ai11": "\u025B\u0300\u025B\u0300",
  "ai22": "\u03AD\u03AD",
  "ai33": "\u025B\u0304\u025B\u0304",
  "i11": "\xEC\xEC",
  "i22": "\xED\xED",
  "i33": "\u012B\u012B",
  "o11": "\xF2\xF2",
  "o22": "\xF3\xF3",
  "o33": "\u014D\u014D",
  "o*11": "\u0254\u0300\u0254\u0300",
  "o*22": "\u0254\u0301\u0254\u0301",
  "o*33": "\u0254\u0304\u0254\u0304",
  "uu11": "\u0289\u0300\u0289\u0300",
  "uu22": "\u0289\u0301\u0289\u0301",
  "uu33": "\u0289\u0304\u0289\u0304",
  "u11": "\xF9\xF9",
  "u22": "\xFA\xFA",
  "u33": "\u016B\u016B",
  "u-11": "\u0289\u0300\u0289\u0300",
  "u-22": "\u0289\u0301\u0289\u0301",
  "u-33": "\u0289\u0304\u0289\u0304",
  "uuaf1": "\u0289\u0300\u0251\u0300",
  "uuaf2": "\u0289\u0301\u0251\u0301",
  "uuaf3": "\u0289\u0304\u0251\u0304",
  "o*21": "\u0254\u0302",
  "o*12": "\u0254\u030C",
  "af12": "\u0251\u030C",
  "uuaf5": "\u0289\u0251\u0302",
  "uuaf7": "\u0289\u0251\u030C",
  "uuaf ": "\u0289\u0251",
  "eu12": "\u0259\u030C",
  "ai12": "\u025B\u030C",
  "uu12": "\u0289\u030C",
  "af21": "\u0251\u0302",
  "eu21": "\u0259\u0302",
  "ai21": "\u025B\u0302",
  "uu21": "\u0289\u0302",
  "uaf1": "\xF9\u0251\u0300",
  "iaf1": "\xEC\u0251\u0300",
  "uaf2": "\xFA\u0251\u0301",
  "iaf2": "\xED\u0251\u0301",
  "iaf5": "i\u0251\u0302",
  "iaf7": "i\u0251\u030C",
  "uaf3": "\u016B\u0251\u0304",
  "iaf3": "\u012B\u0251\u0304",
  "oo12": "\u01D2\u01D2",
  "oo21": "\xF4\xF4",
  "..af": "\u0251\u0308",
  "..ai": "\u025B\u0308",
  "..eu": "\u0259\u0308",
  "..o*": "\u0254\u0308",
  "..uu": "\u0289\u0308",
  "ai1": "\u025B\u0300",
  "ii1": "\xEC\xEC",
  "o*2": "\u0254\u0301",
  "o*3": "\u0254\u0304",
  "o*1": "\u0254\u0300",
  "uu1": "\u0289\u0300",
  "eu1": "\u0259\u0300",
  "eu2": "\u0259\u0301",
  "ai2": "\u03AD",
  "uu2": "\u0289\u0301",
  "eu3": "\u0259\u0304",
  "uu3": "\u0289\u0304",
  "a12": "\u01CE",
  "iaf": "i\u0251",
  "e12": "\u011B",
  "i12": "\u01D0",
  "u12": "\u01D4",
  "a21": "\xE2",
  "e21": "\xEA",
  "i21": "\xEE",
  "u21": "\xFB",
  "aa1": "\xE0\xE0",
  "ua1": "\xF9\xE0",
  "ia1": "\xEC\xE0",
  "aff ": "\u0251\u0251",
  "ee1": "\xE8\xE8",
  "ie1": "\xEC\xE8",
  "af": "\u0251",
  "af1": "\u0251\u0300",
  "aa2": "\xE1\xE1",
  "ee2": "\xE9\xE9",
  "ii2": "\xED\xED",
  "ie2": "\xED\xE9",
  "oo2": "\xF3\xF3",
  "ua2": "\xFA\xE1",
  "ia2": "\xED\xE1",
  "af2": "\u0251\u0301",
  "ii3": "\u012B\u012B",
  "ai3": "\u025B\u0304",
  "ie3": "\u012B\u0113",
  "ee3": "\u0113\u0113",
  "oo3": "\u014D\u014D",
  "ua3": "\u016B\u0101",
  "ia3": "\u012B\u0101",
  "aa3": "\u0101\u0101",
  "af3": "\u0251\u0304",
  "o12": "\u01D2",
  "oo1": "\xF2\xF2",
  "o21": "\xF4",
  "o*7": "\u0254\u030C",
  "o*5": "\u0254\u0302",
  "af7": "\u0251\u030C",
  "eu7": "\u0259\u030C",
  "ai7": "\u025B\u030C",
  "uu7": "\u0289\u030C",
  "af5": "\u0251\u0302",
  "eu5": "\u0259\u0302",
  "ai5": "\u025B\u0302",
  "uu5": "\u0289\u0302",
  "oo7": "\u01D2\u01D2",
  "oo5": "\xF4\xF4",
  "..a": "\xE4",
  "..b": "b\u0308",
  "..c": "c\u0308",
  "..d": "d\u0308",
  "..e": "\xEB",
  "..f": "f\u0308",
  "..g": "g\u0308",
  "..h": "\u1E27",
  "..i": "\xEF",
  "..j": "j\u0308",
  "..k": "k\u0308",
  "..l": "l\u0308",
  "..m": "m\u0308",
  "..n": "n\u0308",
  "..o": "\xF6",
  "..p": "p\u0308",
  "..q": "q\u0308",
  "..r": "r\u0308",
  "..s": "s\u0308",
  "..t": "\u1E97",
  "..u": "\xFC",
  "..v": "v\u0308",
  "..w": "\u1E85",
  "..x": "\u1E8D",
  "..y": "\xFF",
  "..z": "z\u0308",
  ".af": "\u0251\u0307",
  ".ai": "\u03B5\u0307",
  ".eu": "\u0259\u0307",
  ".o*": "\u0254\u0307",
  ".uu": "\u0289\u0307",
  "u1": "\xF9",
  "u2": "\xFA",
  "o*": "\u0254",
  "i1": "\xEC",
  "u3": "\u016B",
  "a1": "\xE0",
  "e1": "\xE8",
  "n*": "\u014B",
  "i2": "\xED",
  "e2": "\xE9",
  "a2": "\xE1",
  "i3": "\u012B",
  "e3": "\u0113",
  "a3": "\u0101",
  "o1": "\xF2",
  "o2": "\xF3",
  "o3": "\u014D",
  "a7": "\u01CE",
  "e7": "\u011B",
  "i7": "\u01D0",
  "u7": "\u01D4",
  "a5": "\xE2",
  "e5": "\xEA",
  "i5": "\xEE",
  "u5": "\xFB",
  "o7": "\u01D2",
  "o5": "\xF4",
  ".?": "\u0294",
  ".a": "\u0227",
  ".b": "\u1E03",
  ".c": "\u010B",
  ".d": "\u1E0B",
  ".e": "\u0117",
  ".f": "\u1E1F",
  ".g": "\u0121",
  ".h": "\u1E23",
  ".i": "i\u0307",
  ".j": "j\u0307",
  ".k": "k\u0307",
  ".l": "l\u0307",
  ".m": "\u1E41",
  ".n": "\u1E45",
  ".o": "\u022F",
  ".p": "\u1E57",
  ".q": "q\u0307",
  ".r": "\u1E59",
  ".s": "\u1E61",
  ".t": "\u1E6B",
  ".u": "u\u0307",
  ".v": "v\u0307",
  ".w": "\u1E87",
  ".x": "\u1E8B",
  ".y": "\u1E8F",
  ".z": "\u017C",
  "?.": "\u0294",
  "u-1": "\u0289\u0300",
  "u-2": "\u0289\u0301",
  "u-3": "\u0289\u0304",
  "af ": "\u0251",
  "eu": "\u0259",
  "ai": "\u03B5",
  "uu ": "\u0289",
  "u-5": "\u0289\u0302",
  "u-7": "\u0289\u030C",
  "u- ": "\u0289",
  "u-": "\u0289",
  "n1": "\u01F9",
  "n2": "\u0144",
  "n3": "n\u0304",
  "n7": "\u0148",
  "n5": "n\u0302",
  "m1": "m\u0300",
  "m2": "\u1E3F",
  "m3": "m\u0304",
  "m7": "m\u030C",
  "m5": "m\u0302",
  "N1": "\u01F8",
  "N2": "\u0143",
  "N3": "N\u0304",
  "N7": "\u0147",
  "N5": "N\u0302",
  "N*1": "\u014A\u0300",
  "N*2": "\u014A\u0301",
  "N*3": "\u014A\u0304",
  "N*7": "\u014A\u030C",
  "N*5": "\u014A\u0302",
  "N*": "\u014A",
  "M1": "M\u0300",
  "M2": "\u1E3E",
  "M3": "M\u0304",
  "M7": "M\u030C",
  "M5": "M\u0302",
  "A1": "\xC0",
  "A2": "\xC1",
  "A3": "\u0100",
  "A7": "\u01CD",
  "A5": "\xC2",
  "E1": "\xC8",
  "E2": "\xC9",
  "E3": "\u0112",
  "E7": "\u011A",
  "E5": "\xCA",
  "O1": "\xD2",
  "O2": "\xD3",
  "O3": "\u014C",
  "O7": "\u01D1",
  "O5": "\xD4",
  "O*1": "\u0186\u0300",
  "O*2": "\u0186\u0301",
  "O*3": "\u0186\u0304",
  "O*7": "\u0186\u030C",
  "O*5": "\u0186\u0302",
  "O*": "\u0186",
  "A12": "\u01CD",
  "A21": "\xC2",
  "O12": "\u01D1",
  "O21": "\xD4",
  "e3_": "\u0113\u0320",
  "e_3": "\u0113\u0320",
  "e_": "e\u0320",
  "*n": "\u0272",
  "b*": "\u0253",
  "B*": "\u0181",
  "d*": "\u0257",
  "D*": "\u018A",
  "*N": "\u019D",
  "U1": "\xD9",
  "U2": "\xDA",
  "U3": "\u016A",
  "U5": "\xDB",
  "U7": "\u01D3",
  "I1": "\xCC",
  "I2": "\xCD",
  "I3": "\u012A",
  "I5": "\xCE",
  "I7": "\u01CF",
  "AI1": "\u0190\u0300",
  "AI2": "\u03AD",
  "AI3": "\u0190\u0304",
  "AI5": "\u0190\u0302",
  "AI7": "\u0190\u030C",
  "EU1": "\u018F\u0300",
  "EU2": "\u018F\u0301",
  "EU3": "\u018F\u0304",
  "EU5": "\u018F\u0302",
  "a~": "\xE3",
  "i~": "\u0129",
  "u~": "\u0169",
  "e~": "\u1EBD",
  "o~": "\xF5",
  "ai~": "\u025B\u0303",
  "o*~": "\u0254\u0303",
  "af~": "\u0251\u0303",
  "eq.": "=",
  "pluss": "+",
  "i-": "\u0268",
  "i-1": "\u0268\u0300",
  "i-2": "\u0268\u0301",
  "i-3": "\u0268\u0304",
  "i-7": "\u0268\u030C",
  "i-5": "\u0268\u0302"
};
var isAsciiOnlyShortcut = (s) => !/[^\x00-\x7F]/.test(s);
var resolveClafricaKey = (token) => {
  if (token in Clafrica) return token;
  if (isAsciiOnlyShortcut(token)) {
    const lower = token.toLowerCase();
    if (lower !== token && lower in Clafrica) return lower;
  }
  return null;
};
var applyClafricaMappingToToken = (token) => {
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
      return Clafrica[key];
    }
  }
  let result = token;
  let changed = true;
  while (changed) {
    changed = false;
    for (const key of allKeys) {
      if (key.length > result.length) continue;
      const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const insens = isAsciiOnlyShortcut(key);
      const probe = insens ? new RegExp(escapedKey, "i") : new RegExp(escapedKey);
      if (!probe.test(result)) continue;
      const value = Clafrica[key];
      const regex = new RegExp(escapedKey, insens ? "gi" : "g");
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
var ALL_CLAFRICA_KEYS = Object.keys(Clafrica).sort((a, b) => b.length - a.length);
var AMBIGUOUS_CLAFRICA_KEYS = new Set(
  ALL_CLAFRICA_KEYS.filter(
    (key) => ALL_CLAFRICA_KEYS.some((otherKey) => otherKey.length > key.length && otherKey.startsWith(key))
  )
);
var getLongestTrailingPrefix = (token) => {
  let longestSuffix = null;
  const lowerToken = token.toLowerCase();
  for (let index = 0; index < token.length; index += 1) {
    const suffix = token.slice(index);
    const suffixLower = lowerToken.slice(index);
    const asciiSuffix = isAsciiOnlyShortcut(suffix);
    if (ALL_CLAFRICA_KEYS.some((key) => {
      if (key.startsWith(suffix)) return true;
      if (asciiSuffix && isAsciiOnlyShortcut(key) && key.toLowerCase().startsWith(suffixLower)) {
        return true;
      }
      return false;
    })) {
      if (!longestSuffix || suffix.length > longestSuffix.length) {
        longestSuffix = suffix;
      }
    }
  }
  return longestSuffix;
};
var COMBINING_LOW_TONE_MARK_REGEX = /\u0300/g;
function stripLowToneMarks(input) {
  return input.normalize("NFD").replace(COMBINING_LOW_TONE_MARK_REGEX, "").normalize("NFC");
}
var getLongestTrailingExactKey = (token) => {
  let longestSuffix = null;
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
var getAmbiguousTrailingSuffix = (token) => {
  let longestSuffix = null;
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
var applyLiveClafricaMappingToTrailingToken = (token) => {
  if (!token) {
    return token;
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
var finalizeClafricaToken = (token) => {
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
var applyClafricaMapping = (input, options = {}) => {
  if (!input) return input;
  const { preserveAmbiguousTrailingToken = false } = options;
  const segments = input.split(/(\s+)/);
  const trailingTokenIndex = !/\s$/.test(input) ? segments.length - 1 : -1;
  return segments.map((segment, index) => {
    if (/\s+/.test(segment)) {
      return segment;
    }
    if (preserveAmbiguousTrailingToken && index === trailingTokenIndex) {
      return applyLiveClafricaMappingToTrailingToken(segment);
    }
    return applyClafricaMappingToToken(segment);
  }).join("");
};
var finalizeClafricaInput = (input) => {
  if (!input) return input;
  return input.split(/(\s+)/).map((segment) => /\s+/.test(segment) ? segment : finalizeClafricaToken(segment)).join("");
};
var INSERT_PALETTE_MAX = 96;
var buildClafricaInsertPalette = () => {
  const unique = /* @__PURE__ */ new Set();
  for (const v of Object.values(Clafrica)) {
    if (typeof v !== "string" || !v) continue;
    if (v.length >= 1 && v.length <= 4) {
      unique.add(v);
    }
  }
  return Array.from(unique).sort((a, b) => a.length - b.length || a.localeCompare(b, "en")).slice(0, INSERT_PALETTE_MAX);
};
var CLAFRICA_INSERT_PALETTE = buildClafricaInsertPalette();
var cleanWord = (word) => {
  return word.trim().toLowerCase().replace(/[’]/g, "'").replace(/^[\/.,!?;:()"/`\s]+|[\/.,!?;:()"/`\s]+$/g, "").replace(/^'+/, "");
};
export {
  CLAFRICA_INSERT_PALETTE,
  Clafrica,
  applyClafricaMapping,
  cleanWord,
  finalizeClafricaInput,
  stripLowToneMarks
};
