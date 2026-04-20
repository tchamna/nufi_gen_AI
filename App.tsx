import { useCallback, useEffect, useRef, useState } from "react";
import {
  detectVerb,
  getConjugationDocxUrl,
  loadGroupedConjugation,
  loadGroupedConjugationNegative,
  loadVerbs,
  loadVerbMeta,
  resolveVerb,
  type ConjugateLayoutResponse,
  type DetectVerbResponse,
  type ResolveVerbResponse,
  type WordLayoutGroup,
} from "./api";
import {
  CELL_TRANSLATION_MODAL_TITLE,
  getCellContextualTranslation,
  type CellTranslationResult,
} from "./contextualCellTranslation";
import {
  applyClafricaMapping,
  CLAFRICA_INSERT_PALETTE,
  finalizeClafricaInput,
  stripLowToneMarks,
} from "./clafricaMapping";
import nufiGrammarCover from "./assets/Slide7_nufi_grammaire.png";
import nufiDictionaryCover from "./assets/Nufi_Dictionary.png";
import resulamLogoEgg from "./assets/resulam_logo_egg.png";
import "./App.css";
import "./clafricaInsertPalette.css";
import { LiveVisitors } from "./LiveVisitors";
import { VisitorAnalytics } from "./VisitorAnalytics";

const CLAFRICA_STORAGE_KEY = "nufi-clafrica-enabled";
const NUFI_HEADERS_STORAGE_KEY = "nufi-headers-enabled";
const THEME_STORAGE_KEY = "nufi-theme";
const DOUBLE_SHIFT_MS = 420;

const PAYPAL_DONATE_URL =
  "https://www.paypal.com/donate/?hosted_button_id=JMMGALRZ33WJY";
const AFRICAN_BOOKS_URL = "https://africanlanguagelibrary.tchamna.com/";
const GRAMMAIRE_BAMILEKE_NUFI_URL = "http://bit.ly/grammaire_bamileke_nufi";
const NUFI_GRAMMAR_PAPERBACK_URL = "https://www.amazon.com/dp/1511920408";
const NUFI_GRAMMAR_EBOOK_URL = "https://www.amazon.com/dp/B0865QYPPZ";
const NUFI_GRAMMAR_HARDCOVER_URL = "https://www.amazon.com/dp/B0FQ5G2GFK";
const NUFI_ANDROID_DICTIONARY_URL =
  "https://play.google.com/store/apps/details?id=com.resulam.android.NufiTchamna_nufi_francais_nufi&hl=fr&pli=1";
const HEADER_GLOSS_MAX_LENGTH = 72;
const BASE_TIME_MARKERS = [
  "mɑ̄ lɑ̀",
  "mɑ̌",
  "mɑ̀",
  "kò",
  "fhʉ́",
  "fhʉ̄",
  "kɑ̀",
  "lɑ̀",
  "lɑ̌'",
  "lɑlɑ̌'",
  "lɑ̀lɑ̌'",
  "dɑ̌'",
  "dɑ̀",
  "dɑ̀lɑ̌'",
  "indɑ̄'",
  "ìndɑ̄'",
  "kɑ́lɑ̄'",
  "i",
  "ì",
  "ìndīē",
  "kɑ́",
  "síé",
  "sīē",
  "mam",
  "kom",
] as const;

const TIME_MARKERS = Array.from(
  new Set(BASE_TIME_MARKERS.flatMap((marker) => [marker, stripLowToneMarks(marker)]))
).sort((a, b) => b.length - a.length);
const FUTUR_PROCHE_TIME_MARKERS = Array.from(
  new Set(["i", "ì", "síé", "sīē", "kɑ́"].flatMap((marker) => [marker, stripLowToneMarks(marker)]))
).sort((a, b) => b.length - a.length);
const NUFI_GROUP_TITLE_LABELS: Record<string, string> = {
  "Présent": "Ntié’ ntié’e le",
  "Passé Récent": "Ntie’ē tōh mêndɑ'",
  "Passé": "Ntie’ē tōh",
  "Temps Habituel": "Ntie’ē ghʉ ndiandia",
  "Futur Proche": "Ntie’ē sɑ' mêndɑ'",
  "Futur Lointain": "Ntie’ē sɑ' sʉsʉɑ",
};

const NUFI_COLUMN_HEADER_LABELS: Record<string, string> = {
  "Présent 1": "Ntié’e le",
  "Présent 2": "Ntié’e le",
  "Impératif": "Ghəə̄ngʉ' | Ghəə̄ntɑ̄h",
  "Passé Composé": "Ntie’ē tōh mêndɑ'",
  "Présent accompli": "Ntie’ē tōh mêndɑ'",
  "Passé Récent": "Ntie’ē tōh fɑ́hnzɑ̄",
  "Passé d'hier": "Ntie’ē tōh wāha",
  "Passé (>= 2 jours)": "Ntie’ē tōh līē' pʉ́ɑ́",
  "Passé Lointain": "Ntie’ē tōh tɑ kwaŋ",
  "Présent Habituel": "Ntie’ē ghʉ ndiandia",
  "Présent Habituel 1": "Ntie’ē ghʉ ndiandia",
  "Présent Habituel 2": "Ntie’ē ghʉ ndiandia",
  "Passé Habituel": "Ntie’ē tōh ndiandia",
  "Passé Habituel 1": "Ntie’ē tōh ndiandia",
  "Passé Habituel 2": "Ntie’ē tōh ndiandia",
  "Futur Proche": "Ntie’ē sɑ' mêndɑ'",
  "Futur Lointain": "Ntie’ē sɑ' sʉsʉɑ",
};

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const buildTimeMarkerRegex = (markers: readonly string[]) =>
  new RegExp(`(^|[\\s([{«“"'])(${markers.map(escapeRegex).join("|")})`, "gu");

/** Typographic apostrophe as emitted by the Python backend (U+2019). */
const A9 = "\u2019";

type NegativeParticleContext = {
  groupTitle: string;
  columnHeader: string;
  columnIndex: number;
};

