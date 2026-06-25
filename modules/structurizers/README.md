# Module 2: Structurizer

This module separates the main presentation segment from the Q&A session in transcripts. It formats the Q&A segment with clear speaker labels (`[Question]`, `[Answer]`, `[Follow-up]`) while strictly retaining the exact original wording.

---

## 1. Directory Structure

- **[input/](input/)**: Contains raw transcript `.txt` files. This directory is **symlinked** directly to `modules/transcribers/output/`.
- **[output/](output/)**: Generates two output text files:
  - `<name>_presentation.txt`: Contains the main presentation segment.
  - `<name>_q_and_a.txt`: Contains the structured and labeled Q&A session.

---

## 2. Engine & API Details

This module uses `GeminiStructurizer` (configured in `.env`):
- **Model**: `gemini-flash-lite-latest` (recommended on the free tier to prevent rate limit limits).
- **Constraints**: Guided by Pydantic schema generation configuration to return structured JSON. The prompt strictly instructs the LLM not to change, paraphrase, summarize, or edit any words from the original transcript.
- **Rate Limit Safeguards**: The runner includes a built-in 20-second cooldown delay between files to prevent exceeding the Gemini Free Tier's 5 Requests Per Minute (RPM) quota.

---

## 3. Usage

Run this module from the project root directory.

### Process All Unprocessed Transcripts
Processes transcripts in the `input/` folder that do not already have structured outputs in `output/`:

```bash
python modules/structurizers/run.py
```

### Process or Force Re-run Specific File(s)
You can target a specific transcript file directly, which overrides the skip checks and forces a re-run:

```bash
python modules/structurizers/run.py agoda.txt
```
