import { applyClafricaMapping, finalizeClafricaInput } from "./clafricaMapping.js";

const CLAFRICA_STORAGE_KEY = "nufi-clafrica-enabled";
const AUDIO_TOGGLE_STORAGE_KEY = "nufi-audio-enabled";
const DEFAULT_SEED = "ng\u0251\u030c y\u00fa'";
const keyboardSuggestCache = new Map();
let currentAudio = null;

const seedEl = document.getElementById("seed");
const clafricaEl = document.getElementById("clafrica");
const clafricaHintEl = document.getElementById("clafrica-hint");
const audioToggleEl = document.getElementById("audioToggle");
const audioStatusEl = document.getElementById("audio-status");
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

try {
  audioToggleEl.checked = localStorage.getItem(AUDIO_TOGGLE_STORAGE_KEY) === "1";
} catch (_) {
  audioToggleEl.checked = false;
}

clafricaHintEl.hidden = !clafricaEl.checked;
seedEl.value = DEFAULT_SEED;

function setAudioStatus(message, isError = false) {
  audioStatusEl.textContent = message || "";
  audioStatusEl.classList.toggle("error-text", Boolean(isError));
}

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

async function playSuggestionAudio(word) {
  if (!audioToggleEl.checked || !word) {
    return;
  }

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  const audio = new Audio(`/api/audio/${encodeURIComponent(word)}`);
  currentAudio = audio;
  setAudioStatus(`Playing ${word}...`);

  audio.addEventListener(
    "ended",
    () => {
      if (currentAudio === audio) {
        currentAudio = null;
      }
      setAudioStatus("");
    },
    { once: true }
  );

  audio.addEventListener(
    "error",
    () => {
      if (currentAudio === audio) {
        currentAudio = null;
      }
      setAudioStatus(`Audio unavailable for ${word}.`, true);
    },
    { once: true }
  );

  try {
    await audio.play();
  } catch (_) {
    if (currentAudio === audio) {
      currentAudio = null;
    }
    setAudioStatus(`Audio unavailable for ${word}.`, true);
  }
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
    const probability = suggestion.score ?? suggestion.probability ?? 0;
    const word = suggestion.word;
    button.textContent = word;
    button.title = typeof probability === "number" ? `p ~= ${probability.toFixed(4)}` : "";
    button.addEventListener("click", async () => {
      appendSuggestion(word);
      await playSuggestionAudio(word);
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

audioToggleEl.addEventListener("change", () => {
  try {
    localStorage.setItem(AUDIO_TOGGLE_STORAGE_KEY, audioToggleEl.checked ? "1" : "0");
  } catch (_) {
    /* private mode */
  }
  if (!audioToggleEl.checked) {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    setAudioStatus("");
  }
});

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
