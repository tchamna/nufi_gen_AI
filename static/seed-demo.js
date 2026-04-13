import { applyClafricaMapping, finalizeClafricaInput } from "./clafricaMapping.js";

const CLAFRICA_STORAGE_KEY = "nufi-clafrica-enabled";
const DEFAULT_SEED = "ng\u0251\u030c y\u00fa'";
const keyboardSuggestCache = new Map();

const seedEl = document.getElementById("seed");
const clafricaEl = document.getElementById("clafrica");
const clafricaHintEl = document.getElementById("clafrica-hint");
const nEl = document.getElementById("n");
const numCandidatesEl = document.getElementById("numCandidates");
const maxTokensEl = document.getElementById("maxTokens");
const temperatureEl = document.getElementById("temperature");
const matchLimitEl = document.getElementById("matchLimit");
const goEl = document.getElementById("go");
const suggestEl = document.getElementById("suggest");
const suggestionsEl = document.getElementById("suggestions");

try {
  const stored = localStorage.getItem(CLAFRICA_STORAGE_KEY);
  clafricaEl.checked = stored === null ? true : stored === "1";
} catch (_) {
  clafricaEl.checked = true;
}
clafricaHintEl.hidden = !clafricaEl.checked;

seedEl.value = DEFAULT_SEED;

function readGenerateSettings() {
  return {
    text: seedEl.value,
    n: parseInt(nEl.value || "4", 10),
    num_candidates: parseInt(numCandidatesEl.value || "5", 10),
    max_tokens: parseInt(maxTokensEl.value || "40", 10),
    temperature: parseFloat(temperatureEl.value || "1"),
    match_limit: parseInt(matchLimitEl.value || "8", 10),
    max_sources_per_match: 3,
  };
}

function readKeyboardSuggestSettings() {
  return {
    text: seedEl.value,
    n: parseInt(nEl.value || "4", 10),
    limit: 8,
  };
}

function appendSuggestion(word) {
  const current = seedEl.value.trim();
  seedEl.value = current ? `${current} ${word}` : word;
}

function renderSuggestions(payload, errorMessage) {
  suggestionsEl.innerHTML = "";
  if (errorMessage) {
    const li = document.createElement("li");
    li.className = "error-text";
    li.textContent = errorMessage;
    suggestionsEl.appendChild(li);
    return;
  }

  if (!payload.suggestions || !payload.suggestions.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "No suggestions for this seed.";
    suggestionsEl.appendChild(li);
    return;
  }

  payload.suggestions.forEach((suggestion) => {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "suggestion";
    const p = suggestion.score ?? suggestion.probability ?? 0;
    const word = suggestion.word;
    button.textContent = word;
    button.title = typeof p === "number" ? `p ≈ ${p.toFixed(4)}` : "";
    button.addEventListener("click", async () => {
      appendSuggestion(word);
      await fetchKeyboardSuggestions();
    });
    li.appendChild(button);
    suggestionsEl.appendChild(li);
  });
}

async function fetchKeyboardSuggestions() {
  const payload = readKeyboardSuggestSettings();
  const cacheKey = JSON.stringify(payload);
  if (keyboardSuggestCache.has(cacheKey)) {
    renderSuggestions(keyboardSuggestCache.get(cacheKey), null);
    return;
  }

  suggestEl.disabled = true;
  try {
    const resp = await fetch("/api/keyboard/suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || "Suggestion request failed");
    }
    keyboardSuggestCache.set(cacheKey, data);
    if (keyboardSuggestCache.size > 50) {
      const oldestKey = keyboardSuggestCache.keys().next().value;
      keyboardSuggestCache.delete(oldestKey);
    }
    renderSuggestions(data, null);
  } catch (error) {
    renderSuggestions({ suggestions: [], used_context: 0 }, error.message);
  } finally {
    suggestEl.disabled = false;
  }
}

async function generate() {
  const payload = readGenerateSettings();
  goEl.disabled = true;
  try {
    const resp = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || "Request failed");
    }
    keyboardSuggestCache.clear();
    await fetchKeyboardSuggestions();
  } catch (error) {
    renderSuggestions({ suggestions: [], used_context: 0 }, error.message);
  } finally {
    goEl.disabled = false;
  }
}

function applyLiveClafricaIfEnabled() {
  if (!clafricaEl.checked) return;
  const next = applyClafricaMapping(seedEl.value, {
    preserveAmbiguousTrailingToken: true,
  });
  if (next !== seedEl.value) {
    seedEl.value = next;
  }
}

function onSeedEdited() {
  applyLiveClafricaIfEnabled();
  keyboardSuggestCache.clear();
  window.clearTimeout(window.__suggestTimer);
  window.__suggestTimer = window.setTimeout(fetchKeyboardSuggestions, 250);
}

goEl.addEventListener("click", generate);
suggestEl.addEventListener("click", fetchKeyboardSuggestions);

clafricaEl.addEventListener("change", () => {
  clafricaHintEl.hidden = !clafricaEl.checked;
  try {
    localStorage.setItem(CLAFRICA_STORAGE_KEY, clafricaEl.checked ? "1" : "0");
  } catch (_) {
    /* private mode */
  }
  if (clafricaEl.checked) {
    seedEl.value = finalizeClafricaInput(seedEl.value);
  }
  keyboardSuggestCache.clear();
  fetchKeyboardSuggestions();
});

// input: primary; keyup/paste: fallback when input does not fire (some browsers / IME)
seedEl.addEventListener("input", onSeedEdited);
seedEl.addEventListener("keyup", () => {
  applyLiveClafricaIfEnabled();
});
seedEl.addEventListener("paste", () => {
  window.setTimeout(onSeedEdited, 0);
});

applyLiveClafricaIfEnabled();
renderSuggestions({ suggestions: [], used_context: 0 }, null);
fetchKeyboardSuggestions();