function timeMarkersForContext(contextTitle?: string): readonly string[] {
  if (contextTitle?.toLowerCase().includes("futur proche")) {
    return FUTUR_PROCHE_TIME_MARKERS;
  }
  return TIME_MARKERS;
}

function negativeParticlePatterns(ctx: NegativeParticleContext): string[] {
  const gt = ctx.groupTitle.trim();
  const ch = ctx.columnHeader.trim();
  const ci = ctx.columnIndex;

  const b = [`(bɑ̄)`, `bɑ̄`];

  if (gt === "Présent") {
    if (ch === "Présent 1") {
      return [`sī mɑ̀`, ...b];
    }
    if (ch === "Présent 2") {
      return [`sī kò`, ...b];
    }
    if (ch === "Impératif") {
      return [`Ǒ sì`, `Pɑ̌h sì`, `Pěn sì`, ...b];
    }
  }

  if (gt === "Passé Récent") {
    if (ch === "Présent accompli") {
      return [`kɑ̀${A9}`, `kɑ̀'`, ...b];
    }
    if (ch === "Passé Récent") {
      return [`kɑ̀${A9} fhʉ̄`, `kɑ̀' fhʉ̄`, ...b];
    }
  }

  if (gt === "Passé") {
    if (ch === "Passé d'hier") {
      return [`kɑ̀ sì`, ...b];
    }
    if (ch === "Passé (>= 2 jours)") {
      return [`dɑ̀ sì`, `lɑ̀ sì`, ...b];
    }
    if (ch === "Passé Lointain") {
      return [`dɑ̀ sì lɑ̄${A9}`, `lɑ̀ sì lɑ̄${A9}`, `dɑ̀ sì lɑ̄'`, `lɑ̀ sì lɑ̄'`, ...b];
    }
  }

  if (gt === "Futur Proche") {
    if (ci === 0) {
      return [`sī kɑ́`, ...b];
    }
    if (ci === 1) {
      return [`sī ì`, ...b];
    }
    if (ci === 2) {
      return [`sī sīē`, ...b];
    }
  }

  if (gt === "Futur Lointain") {
    if (ci === 0) {
      return [`sī kɑ́lɑ̄${A9}`, `sī kɑ́lɑ̄'`, ...b];
    }
    if (ci === 1) {
      return [`sī ìndɑ̄${A9}`, `sī ìndɑ̄'`, ...b];
    }
    if (ci === 2) {
      return [`sī ìndīē`, ...b];
    }
  }

  if (gt === "Temps Habituel") {
    if (ch === "Présent Habituel") {
      return [`sǐ${A9}`, `sǐ'`, ...b];
    }
    if (ch === "Passé Habituel") {
      return [`dɑ̌' sì'`, `lɑ̌' sì'`, ...b];
    }
  }

  return [];
}

function collectNonOverlappingSpans(
  text: string,
  patterns: readonly string[]
): Array<{ start: number; end: number }> {
  const uniq = Array.from(new Set(patterns.filter((p) => p.length > 0))).sort(
    (a, b) => b.length - a.length || a.localeCompare(b)
  );
  const claimed = new Array<boolean>(text.length).fill(false);
  const spans: Array<{ start: number; end: number }> = [];
  for (const p of uniq) {
    let from = 0;
    while (from <= text.length - p.length) {
      const i = text.indexOf(p, from);
      if (i === -1) {
        break;
      }
      let ok = true;
      for (let j = i; j < i + p.length; j++) {
        if (claimed[j]) {
          ok = false;
          break;
        }
      }
      if (ok) {
        for (let j = i; j < i + p.length; j++) {
          claimed[j] = true;
        }
        spans.push({ start: i, end: i + p.length });
        from = i + p.length;
      } else {
        from = i + 1;
      }
    }
  }
  spans.sort((a, b) => a.start - b.start);
  return spans;
}

/**
 * When "Strip low tones" is on, displayed cell text is passed through stripLowToneMarks
 * (removes U+0300 grave). Particle patterns must include those variants or highlights
 * disappear for graves (e.g. sī mɑ̀ → sī mɑ); affirmative TIME_MARKERS already
 * duplicates markers this way.
 */
function expandParticlePatternsForDisplay(
  patterns: readonly string[],
  stripTonesEnabled: boolean
): string[] {
  if (!stripTonesEnabled) {
    return Array.from(new Set(patterns));
  }
  const out = new Set<string>();
  for (const p of patterns) {
    out.add(p);
    const stripped = stripLowToneMarks(p);
    if (stripped !== p) {
      out.add(stripped);
    }
  }
  return Array.from(out);
}

function renderHighlightedSpans(
  text: string,
  spans: Array<{ start: number; end: number }>
): React.ReactNode {
  if (spans.length === 0) {
    return text;
  }
  const nodes: React.ReactNode[] = [];
  let cursor = 0;
  spans.forEach((s, index) => {
    if (cursor < s.start) {
      nodes.push(text.slice(cursor, s.start));
    }
    nodes.push(
      <span key={`time-marker-${index}-${s.start}`} className="time-marker">
        {text.slice(s.start, s.end)}
      </span>
    );
    cursor = s.end;
  });
  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }
  return <>{nodes}</>;
}

function renderHighlightedTimeMarkers(
  text: string,
  contextTitle?: string
): React.ReactNode {
  const matches = Array.from(text.matchAll(buildTimeMarkerRegex(timeMarkersForContext(contextTitle))));
  if (matches.length === 0) {
    return text;
  }

  const nodes: React.ReactNode[] = [];
  let cursor = 0;

  matches.forEach((match, index) => {
    const start = match.index ?? 0;
    const boundary = match[1] ?? "";
    const marker = match[2] ?? "";
    const markerStart = start + boundary.length;

    if (cursor < markerStart) {
      nodes.push(text.slice(cursor, markerStart));
    }

    nodes.push(
      <span key={`time-marker-${index}-${markerStart}`} className="time-marker">
        {marker}
      </span>
    );

    cursor = markerStart + marker.length;
  });

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return <>{nodes}</>;
}

