# Next-word prediction: what we built, and what beats n-grams

This document summarizes the **n-gram–based** pipeline currently in this repo, its **limits**, and **state-of-the-art** alternatives for **next-token / next-word** prediction—especially for **low-resource** languages like Nufi.

---

## 1. What we implemented (n-gram stack)

Roughly, the API and keyboard call **`suggest_next_words`** in `nufi_model.py`, backed by a **combined n-gram model** (orders 2–5) stored in `data/Nufi/Nufi_language_model_api.pickle`.

| Area | What we did |
|------|-------------|
| **Corpus** | Lines cleaned with **`clean_text`** (Bana → standard, ton bas, punctuation). Latin **“N.B.” / “N. B.”** markers stripped **before** tokenization so they do not become spurious **`n` → `b`** bigrams. |
| **Inference** | **Legacy tone / bare-vowel** fallbacks so user input still matches older pickle keys. |
| **Display** | **`clean_text`** on each suggested word; **merge** rows that collapse to the same string after normalization (no duplicate chips like two `lah`). |
| **Artifacts** | Drop the pathological case where context is only **`n`** and the model still returns **only** **`b`** (leftover from **N.B.** in old pickles). |
| **Ranking** | **Interpolated backoff** for *suggestions only*: blend distributions from **longest context → shorter contexts** (e.g. trigram + bigram + unigram). When the longest context is **sparse** (few distinct next words), **stronger weight** on the **unigram after the last token** so rare but plausible continuations are not hidden entirely. |
| **Generation** | **`generate_*`** still uses **longest-match** n-grams (not the interpolated blend), so story completion behavior stays closer to classic n-gram generation. |

**Important limitation (inherent to n-grams):** the model predicts the **immediate next token** after the last word. It does **not** skip particles or predict a salient word several steps ahead. If your corpus has `… zǎ ō ō ō … lè bɑ̄ …`, the **immediate** successor after `zǎ` is often **`ō`**, not **`bɑ̄`**, even if **`bɑ̄`** feels “next” in a clause-level sense.

---

## 2. Why n-grams are a weak ceiling here

- **Data sparsity:** For rare contexts `(w_{i-2}, w_{i-1}, w_i)`, counts collapse; backoff helps but cannot invent generalizations.
- **No morphology:** Word-level n-grams treat `bɑ̄` and `bɑ́` as unrelated unless the data repeats both.
- **Long range:** Anything beyond a few words is invisible.
- **Keyboard UX:** You want **smooth** rankings from **partial** phrases; pure counts are noisy.

N-grams remain **valid baselines**: fast, small, debuggable, and deployable everywhere. They are **not** SOTA for open-domain language modeling.

---

## 3. State of the art for next-token prediction

**SOTA** for general text is **neural language models** trained on large corpora: today this means **Transformer decoders** (GPT-style) or **encoder–decoder** models, with **subword tokenization** (SentencePiece, BPE, Unigram LM).

Typical stack:

1. **Tokenization:** SentencePiece or similar on **Nufi + related languages** (or multilingual vocabulary) so rare words are rare **pieces**, not OOV.
2. **Architecture:** Small **decoder-only Transformer** (e.g. tens of millions of parameters) for **server** inference; or **distilled / quantized** models for **edge**.
3. **Training objective:** Causal LM (predict next subword). Optional **auxiliary** losses (not required for keyboard).
4. **Low-resource mitigations:**  
   - **Multilingual pretrain** then **Nufi-only finetune**  
   - **Data augmentation** (back-translation, careful synthetic text)  
   - **Regularization** and **early stopping** on a held-out Nufi set  

**Research adjacent to “keyboard LM”:** large commercial keyboards use **neural** models with **personalization** and **federated learning**; published details are sparse, but the pattern is **RNN/LSTM → Transformer** over **subwords**, with **server-side** scoring.

**Classical ML alternative (still not “neural SOTA” but better than raw word n-grams):** **KenLM** (modified Kneser–Ney) on **subwords**—strong **backoff** and **smoothing**, still **count-based**, easier than training Transformers but **no deep semantics**.

---

## 4. Recommended direction for *this* project

| Goal | Practical approach |
|------|---------------------|
| **Better next-word list on the API** | Finetune a **small causal LM** (e.g. **Llama-class** tiny open weights, or **GPT-2–sized** open model) on **Nufi text**, or train a **small Transformer from scratch** if data is small (use **subwords**). Expose **`POST /api/keyboard/suggest`** with **`log P(next \| context)`** from the neural model. |
| **Keep latency / cost low** | **Distill** to a smaller model, **quantize** (int8), batch requests, **cache** prefixes. |
| **Android keyboard** | **Option A:** Same HTTP API (neural backend). **Option B:** **ONNX Runtime** or **TensorFlow Lite** with a **tiny** model (heavier engineering). |
| **Hybrid (often best in production)** | **Neural** top-k reranking + **n-gram** or **lexicon** constraints for **OOV** / **tone** / **blocked** forms. |

---

## 5. Minimal implementation roadmap (neural path)

1. **Normalize text** with the same **`clean_text`** rules (or train on **raw** then normalize at inference—pick one and stay consistent).
2. **Train SentencePiece** on the Nufi corpus (vocab 4k–16k).
3. **Train** a small **causal Transformer** (e.g. **nanoGPT-style** or **Hugging Face** `Trainer` with a small config).
4. **Evaluate** with **perplexity** on held-out Nufi and **manual** keyboard trials.
5. **Replace** `suggest_next_words` **or** add **`/api/keyboard/suggest-neural`** that returns top-k tokens; keep n-gram endpoint as fallback.
6. **Deploy** behind the same FastAPI app; add **GPU** optional for throughput.

---

## 6. Summary

- **Current repo:** **Word-level combined n-grams** + **cleaning**, **N.B. stripping**, **dedupe**, **artifact guards**, and **interpolated backoff** for suggestions—solid **baseline**, not SOTA.
- **SOTA:** **Subword neural LMs** (Transformers), optionally **multilingual** pretrain + **Nufi** finetune.
- **Best “instead of n-grams”** for quality: **train or finetune a small causal LM** and serve **top-k next subwords**; keep n-grams or rules only if you need **deterministic** fallbacks.

This file is documentation only; it does not change runtime behavior. To pursue the neural path, add a training script and a separate model artifact, then wire a new suggestion endpoint.
