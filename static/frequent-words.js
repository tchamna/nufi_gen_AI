const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const wordsBodyEl = document.getElementById("words-body");
const resultsTitleEl = document.getElementById("results-title");
const controlsFormEl = document.getElementById("controls");
const minLettersEl = document.getElementById("min-letters");

const POLYGLOT_DICTIONARY_BASE = "https://african-polyglot.com/dictionary";

function polyglotLookupUrl(word) {
  const url = new URL(POLYGLOT_DICTIONARY_BASE);
  url.searchParams.set("q", word);
  return url.toString();
}

function setStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.classList.toggle("error", Boolean(isError));
}

function readMinLettersFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("min_letters");
  if (!raw) {
    return null;
  }
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) && value >= 1 ? value : null;
}

function updateUrl(minLetters) {
  const url = new URL(window.location.href);
  url.searchParams.set("min_letters", String(minLetters));
  window.history.replaceState({}, "", url);
}

function renderSummary(payload) {
  const items = [
    ["Minimum letters", payload.min_letters],
    ["Matching unique words", payload.matching_unique_words],
    ["Returned", payload.returned],
    ["Total alpha tokens", payload.total_alpha_tokens],
  ];

  summaryEl.innerHTML = "";
  items.forEach(([label, value]) => {
    const card = document.createElement("section");
    card.className = "metric";
    card.innerHTML = `<div class="label">${label}</div><div class="value">${Number(value).toLocaleString()}</div>`;
    summaryEl.appendChild(card);
  });
}

function renderTable(items, minLetters) {
  wordsBodyEl.innerHTML = "";
  resultsTitleEl.textContent = `Top ${items.length} words with at least ${minLetters} letters`;

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

async function loadFrequentWords(minLetters) {
  setStatus("Loading word frequencies...");
  try {
    const response = await fetch(
      `/api/stats/frequent-words?min_letters=${encodeURIComponent(minLetters)}&limit=100`,
    );
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Failed to load frequent words");
    }

    renderSummary(payload);
    renderTable(payload.words || [], payload.min_letters);
    updateUrl(payload.min_letters);
    setStatus("");
  } catch (error) {
    setStatus(error.message || "Failed to load frequent words", true);
  }
}

controlsFormEl.addEventListener("submit", (event) => {
  event.preventDefault();
  const minLetters = Number.parseInt(minLettersEl.value, 10);
  if (!Number.isFinite(minLetters) || minLetters < 1) {
    setStatus("Enter a minimum letter count of at least 1.", true);
    return;
  }
  loadFrequentWords(minLetters);
});

const initialMinLetters = readMinLettersFromUrl() ?? Number.parseInt(minLettersEl.value, 10) ?? 4;
minLettersEl.value = String(initialMinLetters);
loadFrequentWords(initialMinLetters);
