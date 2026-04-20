const sourceTextEl = document.getElementById("sourceText");
const cleanedTextEl = document.getElementById("cleanedText");
const cleanTextButtonEl = document.getElementById("cleanTextButton");
const copyTextButtonEl = document.getElementById("copyTextButton");
const downloadTextButtonEl = document.getElementById("downloadTextButton");
const clearTextButtonEl = document.getElementById("clearTextButton");
const textStatusEl = document.getElementById("textStatus");

const dropzoneEl = document.getElementById("dropzone");
const fileInputEl = document.getElementById("fileInput");
const cleanFileButtonEl = document.getElementById("cleanFileButton");
const fileMetaEl = document.getElementById("fileMeta");
const fileStatusEl = document.getElementById("fileStatus");
let selectedFile = null;

function setStatus(target, message, isError = false) {
  target.textContent = message || "";
  target.classList.toggle("error", Boolean(isError));
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function parseFilenameFromDisposition(headerValue) {
  if (!headerValue) {
    return "cleaned_clean_nufi.txt";
  }
  const utf8Match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) {
    return decodeURIComponent(utf8Match[1]);
  }
  const basicMatch = headerValue.match(/filename="([^"]+)"/i);
  if (basicMatch) {
    return basicMatch[1];
  }
  return "cleaned_clean_nufi.txt";
}

async function cleanText() {
  cleanTextButtonEl.disabled = true;
  setStatus(textStatusEl, "Cleaning text...");
  try {
    const response = await fetch("/api/clean-nufi/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: sourceTextEl.value }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Cleanup failed");
    }
    cleanedTextEl.value = payload.cleaned_text || "";
    setStatus(textStatusEl, "Cleaned text ready.");
  } catch (error) {
    setStatus(textStatusEl, error.message || "Cleanup failed", true);
  } finally {
    cleanTextButtonEl.disabled = false;
  }
}

// Debounce helper to limit frequency of API calls when typing
function debounce(fn, wait) {
  let t = null;
  return (...args) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

// Live-clean as the user types (debounced) so they don't have to click "Clean text"
const debouncedClean = debounce(() => {
  // Only run if there is some text
  if (sourceTextEl && sourceTextEl.value && sourceTextEl.value.trim()) {
    cleanText();
  } else {
    // Clear cleaned output when input is empty
    if (cleanedTextEl) cleanedTextEl.value = "";
    setStatus(textStatusEl, "");
  }
}, 400);

if (sourceTextEl) {
  sourceTextEl.addEventListener("input", debouncedClean);
}

async function copyCleanedText() {
  if (!cleanedTextEl.value) {
    setStatus(textStatusEl, "No cleaned text to copy.", true);
    return;
  }
  try {
    await navigator.clipboard.writeText(cleanedTextEl.value);
    setStatus(textStatusEl, "Cleaned text copied.");
  } catch (_) {
    cleanedTextEl.focus();
    cleanedTextEl.select();
    document.execCommand("copy");
    setStatus(textStatusEl, "Cleaned text copied.");
  }
}

function downloadCleanedText() {
  if (!cleanedTextEl.value) {
    setStatus(textStatusEl, "No cleaned text to download.", true);
    return;
  }
  downloadBlob(new Blob([cleanedTextEl.value], { type: "text/plain;charset=utf-8" }), "cleaned_nufi.txt");
  setStatus(textStatusEl, "Cleaned text downloaded.");
}

function clearText() {
  sourceTextEl.value = "";
  cleanedTextEl.value = "";
  setStatus(textStatusEl, "");
}

function setSelectedFile(file) {
  selectedFile = file || null;
  if (!file) {
    fileMetaEl.textContent = "";
    return;
  }
  const sizeKb = Math.max(1, Math.round(file.size / 1024));
  fileMetaEl.textContent = `Selected file: ${file.name} (${sizeKb} KB)`;
}

async function cleanFile() {
  const file = selectedFile;
  if (!file) {
    setStatus(fileStatusEl, "Choose a .txt or .docx file first.", true);
    return;
  }

  cleanFileButtonEl.disabled = true;
  setStatus(fileStatusEl, `Cleaning ${file.name}...`);
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch("/api/clean-nufi/file", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      let message = "File cleanup failed";
      try {
        const payload = await response.json();
        message = payload.detail || message;
      } catch (_) {
        /* ignore */
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition");
    const filename = parseFilenameFromDisposition(disposition);
    downloadBlob(blob, filename);
    setStatus(fileStatusEl, `Downloaded ${filename}.`);
  } catch (error) {
    setStatus(fileStatusEl, error.message || "File cleanup failed", true);
  } finally {
    cleanFileButtonEl.disabled = false;
  }
}

["dragenter", "dragover"].forEach((eventName) => {
  dropzoneEl.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzoneEl.classList.add("dragover");
  });
});

["dragleave", "dragend", "drop"].forEach((eventName) => {
  dropzoneEl.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzoneEl.classList.remove("dragover");
  });
});

dropzoneEl.addEventListener("drop", (event) => {
  const files = event.dataTransfer?.files;
  if (!files || !files.length) {
    return;
  }
  setSelectedFile(files[0]);
});

dropzoneEl.addEventListener("click", () => fileInputEl.click());
dropzoneEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    fileInputEl.click();
  }
});

fileInputEl.addEventListener("change", () => {
  setSelectedFile((fileInputEl.files && fileInputEl.files[0]) || null);
  setStatus(fileStatusEl, "");
});

cleanTextButtonEl.addEventListener("click", cleanText);
copyTextButtonEl.addEventListener("click", copyCleanedText);
downloadTextButtonEl.addEventListener("click", downloadCleanedText);
clearTextButtonEl.addEventListener("click", clearText);
cleanFileButtonEl.addEventListener("click", cleanFile);
