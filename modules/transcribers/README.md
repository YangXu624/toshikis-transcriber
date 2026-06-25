# Module 1: Transcriber

This module transcribes raw audio files using local, offline speech-to-text models.

---

## 1. Directory Structure

- **[input/](input/)**: Place your raw audio files here (e.g., `.mp3`, `.wav`, or `.m4a`).
- **[output/](output/)**: Generated plain text transcripts are saved here as `.txt` files.

---

## 2. Engine & Model Details

This module uses `FasterWhisperTranscriber` (under the `faster_whisper` provider configured in `.env`):
- **Model**: `large-v3-turbo` (providing the best balance of speed, low memory footprint, and high accuracy for accented speech).
- **Device**: Automatic CPU/GPU determination.
- **Language**: Forced to English (`en`) to prevent misdetection of regional accents.
- **Brand Context Prompt**: Automatically injects a brand spelling context prompt: `"Agoda, Eco Voyage, Binjai Consulting Group, solo travelers, Ago Local, travel bookers."` to prevent spelling degradation of custom product names.

---

## 3. Usage

Run this module from the project root directory.

### Process All Unprocessed Audio Files
Checks the `input/` folder, and transcribes all audio files that do not already have a corresponding `.txt` transcript in the `output/` folder:

```bash
python modules/transcribers/run.py
```

### Process or Force Re-run Specific File(s)
You can target one or more files specifically. This bypasses the already-processed skip check:

```bash
python modules/transcribers/run.py agoda.mp3
```
