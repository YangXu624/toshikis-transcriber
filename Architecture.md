# Architecture Design Document: AI Session Capture & Summarisation Tool

This document outlines the architectural design, directory dependency flow, responsibilities, and extension mechanisms for the AI Session Capture & Summarisation Tool.

---

## 1. Architectural Principles

This application adheres to **Clean Architecture** and **SOLID** principles:

* **Dependency Inversion**: High-level business logic (e.g. the orchestrator and runners) does not depend on low-level implementation details (Whisper, Gemini, Local Filesystem). Instead, both depend on abstract interfaces.
* **Modular Segregation**: The pipeline is broken into three distinct stages (Transcription, Structurization, Summarization). Each stage acts as an independent module that can be run, configured, and tested in isolation.
* **Separation of Concerns**: Core orchestration, domain representation, configuration management, and third-party library adapters are isolated in distinct directory structures.
* **Dynamic Adapter Registry**: Adapters are registered at runtime using decorators, making swapping providers (e.g., local Whisper vs. cloud Gemini) or adding new providers completely plug-and-play.

---

## 2. Directory Layout & Pipeline Flow

The workflow is decoupled into three sequential modules inside the `modules/` directory. Downstream inputs link to upstream outputs via directory symlinks.

```
┌───────────────────────────────────────────────┐
│              modules/transcribers             │
│  - Input: Raw audio (.mp3, .wav, .m4a)        │
│  - Adapter: FasterWhisperTranscriber          │
│  - Output: Raw transcripts (.txt)             │
└──────────────┬────────────────────────────────┘
               │
               ▼ (Symlink Directory Link)
┌───────────────────────────────────────────────┐
│             modules/structurizers             │
│  - Input: Raw transcripts (.txt)              │
│  - Adapter: GeminiStructurizer                │
│  - Output: Separated Presentation & Q&A       │
│            (<name>_presentation.txt,          │
│             <name>_q_and_a.txt)               │
└──────────────┬────────────────────────────────┘
               │
               ▼ (Symlink Directory Link)
┌───────────────────────────────────────────────┐
│              modules/summarizers              │
│  - Input: Q&A transcripts (<name>_q_and_a.txt)│
│  - Adapter: GeminiSummarizer                  │
│  - Output: Structured Plain Text & JSON       │
│            (<name>_summary.txt,               │
│             <name>_summary.json)              │
└───────────────────────────────────────────────┘
```

### Component Code Organization:
```text
project/
│
├── core/
│   ├── orchestrator.py      # Pipeline orchestrator coordinating the end-to-end flow
│   ├── factory.py           # Factory instantiating adapters based on config
│   ├── registry.py          # Decoupled registry mapping strings to adapter classes
│   └── interfaces.py        # Abstract interfaces (BaseTranscriber, BaseSummarizer, BaseStorage)
│
├── domain/
│   ├── models.py            # Rich data models (Session, Transcript, Summary)
│   ├── exceptions.py        # Domain-specific custom exceptions
│   └── types.py             # Reusable type definitions
│
├── modules/
│   ├── transcribers/        # Module 1: Whisper engine & CLI runner
│   ├── structurizers/       # Module 2: Gemini formatting engine & CLI runner
│   └── summarizers/         # Module 3: Gemini summarization engine & CLI runner
│
├── config/
│   ├── settings.py          # Pydantic configuration settings & parsing
│   └── config.yaml          # Main YAML configuration file
│
├── tests/                   # Target test suites for unit and integration testing
│
└── .env                     # Local environment keys & overrides
```

---

## 3. Communication & Data Flow

High-level domain models (`Transcript`, `Summary`, `Session`) serve as the common language across architectural boundaries.

```
 [ CLI Runner / Orchestrator ]
             │
             ▼
   [ core/interfaces.py ] ◄─────── [ modules/* ] (Concrete Adapters implement interfaces)
             │
             ▼
   [ domain/models.py ] (Domain data structures flow across boundaries)
```

1. **Bootstrapping**: The CLI runner/orchestrator loads configurations via `config/settings.py` and queries the `AdapterFactory`.
2. **Adapter Instantiation**: The `AdapterFactory` instantiates concrete adapter classes (e.g. `GeminiStructurizer`) using their registered string identifiers and injects them.
3. **Execution & Boundary Translation**: The runner triggers the adapters. The adapters translate the third-party response format into standard domain models (e.g., maps API response JSON to domain `Summary`), shielding the core code from API changes.

---

## 4. Key Engineering Implementations

### A. Symlink Synchronization
To run the modules individually without manual copying, the `input/` folder of each downstream module is a symbolic link to the upstream module's `output/` folder:
- `modules/structurizers/input` -> `../transcribers/output`
- `modules/summarizers/input` -> `../structurizers/output`

### B. Smart CLI Argument Filtering
To prevent hitting API rate limits or wasting GPU/CPU computation, the runner scripts support optional command-line filtering:
- If run without arguments:
  - Iterates over all files in the `input/` directory.
  - Automatically checks `output/` and skips files that have already been processed.
- If run with target filenames as arguments (e.g. `python modules/structurizers/run.py agoda.txt`):
  - Filters processing to match only the specified filenames.
  - Skips the already-processed check to force a re-run of the target files.

### C. Rate Limit & Cost Mitigation
- **Cooldown Delays**: Built-in 20-second sleep intervals in the API-driven loops prevent triggering Gemini's Free Tier Rate Limits (RPM).
- **Model Aliasing**: The adapters automatically map default configurations to `gemini-flash-lite-latest` (1.5 Flash alias) rather than experimental models to leverage higher daily request quotas.
