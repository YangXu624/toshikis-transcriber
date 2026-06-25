# Module 3: Summarizer

This module analyzes structured Q&A sessions and generates executive summaries. It is constrained to summarize **only** the answers provided during Q&A sessions, ignoring the questions and the main presentation section.

---

## 1. Directory Structure

- **[input/](input/)**: Contains speaker-labeled `*_q_and_a.txt` files. This directory is **symlinked** directly to `modules/structurizers/output/`.
- **[output/](output/)**: Generates two output summary formats:
  - `<name>_summary.txt`: A plain-text document with sections for Summary, Key Points, Action Items, and Topics.
  - `<name>_summary.json`: A structured JSON file containing the keys: `content`, `key_points`, `action_items`, and `topics`.

---

## 2. Engine & Prompt Guidelines

This module uses `GeminiSummarizer` (configured in `.env`):
- **Model**: `gemini-flash-lite-latest` (recommended on the free tier to prevent rate limit limits).
- **Core Constraint**: The summarizer focuses strictly on capturing and condensing the information provided inside `[Answer]` blocks, ignoring the questions themselves and any main presentation context.
- **Pydantic Schemas**: Enforces a strict response schema to cleanly structure findings into bullet points and topics.

---

## 3. Usage

Run this module from the project root directory.

### Process All Unprocessed Q&A Transcripts
Processes all structured Q&A files in `input/` that do not already have summary files in `output/`:

```bash
python modules/summarizers/run.py
```

### Process or Force Re-run Specific File(s)
Process a specific file, bypassing any exist/skip checks in the output directory:

```bash
python modules/summarizers/run.py agoda_q_and_a.txt
```
