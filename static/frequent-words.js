const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const wordsBodyEl = document.getElementById("words-body");
const resultsTitleEl = document.getElementById("results-title");
const controlsFormEl = document.getElementById("controls");
const minLettersEl = document.getElementById("min-letters");
const maxLettersEl = document.getElementById("max-letters");

const POLYGLOT_DICTIONARY_BASE = "https://african-polyglot.com/dictionary";
const LETTER_COUNT_MIN = 1;
const LETTER_COUNT_MAX = 32;

function polyglotLookupUrl(word) {
  const url = new URL(POLYGLOT_DICTIONARY_BASE);
  url.searchParams.set("q", word);
  return url.toString();
}

function setStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.classList.toggle("error", Boolean(isError));
}

function parseLetterCount(raw) {
  if (raw === null || raw === undefined || raw === "") {
    return null;
  }
  const value = Number.parseInt(String(raw), 10);
  if (!Number.isFinite(value) || value < LETTER_COUNT_MIN || value > LETTER_COUNT_MAX) {
    return null;
  }
  return value;
}

function readMinLettersFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return parseLetterCount(params.get("min_letters"));
}

function readMaxLettersFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return parseLetterCount(params.get("max_letters"));
}

function updateUrl(minLetters, maxLetters) {
  const url = new URL(window.location.href);
  url.searchParams.set("min_letters", String(minLetters));
  if (maxLetters === null) {
    url.searchParams.delete("max_letters");
  } else {
    url.searchParams.set("max_letters", String(maxLetters));
  }
  window.history.replaceState({}, "", url);
}

function formatLetterRange(minLetters, maxLetters) {
  if (maxLetters === null || maxLetters === undefined) {
    return `at least ${minLetters} letters`;
  }
  if (minLetters === maxLetters) {
    return `exactly ${minLetters} letters`;
  }
  return `${minLetters}–${maxLetters} letters`;
}

function renderSummary(payload) {
  const items = [
    ["Minimum letters", payload.min_letters],
    ["Maximum letters", payload.max_letters ?? "No limit"],
    ["Matching unique words", payload.matching_unique_words],
    ["Returned", payload.returned],
    ["Total alpha tokens", payload.total_alpha_tokens],
  ];

  summaryEl.innerHTML = "";
  items.forEach(([label, value]) => {
    const card = document.createElement("section");
    card.className = "metric";
    const displayValue =
      typeof value === "number" ? Number(value).toLocaleString() : String(value);
    card.innerHTML = `<div class="label">${label}</div><div class="value">${displayValue}</div>`;
    summaryEl.appendChild(card);
  });
}

function renderTable(items, minLetters, maxLetters) {
  wordsBodyEl.innerHTML = "";
  resultsTitleEl.textContent = `Top ${items.length} words with ${formatLetterRange(
    minLetters,
    maxLetters,
  )}`;

  if (!items.length) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="6">No words matched this threshold.</td>`;
    wordsBodyEl.appendChild(row);
    return;
  }

  const maxCount = Math.max(...items.map((item) => item.count));
  items.forEach((item) => {
    const row = document.createElement("tr");
    const width = Math.max(2, Math.round((item.count / maxCount) * 100));
    const lookupUrl = polyglotLookupUrl(item.word);
    row.innerHTML = `
      <td>${item.rank}</td>
      <td class="word">${item.word}</td>
      <td>${item.letter_count}</td>
      <td>${item.count.toLocaleString()}</td>
      <td>
        <a
          class="lookup-link"
          href="${lookupUrl}"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Look up meaning of ${item.word} in African Polyglot"
        >Meaning</a>
      </td>
      <td class="bar-cell">
        <div class="bar-wrap">
          <div class="bar" style="width:${width}%"></div>
        </div>
      </td>
    `;
    wordsBodyEl.appendChild(row);
  });
}

function validateLetterCounts(minLetters, maxLetters) {
  if (!Number.isFinite(minLetters) || minLetters < LETTER_COUNT_MIN || minLetters > LETTER_COUNT_MAX) {
    return `Enter a minimum letter count between ${LETTER_COUNT_MIN} and ${LETTER_COUNT_MAX}.`;
  }
  if (maxLetters !== null) {
    if (!Number.isFinite(maxLetters) || maxLetters < LETTER_COUNT_MIN || maxLetters > LETTER_COUNT_MAX) {
      return `Enter a maximum letter count between ${LETTER_COUNT_MIN} and ${LETTER_COUNT_MAX}, or leave it blank.`;
    }
    if (minLetters > maxLetters) {
      return "Minimum letters must be less than or equal to maximum letters.";
    }
  }
  return null;
}

async function loadFrequentWords(minLetters, maxLetters) {
  setStatus("Loading word frequencies...");
  try {
    const params = new URLSearchParams({
      min_letters: String(minLetters),
      limit: "100",
    });
    if (maxLetters !== null) {
      params.set("max_letters", String(maxLetters));
    }

    const response = await fetch(`/api/stats/frequent-words?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Failed to load frequent words");
    }

    renderSummary(payload);
    renderTable(payload.words || [], payload.min_letters, payload.max_letters ?? null);
    updateUrl(payload.min_letters, payload.max_letters ?? null);
    setStatus("");
  } catch (error) {
    setStatus(error.message || "Failed to load frequent words", true);
  }
}

controlsFormEl.addEventListener("submit", (event) => {
  event.preventDefault();
  const minLetters = Number.parseInt(minLettersEl.value, 10);
  const maxLettersRaw = maxLettersEl.value.trim();
  const maxLetters = maxLettersRaw === "" ? null : Number.parseInt(maxLettersRaw, 10);
  const validationError = validateLetterCounts(minLetters, maxLetters);
  if (validationError) {
    setStatus(validationError, true);
    return;
  }
  loadFrequentWords(minLetters, maxLetters);
});

const initialMinLetters = readMinLettersFromUrl() ?? Number.parseInt(minLettersEl.value, 10) ?? 4;
const initialMaxLetters = readMaxLettersFromUrl();
minLettersEl.value = String(initialMinLetters);
maxLettersEl.value = initialMaxLetters === null ? "" : String(initialMaxLetters);
loadFrequentWords(initialMinLetters, initialMaxLetters);