function renderNegativeParticleHighlights(
  text: string,
  ctx: NegativeParticleContext,
  stripTonesEnabled: boolean
): React.ReactNode {
  const raw = negativeParticlePatterns(ctx);
  if (raw.length === 0) {
    return renderHighlightedTimeMarkers(text, ctx.groupTitle);
  }
  const patterns = expandParticlePatternsForDisplay(raw, stripTonesEnabled);
  const spans = collectNonOverlappingSpans(text, patterns);
  if (spans.length === 0) {
    return renderHighlightedTimeMarkers(text, ctx.groupTitle);
  }
  return renderHighlightedSpans(text, spans);
}

type ConjugationCellContext =
  | string
  | {
      groupTitle: string;
      columnHeader: string;
      columnIndex: number;
    };

function wordTableStyleToAttr(style: string | undefined): string {
  const s = (style ?? "Light Grid Accent 5").trim().toLowerCase();
  return s.replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

function formatGroupHeading(
  groupTitle: string,
  verb: React.ReactNode,
  translatedVerb: string | null | undefined
): React.ReactNode {
  const gloss = translatedVerb?.trim().replace(/\s*,\s*/g, "; ");
  const shortGloss =
    gloss && gloss.length > HEADER_GLOSS_MAX_LENGTH
      ? `${gloss.slice(0, HEADER_GLOSS_MAX_LENGTH).trimEnd()}...`
      : gloss;
  return shortGloss ? (
    <>
      {groupTitle} ({verb}: {shortGloss})
    </>
  ) : (
    <>
      {groupTitle} ({verb})
    </>
  );
}

function capitalizeForDisplay(text: string): string {
  if (!text) return text;
  return `${text.charAt(0).toLocaleUpperCase()}${text.slice(1)}`;
}

function displayToneGroupLabel(group: string | null | undefined): string | null {
  if (!group) return null;
  const value = group.trim();
  if (!value || value === "—") return null;
  const lowered = value.toLowerCase();
  if (lowered === "haut") return "Groupe 1";
  if (lowered === "moyen") return "Groupe 2";
  return value;
}

function normalizeFrenchColumnHeader(label: string): string {
  if (label === "Présent 1" || label === "Présent 2") {
    return "Present";
  }
  if (label === "Passé Habituel 1" || label === "Passé Habituel 2") {
    return "Passé Habituel";
  }
  return label;
}

function getUiLanguage(): "fr" | "en" {
  if (typeof document !== "undefined") {
    const lang = document.documentElement.lang?.trim().toLowerCase();
    if (lang.startsWith("fr")) return "fr";
    if (lang.startsWith("en")) return "en";
  }
  if (typeof navigator !== "undefined") {
    const lang = navigator.language?.trim().toLowerCase();
    if (lang.startsWith("fr")) return "fr";
    if (lang.startsWith("en")) return "en";
  }
  return "en";
}

function formatDatabaseNotice(verb: string): string {
  const displayVerb = verb
    ? `${verb.charAt(0).toLocaleUpperCase()}${verb.slice(1)}`
    : verb;

  if (getUiLanguage() === "fr") {
    return `${displayVerb} n’est pas trouvé dans notre base de données, mais s’il devait être conjugué, il le serait comme ci-dessous…`;
  }

  return `${displayVerb} is not found in our database, but if it were to be conjugated, it would be like below ...`;
}

function getHeroSubtitle(): string {
  if (getUiLanguage() === "fr") {
    return "Cherchez un verbe (français, anglais ou fe'éfě'e) et cliquez sur chaque phrase pour voir la traduction automatique.";
  }
  return "Search for a verb (French, English, or Fe'éfě'e) and click each cell to see the automatic translation.";
}

function getDocxDownloadLabel(): string {
  return getUiLanguage() === "fr" ? "Télécharger Word" : "Download Word";
}

export default function App() {
  const [currentPathname, setCurrentPathname] = useState(() =>
    typeof window === "undefined" ? "/" : window.location.pathname
  );
  const [verb, setVerb] = useState("");
  const [clafricaEnabled, setClafricaEnabled] = useState(() => {
    try {
      if (typeof localStorage === "undefined") {
        return true;
      }
      const stored = localStorage.getItem(CLAFRICA_STORAGE_KEY);
      return stored === null ? true : stored === "1";
    } catch {
      return true;
    }
  });
  const [nufiHeadersEnabled, setNufiHeadersEnabled] = useState(() => {
    try {
      if (typeof localStorage === "undefined") {
        return false;
      }
      return localStorage.getItem(NUFI_HEADERS_STORAGE_KEY) === "1";
    } catch {
      return false;
    }
  });
  const [headerGlossLanguage, setHeaderGlossLanguage] = useState<"fr" | "en">("fr");
  const [stripTonesEnabled, setStripTonesEnabled] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    try {
      if (typeof localStorage === "undefined") {
        return "light";
      }
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      return stored === "dark" ? "dark" : "light";
    } catch {
      return "light";
    }
  });
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metaLine, setMetaLine] = useState<string | null>(null);
  const [databaseNotice, setDatabaseNotice] = useState<string | null>(null);
  const [polarity, setPolarity] = useState<"affirmative" | "negative">("affirmative");
  const [wordLayoutAff, setWordLayoutAff] = useState<ConjugateLayoutResponse | null>(null);
  const [wordLayoutNeg, setWordLayoutNeg] = useState<ConjugateLayoutResponse | null>(null);
  const [resolveChoices, setResolveChoices] = useState<ResolveVerbResponse["candidates"]>([]);
  const [resolvePrompt, setResolvePrompt] = useState<string | null>(null);
  const [detectText, setDetectText] = useState("");
  const [detectResult, setDetectResult] = useState<DetectVerbResponse | null>(null);
  const [detectError, setDetectError] = useState<string | null>(null);
  const [detectLoading, setDetectLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialConjugationLoaded, setInitialConjugationLoaded] = useState(false);
  const lastShiftDownRef = useRef(0);
  const verbInputRef = useRef<HTMLInputElement>(null);
  const detectInputRef = useRef<HTMLInputElement>(null);

  type CellTranslationPayload = { nufi: string } & CellTranslationResult;
  const [cellTranslation, setCellTranslation] = useState<CellTranslationPayload | null>(null);

  useEffect(() => {
    setReady(true);
  }, []);

  useEffect(() => {
    if (!cellTranslation) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setCellTranslation(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cellTranslation]);

  useEffect(() => {
    const onPopState = () => {
      setCurrentPathname(window.location.pathname);
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Shift") {
        if (e.repeat) return;
        const now = Date.now();
        if (
          lastShiftDownRef.current > 0 &&
          now - lastShiftDownRef.current < DOUBLE_SHIFT_MS
        ) {
          e.preventDefault();
          setClafricaEnabled((v) => !v);
          lastShiftDownRef.current = 0;
        } else {
          lastShiftDownRef.current = now;
        }
        return;
      }
      lastShiftDownRef.current = 0;
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(CLAFRICA_STORAGE_KEY, clafricaEnabled ? "1" : "0");
    } catch {
      /* private mode */
    }
  }, [clafricaEnabled]);

  useEffect(() => {
    try {
      localStorage.setItem(NUFI_HEADERS_STORAGE_KEY, nufiHeadersEnabled ? "1" : "0");
    } catch {
      /* private mode */
    }
  }, [nufiHeadersEnabled]);

  useEffect(() => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      /* private mode */
    }
  }, [theme]);

  const applyInputOptions = useCallback(
    (raw: string, finalizeClafrica = false) => {
      if (!clafricaEnabled) {
        return raw;
      }
      return finalizeClafrica
        ? finalizeClafricaInput(raw)
        : applyClafricaMapping(raw, { preserveAmbiguousTrailingToken: true });
    },
    [clafricaEnabled]
  );

  const renderConjugationText = useCallback(
    (value: string | null | undefined, context?: ConjugationCellContext): React.ReactNode => {
      if (!value) return "—";
      const text = stripTonesEnabled ? stripLowToneMarks(value) : value;
      let groupTitle: string | undefined;
      if (typeof context === "string") {
        groupTitle = context;
      } else if (context && typeof context === "object") {
        groupTitle = context.groupTitle;
      }
      if (
        polarity === "negative" &&
        context &&
        typeof context === "object" &&
        "columnHeader" in context
      ) {
        return renderNegativeParticleHighlights(
          text,
          {
            groupTitle: context.groupTitle,
            columnHeader: context.columnHeader ?? "",
            columnIndex: context.columnIndex ?? 0,
          },
          stripTonesEnabled
        );
      }
      return renderHighlightedTimeMarkers(text, groupTitle);
    },
    [stripTonesEnabled, polarity]
  );

  const displayGroupTitle = useCallback(
    (label: string) =>
      nufiHeadersEnabled ? (NUFI_GROUP_TITLE_LABELS[label] ?? label) : label,
    [nufiHeadersEnabled]
  );

  const displayColumnHeader = useCallback(
    (label: string) => {
      const normalizedLabel = normalizeFrenchColumnHeader(label);
      return nufiHeadersEnabled
        ? (NUFI_COLUMN_HEADER_LABELS[label] ?? normalizedLabel)
        : normalizedLabel;
    },
    [nufiHeadersEnabled]
  );

  const navigateTo = useCallback((path: string) => {
    if (typeof window === "undefined") return;
    if (window.location.pathname === path) return;
    window.history.pushState({}, "", path);
    setCurrentPathname(path);
  }, []);

  const onVerbChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setVerb(applyInputOptions(e.target.value));
    },
    [applyInputOptions]
  );

  const onVerbBlur = useCallback(() => {
    setVerb((current) => applyInputOptions(current, true));
  }, [applyInputOptions]);

  const onDetectTextChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setDetectText(applyInputOptions(e.target.value));
    },
    [applyInputOptions]
  );

  const onDetectBlur = useCallback(() => {
    setDetectText((current) => applyInputOptions(current, true));
  }, [applyInputOptions]);

  const insertIntoVerb = useCallback(
    (fragment: string) => {
      const el = verbInputRef.current;
      const start = el?.selectionStart ?? verb.length;
      const end = el?.selectionEnd ?? verb.length;
      const combined = verb.slice(0, start) + fragment + verb.slice(end);
      const mapped = applyInputOptions(combined);
      const newPos = start + (mapped.length - verb.length);
      setVerb(mapped);
      requestAnimationFrame(() => {
        if (el && document.body.contains(el)) {
          el.focus();
          el.setSelectionRange(newPos, newPos);
        }
      });
    },
    [applyInputOptions, verb]
  );

  const insertIntoDetect = useCallback(
    (fragment: string) => {
      const el = detectInputRef.current;
      const start = el?.selectionStart ?? detectText.length;
      const end = el?.selectionEnd ?? detectText.length;
      const combined = detectText.slice(0, start) + fragment + detectText.slice(end);
      const mapped = applyInputOptions(combined);
      const newPos = start + (mapped.length - detectText.length);
      setDetectText(mapped);
      requestAnimationFrame(() => {
        if (el && document.body.contains(el)) {
          el.focus();
          el.setSelectionRange(newPos, newPos);
        }
      });
    },
    [applyInputOptions, detectText]
  );

  const runConjugation = useCallback(
    async (rawVerb: string, options?: { skipResolve?: boolean; syncInput?: boolean }) => {
      const v = applyInputOptions(rawVerb, true).trim();
      if (!v) {
        setError("Entrez un verbe.");
        return;
      }
      if (options?.syncInput !== false) {
        setVerb(v);
      }
      setLoading(true);
      setError(null);
      setMetaLine(null);
      setDatabaseNotice(null);
      setWordLayoutAff(null);
      setWordLayoutNeg(null);
      setResolveChoices([]);
      setResolvePrompt(null);

      try {
        const resolved = options?.skipResolve ? null : await resolveVerb(v);
        if (resolved?.ambiguous && resolved.candidates.length > 1) {
          setResolveChoices(resolved.candidates);
          setResolvePrompt(
            `Plusieurs verbes correspondent à « ${v} ». Choisissez le verbe Nufī à conjuguer.`
          );
          return;
        }
        const resolvedVerb = resolved?.resolved_verb ?? v;
        if (options?.syncInput !== false) {
          setVerb(resolvedVerb);
        }

        if (!options?.skipResolve && resolved === null) {
          setDatabaseNotice(formatDatabaseNotice(resolvedVerb));
        }

        const meta = await loadVerbMeta(resolvedVerb);
        if (meta && (options?.skipResolve || resolved !== null)) {
          const displayVerb = meta.verb
            ? `${meta.verb.charAt(0).toLocaleUpperCase()}${meta.verb.slice(1)}`
            : meta.verb;
          const toneGroupLabel = displayToneGroupLabel(meta.group);
          setMetaLine(
            toneGroupLabel ? `${displayVerb} · ${toneGroupLabel}` : displayVerb
          );
        }
        const [layout, layoutNeg] = await Promise.all([
          loadGroupedConjugation(resolvedVerb),
          loadGroupedConjugationNegative(resolvedVerb),
        ]);
        setWordLayoutAff(layout);
        setWordLayoutNeg(layoutNeg);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    },
    [applyInputOptions]
  );

  const onNegativeTabClick = useCallback(() => {
    setPolarity("negative");
    const v = wordLayoutAff?.verb?.trim();
    if (!v || wordLayoutNeg) {
      return;
    }
    void loadGroupedConjugationNegative(v).then((neg) => {
      if (neg) {
        setWordLayoutNeg(neg);
      }
    });
  }, [wordLayoutAff?.verb, wordLayoutNeg]);

  const runDetect = useCallback(
    async (rawText: string) => {
      const text = applyInputOptions(rawText, true).trim();
      if (!text) {
        setDetectError("Entrez un mot à tester.");
        setDetectResult(null);
        return;
      }
      setDetectText(text);
      setDetectLoading(true);
      setDetectError(null);
      try {
        setDetectResult(await detectVerb(text));
      } catch (err) {
        setDetectError(err instanceof Error ? err.message : String(err));
        setDetectResult(null);
      } finally {
        setDetectLoading(false);
      }
    },
    [applyInputOptions]
  );

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await runConjugation(verb);
    },
    [runConjugation, verb]
  );

  const isDetectorPage = currentPathname.startsWith("/verb-detector");

  useEffect(() => {
    if (!ready || isDetectorPage || initialConjugationLoaded) {
      return;
    }

    let cancelled = false;
    void (async () => {
      try {
        const verbs = await loadVerbs();
        if (cancelled || !Array.isArray(verbs) || verbs.length === 0) {
          return;
        }
        const randomEntry = verbs[Math.floor(Math.random() * verbs.length)];
        if (!randomEntry?.verb) {
          return;
        }
        setInitialConjugationLoaded(true);
        await runConjugation(randomEntry.verb, { syncInput: false });
      } catch {
        setInitialConjugationLoaded(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [initialConjugationLoaded, isDetectorPage, ready, runConjugation]);

  const displayWordLayout =
    polarity === "negative" ? wordLayoutNeg : wordLayoutAff;

  const showPolarityTabs =
    Boolean(wordLayoutAff || wordLayoutNeg || loading || resolveChoices.length > 0);

  const onConjCellClick = useCallback(
    (
      cell: string,
      layout: ConjugateLayoutResponse,
      g: WordLayoutGroup,
      rowIndex: number,
      columnIndex: number
    ) => {
      const t = cell.trim();
      if (!t || t === "—") return;
      setCellTranslation({
        nufi: t,
        ...getCellContextualTranslation({
          polarity: layout.polarity ?? "affirmative",
          styleKey: g.style_key || g.title,
          columnIndex,
          columnHeader: g.headers[columnIndex] ?? "",
          rowIndex,
          cellText: t,
          frenchGloss: layout.translated_verb,
          englishGloss: layout.translated_verb_en ?? null,
        }),
      });
    },
    []
  );

  return (
    <div className="app" data-theme={theme} data-polarity={polarity}>
      <section className="hero">
        <div className="hero-topbar">
          <div className="hero-brand">
            <img
              className="hero-brand-logo"
              src={resulamLogoEgg}
              alt="Resulam logo"
              loading="eager"
              decoding="async"
            />
          </div>

          <nav className="site-nav" aria-label="Main navigation">
            <a
              href="/"
              className={`site-nav-link ${!isDetectorPage ? "site-nav-link--active" : ""}`}
              onClick={(e) => {
                e.preventDefault();
                navigateTo("/");
              }}
            >
              Conjugation
            </a>
            <a
              href={AFRICAN_BOOKS_URL}
              className="site-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              African Books
            </a>
            <a
              href={PAYPAL_DONATE_URL}
              className="site-nav-link"
              target="_blank"
              rel="noopener noreferrer sponsored"
            >
              PayPal
            </a>
            <button
              type="button"
              className="theme-toggle"
              onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              title={theme === "dark" ? "Light mode" : "Dark mode"}
            >
              <span className="theme-toggle-icon" aria-hidden="true">
                {theme === "dark" ? "☀" : "☽"}
              </span>
            </button>
          </nav>
        </div>

        {!isDetectorPage ? (
          <>
            <div className="hero-text-content">
              <h1 className="hero-title">Lə́ə́ghəə̄ Fe'éfě'e</h1>
              <p className="hero-desc">{getHeroSubtitle()}</p>
            </div>
            
            <form className="controls" onSubmit={onSubmit}>
              <div className="controls-toggles">
                <div
                  className="clafrica-switch-row"
                  title="Raccourcis Clafrica (af, eu, …). Double Maj pour activer / désactiver."
                >
                  <span className="clafrica-switch-label" id="clafrica-switch-label">
                    Clafrica
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={clafricaEnabled}
                    aria-labelledby="clafrica-switch-label"
                    disabled={!ready}
                    className={`clafrica-switch ${clafricaEnabled ? "clafrica-switch--on" : ""}`}
                    onClick={() => setClafricaEnabled((v) => !v)}
                  >
                    <span className="clafrica-switch-track" aria-hidden>
                      <span className="clafrica-switch-thumb" />
                    </span>
                  </button>
                </div>

                <div
                  className="clafrica-switch-row"
                  title="Masquer seulement le ton bas dans les résultats affichés."
                >
                  <span className="clafrica-switch-label" id="strip-tones-switch-label">
                    Nufī Clean
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={stripTonesEnabled}
                    aria-labelledby="strip-tones-switch-label"
                    disabled={!ready}
                    className={`clafrica-switch ${stripTonesEnabled ? "clafrica-switch--on" : ""}`}
                    onClick={() => setStripTonesEnabled((v) => !v)}
                  >
                    <span className="clafrica-switch-track" aria-hidden>
                      <span className="clafrica-switch-thumb" />
                    </span>
                  </button>
                </div>

                <div
                  className="clafrica-switch-row"
                  title="Afficher les en-têtes des tableaux en Nufī."
                >
                  <span className="clafrica-switch-label" id="nufi-headers-switch-label">
                    Nufī Headers
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={nufiHeadersEnabled}
                    aria-labelledby="nufi-headers-switch-label"
                    disabled={!ready}
                    className={`clafrica-switch ${nufiHeadersEnabled ? "clafrica-switch--on" : ""}`}
                    onClick={() => setNufiHeadersEnabled((v) => !v)}
                  >
                    <span className="clafrica-switch-track" aria-hidden>
                      <span className="clafrica-switch-thumb" />
                    </span>
                  </button>
                </div>

                <div
                  className="clafrica-switch-row"
                  title="Afficher les traductions des en-têtes en anglais."
                >
                  <span className="clafrica-switch-label" id="english-gloss-switch-label">
                    English Gloss
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={headerGlossLanguage === "en"}
                    aria-labelledby="english-gloss-switch-label"
                    disabled={!ready}
                    className={`clafrica-switch ${headerGlossLanguage === "en" ? "clafrica-switch--on" : ""}`}
                    onClick={() =>
                      setHeaderGlossLanguage((current) => (current === "en" ? "fr" : "en"))
                    }
                  >
                    <span className="clafrica-switch-track" aria-hidden>
                      <span className="clafrica-switch-thumb" />
                    </span>
                  </button>
                </div>
              </div>

              <div className="controls-main">
                <input
                  ref={verbInputRef}
                  type="text"
                  value={verb}
                  onChange={onVerbChange}
                  onBlur={onVerbBlur}
                  placeholder="Ex. ndēn, manger, to eat …"
                  autoComplete="off"
                  aria-label="Verbe"
                  disabled={!ready}
                />
                <button type="submit" disabled={loading || !ready}>
                  {loading ? "…" : "Lə̄ə̄"}
                </button>
              </div>
              {clafricaEnabled ? (
                <div
                  className="clafrica-insert-palette-wrap"
                  aria-label="Insert Nufī characters"
                >
                  <p className="clafrica-insert-palette-hint">
                    Tap a character to insert at the cursor (shortcuts like af, eu still apply).
                  </p>
                  <div className="clafrica-insert-palette">
                    {CLAFRICA_INSERT_PALETTE.map((ch) => (
                      <button
                        key={ch}
                        type="button"
                        className="clafrica-insert-char"
                        disabled={!ready}
                        title={`Insert ${ch}`}
                        onMouseDown={(e) => {
                          e.preventDefault();
                        }}
                        onClick={() => insertIntoVerb(ch)}
                      >
                        {ch}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </form>
            {error ? <p className="status-err">{error}</p> : null}
            {databaseNotice ? <p className="status-err status-err-center">{databaseNotice}</p> : null}
            {resolvePrompt ? <p className="resolve-prompt">{resolvePrompt}</p> : null}
            {resolveChoices.length ? (
              <div className="resolve-choice-list">
                {resolveChoices.map((choice) => (
                  <button
                    key={`${choice.verb}-${choice.translated_verb ?? ""}`}
                    type="button"
                    className="resolve-choice"
                    onClick={() => {
                      void runConjugation(choice.verb, { skipResolve: true });
                    }}
                  >
                    <span className="resolve-choice-verb">{renderConjugationText(choice.verb)}</span>
                    <span className="resolve-choice-gloss">
                      {choice.translated_verb ?? "—"}
                    </span>
                  </button>
                ))}
              </div>
            ) : null}
            {metaLine && !loading ? <p className="meta">{metaLine}</p> : null}
          </>
        ) : (
          <>
            <p className="detector-hero-copy">
              Test whether a form is treated as a verb by the current prefix and tone rule.
            </p>
            <div className="controls-toggles detector-hero-toggles">
              <div
                className="clafrica-switch-row"
                title="Raccourcis Clafrica (af, eu, …). Double Maj pour activer / désactiver."
              >
                <span className="clafrica-switch-label" id="detector-clafrica-switch-label">
                  Clafrica
                </span>
                <button
                  type="button"
                  role="switch"
                  aria-checked={clafricaEnabled}
                  aria-labelledby="detector-clafrica-switch-label"
                  disabled={!ready}
                  className={`clafrica-switch ${clafricaEnabled ? "clafrica-switch--on" : ""}`}
                  onClick={() => setClafricaEnabled((v) => !v)}
                >
                  <span className="clafrica-switch-track" aria-hidden>
                    <span className="clafrica-switch-thumb" />
                  </span>
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {isDetectorPage ? (
        <section className="card detector-card">
          <div className="detector-form">
            <input
              ref={detectInputRef}
              value={detectText}
              onChange={onDetectTextChange}
              onBlur={onDetectBlur}
              onKeyDown={(e) => {
                if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing) {
                  return;
                }
                e.preventDefault();
                void runDetect(e.currentTarget.value);
              }}
              placeholder="Ex. nzɑ̄, nden, ngén mfɑ́'"
              autoComplete="off"
              aria-label="Texte à détecter"
              disabled={!ready}
            />
            <button
              type="button"
              disabled={detectLoading || !ready}
              onClick={() => {
                void runDetect(detectText);
              }}
            >
              {detectLoading ? "…" : "Test"}
            </button>
          </div>
          {clafricaEnabled ? (
            <div className="clafrica-insert-palette-wrap" aria-label="Insert Nufī characters">
              <p className="clafrica-insert-palette-hint">
                Tap a character to insert at the cursor (shortcuts like af, eu still apply).
              </p>
              <div className="clafrica-insert-palette">
                {CLAFRICA_INSERT_PALETTE.map((ch) => (
                  <button
                    key={ch}
                    type="button"
                    className="clafrica-insert-char"
                    disabled={!ready}
                    title={`Insert ${ch}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                    }}
                    onClick={() => insertIntoDetect(ch)}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {detectError ? <p className="status-err">{detectError}</p> : null}
          {detectResult ? (
            <div className="detector-result">
              <p>
                <strong>{detectResult.classification === "verb" ? "Verb" : "Non-verb"}</strong>
                {" · "}
                {renderConjugationText(detectResult.input)}
              </p>
              <p>{detectResult.reason}</p>
              <p>
                Prefixes:{" "}
                {detectResult.matched_prefixes.length
                  ? detectResult.matched_prefixes.join(", ")
                  : "—"}
              </p>
            </div>
          ) : null}
        </section>
      ) : (
        <>
          {showPolarityTabs ? (
            <div
              className="polarity-tabs"
              role="tablist"
              aria-label="Polarité de la conjugaison"
            >
              <button
                type="button"
                role="tab"
                id="tab-affirmative"
                aria-selected={polarity === "affirmative"}
                aria-controls="conj-results-panel"
                className={`polarity-tab ${polarity === "affirmative" ? "polarity-tab--active" : ""}`}
                onClick={() => setPolarity("affirmative")}
              >
                Affirmative
              </button>
              <span className="polarity-tabs-sep" aria-hidden>
                |
              </span>
              <button
                type="button"
                role="tab"
                id="tab-negative"
                aria-selected={polarity === "negative"}
                aria-controls="conj-results-panel"
                className={`polarity-tab ${polarity === "negative" ? "polarity-tab--active" : ""}`}
                onClick={onNegativeTabClick}
              >
                Negative
              </button>
            </div>
          ) : null}

          <section
            id="conj-results-panel"
            className="grid word-doc-layout"
            aria-live="polite"
            role="tabpanel"
            aria-labelledby={polarity === "negative" ? "tab-negative" : "tab-affirmative"}
          >
            {displayWordLayout
              ? displayWordLayout.groups.map((g, i) => {
                  const n = Math.max(1, g.headers.length);
                  return (
                    <article key={i} className="card word-group">
                      <h2
                        className="conj-group-title"
                        data-word-style={wordTableStyleToAttr(g.word_table_style)}
                      >
                        {formatGroupHeading(
                          displayGroupTitle(g.title),
                          renderConjugationText(capitalizeForDisplay(displayWordLayout.verb)),
                          headerGlossLanguage === "en"
                            ? (displayWordLayout.translated_verb_en ?? displayWordLayout.translated_verb)
                            : displayWordLayout.translated_verb
                        )}
                      </h2>
                      <div
                        className="conj-table-shell"
                        data-word-style={wordTableStyleToAttr(g.word_table_style)}
                      >
                        <table
                          className="conj-word"
                          data-word-style={wordTableStyleToAttr(g.word_table_style)}
                        >
                          <thead>
                            <tr>
                              {(g.headers.length ? g.headers : ["—"]).map((h, hi) => (
                                <th key={hi} className="conj-th-sub">
                                  {displayColumnHeader(h)}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {g.rows.length === 0 ? (
                              <tr>
                                <td className="muted" colSpan={n}>
                                  —
                                </td>
                              </tr>
                            ) : (
                              g.rows.map((row, ri) => (
                                <tr key={ri}>
                                  {row.map((cell, ci) => (
                                    <td
                                      key={ci}
                                      className="conj-cell-clickable"
                                      title={`${CELL_TRANSLATION_MODAL_TITLE} (FR / EN) — cliquer`}
                                      onClick={() => {
                                        if (!displayWordLayout || !cell) return;
                                        onConjCellClick(
                                          cell,
                                          displayWordLayout,
                                          g,
                                          ri,
                                          ci
                                        );
                                      }}
                                    >
                                      {cell
                                        ? renderConjugationText(cell, {
                                            groupTitle: g.title,
                                            columnHeader: g.headers[ci] ?? "",
                                            columnIndex: ci,
                                          })
                                        : "—"}
                                    </td>
                                  ))}
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </article>
                  );
                })
              : polarity === "negative" && !wordLayoutNeg && wordLayoutAff ? (
                <p className="polarity-unavailable">
                  Conjugaison négative indisponible : le serveur doit exposer au moins{" "}
                  <code className="polarity-unavailable-code">GET /conjugate-layout/negative</code>{" "}
                  (recommandé) ou{" "}
                  <code className="polarity-unavailable-code">GET /conjugate-negative</code>
                  . Redémarrez l’API, reconstruisez le front, puis rechargez la page (Ctrl+F5).
                </p>
              ) : null}
          </section>

          {displayWordLayout && !loading ? (
            <div className="result-actions result-actions-end">
              <a
                className="download-docx-link"
                href={getConjugationDocxUrl(
                  displayWordLayout.verb,
                  stripTonesEnabled,
                  nufiHeadersEnabled,
                  headerGlossLanguage,
                  polarity
                )}
              >
                <span className="download-docx-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" role="img" focusable="false">
                    <rect x="7.5" y="4" width="12.5" height="16" rx="2.4" fill="#2b579a" />
                    <path d="M14.5 4v4h5" fill="#5b86c5" />
                    <path
                      d="M3 7.2A2.2 2.2 0 0 1 5.2 5h7.1v14H5.2A2.2 2.2 0 0 1 3 16.8z"
                      fill="#185abd"
                    />
                    <path
                      d="M5.4 9.1h1.7l1 4.7 1.2-4.7h1.4l1.1 4.7 1-4.7h1.6l-1.9 7.1h-1.4l-1.2-4.5-1.2 4.5H7.3z"
                      fill="#ffffff"
                    />
                  </svg>
                </span>
                {getDocxDownloadLabel()}
              </a>
            </div>
          ) : null}

          <section className="card book-card">
            <div className="book-card-media">
              <a
                href={NUFI_GRAMMAR_PAPERBACK_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="book-cover-link"
                aria-label="Open the paperback listing for La grammaire des langues bamilekes : cas du Nufī"
              >
                <img
                  className="book-cover"
                  src={nufiGrammarCover}
                  alt="Cover of La grammaire des langues bamilekes : cas du Nufī"
                  loading="eager"
                  decoding="async"
                />
              </a>
            </div>
            <div className="book-card-body">
              <h2>Reference Book</h2>
              <p className="book-title">La grammaire des langues bamilekes : cas du Nufī</p>
              <p>Language: Nufī</p>
              <p>
                Authors:{" "}
                <span className="author-name-highlight">Shck Tchamna</span>,{" "}
                Shck Deukam
              </p>
              <div className="book-links">
                <a href={NUFI_GRAMMAR_PAPERBACK_URL} target="_blank" rel="noopener noreferrer">
                  Paperback
                </a>
                <a href={NUFI_GRAMMAR_EBOOK_URL} target="_blank" rel="noopener noreferrer">
                  eBook
                </a>
                <a href={NUFI_GRAMMAR_HARDCOVER_URL} target="_blank" rel="noopener noreferrer">
                  Hardcover
                </a>
              </div>
            </div>
            <aside className="book-card-side">
              <a
                href={NUFI_ANDROID_DICTIONARY_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="dictionary-card-link"
                aria-label="Open the Nufī Android dictionary on Google Play"
              >
                <img
                  className="dictionary-cover"
                  src={nufiDictionaryCover}
                  alt="Nufī Android dictionary on Google Play"
                  loading="eager"
                  decoding="async"
                />
                <div className="dictionary-card-copy">
                  <span className="dictionary-card-eyebrow">Android Dictionary</span>
                  <strong>Nufī Dictionary</strong>
                  <span>Ouvrir sur Google Play</span>
                </div>
              </a>
            </aside>
          </section>
        </>
      )}

      <footer className="site-footer">
        <p className="site-footer-note">
          Cette application a été conçue et développée par{" "}
          <span className="author-name-highlight">Shck Tchamna</span> à partir
          d’un ouvrage de grammaire rédigé en 2015. Les règles de conjugaison qui
          y sont présentées ont servi de base à la modélisation linguistique
          intégrée dans cette application.
        </p>
        <p>
          Toute observation relative à d’éventuelles erreurs ou incohérences peut
          être transmise à{" "}
          <a href="mailto:contact@resulam.com">contact@resulam.com</a>. Nous
          encourageons également les utilisateurs à consulter l’ouvrage de
          référence afin d’approfondir leur compréhension de la structure
          grammaticale des langues bamiléké :{" "}
          <a
            href={GRAMMAIRE_BAMILEKE_NUFI_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            {GRAMMAIRE_BAMILEKE_NUFI_URL}
          </a>
        </p>
        <LiveVisitors pathname={currentPathname} />
        <VisitorAnalytics pathname={currentPathname} />
      </footer>

      <a
        href={PAYPAL_DONATE_URL}
        className="floating-paypal-button"
        target="_blank"
        rel="noopener noreferrer sponsored"
        aria-label="Faire un don via PayPal"
        title="Faire un don via PayPal"
      >
        <span className="floating-paypal-icon" aria-hidden="true">
          <svg viewBox="0 0 40 40" role="img" focusable="false">
            <rect x="0" y="0" width="40" height="40" rx="12" fill="#ffffff" />
            <path
              d="M16.5 9.5h7.2c4.1 0 6.6 2 6.1 5.6-.6 4.1-3.9 6-8.1 6h-2.8l-1 6.2h-4.2l2.9-17.8Z"
              fill="#003087"
            />
            <path
              d="M20.7 12.4h5.2c3 0 4.6 1.4 4.2 4-.5 3-2.9 4.4-6.2 4.4H21l-.9 5.6h-3.7l2.2-14Z"
              fill="#009cde"
              opacity="0.95"
            />
          </svg>
        </span>
        <span className="floating-paypal-label">Donate</span>
      </a>

      {cellTranslation ? (
        <div
          className="cell-trans-backdrop"
          onClick={() => setCellTranslation(null)}
          role="presentation"
        >
          <div
            className="cell-trans-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cell-trans-title"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="cell-trans-close"
              onClick={() => setCellTranslation(null)}
              aria-label="Fermer"
            >
              ×
            </button>
            <h3 id="cell-trans-title">{CELL_TRANSLATION_MODAL_TITLE}</h3>
            <p className="cell-trans-nufi">
              <code>{cellTranslation.nufi}</code>
            </p>
            <h4 className="cell-trans-h4">Français</h4>
            <ul className="cell-trans-list">
              {cellTranslation.linesFr.map((line, i) => (
                <li key={`fr-${i}`}>{line}</li>
              ))}
            </ul>
            <h4 className="cell-trans-h4">English</h4>
            <ul className="cell-trans-list">
              {cellTranslation.linesEn.map((line, i) => (
                <li key={`en-${i}`}>{line}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
}
