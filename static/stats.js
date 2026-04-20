const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const cloudEl = document.getElementById("cloud");
const topAlphaBodyEl = document.getElementById("top-alpha-body");
const topAllBodyEl = document.getElementById("top-all-body");

function setStatus(message, isError = false) {
  statusEl.textContent = message || "";
  statusEl.classList.toggle("error", Boolean(isError));
}

function renderSummary(payload) {
  const items = [
    ["Unique words", payload.unique_word_count],
    ["Unique alpha words", payload.unique_alpha_word_count],
    ["Total tokens", payload.total_tokens],
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

function renderCloud(items) {
  cloudEl.innerHTML = "";
  if (!items.length) {
    cloudEl.textContent = "No word data available.";
    return;
  }

  const maxCount = Math.max(...items.map((item) => item.count));
  const minCount = Math.min(...items.map((item) => item.count));
  const spread = Math.max(1, maxCount - minCount);

  items.forEach((item, index) => {
    const span = document.createElement("span");
    const size = 16 + Math.round(((item.count - minCount) / spread) * 32);
    const hue = 150 - (index % 7) * 12;
    span.textContent = item.word;
    span.style.fontSize = `${size}px`;
    span.style.fontWeight = item.count > maxCount * 0.55 ? "700" : "500";
    span.style.color = `hsl(${hue} 70% 28%)`;
    span.title = `${item.word}: ${item.count}`;
    cloudEl.appendChild(span);
  });
}

function renderTable(target, items) {
  target.innerHTML = "";
  if (!items.length) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="3">No data available.</td>`;
    target.appendChild(row);
    return;
  }

  const maxCount = Math.max(...items.map((item) => item.count));
  items.slice(0, 30).forEach((item) => {
    const row = document.createElement("tr");
    const width = Math.max(2, Math.round((item.count / maxCount) * 100));
    row.innerHTML = `
      <td>${item.word}</td>
      <td>${item.count.toLocaleString()}</td>
      <td class="bar-cell">
        <div class="bar-wrap">
          <div class="bar" style="width:${width}%"></div>
        </div>
      </td>
    `;
    target.appendChild(row);
  });
}

async function loadStats() {
  setStatus("Loading stats...");
  try {
    const response = await fetch("/api/stats/lexical");
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Failed to load stats");
    }

    renderSummary(payload);
    renderCloud(payload.top_alpha_preview || []);
    renderTable(topAlphaBodyEl, payload.top_alpha_words || []);
    renderTable(topAllBodyEl, payload.top_words || []);
    setStatus("");
  } catch (error) {
    setStatus(error.message || "Failed to load stats", true);
  }
}

loadStats();
