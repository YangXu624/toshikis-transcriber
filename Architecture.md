# Architecture Design Document: AI Session Capture & Summarisation Tool

This document outlines the architectural design, dependency flow, responsibilities, and extension mechanisms for the AI Session Capture & Summarisation Tool.

## 1. Architectural Principles

This application adheres to **Clean Architecture** and **SOLID** principles:

* **Dependency Inversion**: High-level business logic (the pipeline orchestrator) does not depend on low-level implementation details (Whisper, Gemini, Local Filesystem). Instead, both depend on abstract interfaces.
* **Separation of Concerns**: Core orchestration, domain representation, configuration management, and third-party library adapters are isolated in distinct directory structures.
* **Single Responsibility**: Each module, class, and method has a single, well-defined purpose. For example, adapters only manage communication with third-party libraries and map data models; they do not control pipeline workflow.
* **Constructor-Based Dependency Injection**: Concrete adapters are instantiated at the application root (`main.py`) and injected into the pipeline orchestrator's constructor. Singletons and global states are avoided to guarantee thread safety and ease of unit testing.

---

## 2. Component Design & Directory Structure

```text
project/
│
├── app/
│   └── main.py              # Application entrypoint (bootstrapping and execution)
│
├── core/
│   ├── orchestrator.py      # Coordinates pipeline steps (Capture -> Transcribe -> Summarize -> Archive)
│   ├── pipeline.py          # Definition of the step execution pipeline
│   ├── factory.py           # Instantiates concrete adapters based on configuration
│   ├── registry.py          # Class-based registry for dynamic adapter lookup
│   └── interfaces.py        # Abstract Base Classes (BaseTranscriber, BaseSummarizer, BaseStorage)
│
├── domain/
│   ├── models.py            # Rich domain models (Session, Transcript, Summary, Metadata)
│   ├── exceptions.py        # Core custom exceptions (DomainException, TranscriberError, etc.)
│   └── types.py             # Type aliases and custom typed structures
│
├── modules/
│   ├── transcribers/        # Transcription adapters (e.g., FasterWhisperTranscriber)
│   ├── summarizers/         # Summarization adapters (e.g., GeminiSummarizer)
│   └── storage/             # Storage backends (e.g., LocalJsonStorage)
│
├── config/
│   ├── settings.py          # Configuration schema, parsing, validation (Pydantic/Dataclasses)
│   └── config.yaml          # Main configuration file
│
├── tests/                   # Pytest testing suite
│
├── .env.example             # Template for environment-specific secrets
├── requirements.txt         # Package dependencies
└── README.md                # General setup and execution instructions
```

---

## 3. Communication & Data Flow

The flow of data and dependencies is strictly **inward** toward the core domain.

```
 [ External Clients / UI / main.py ]
                │
                ▼
      [ core/orchestrator.py ] ───────► [ core/interfaces.py ]
                │                               ▲
                │ (injects)                     │ (implements)
                ▼                               │
      [ core/factory.py ]  ───────────► [ modules/* ] (Concrete Adapters)
                │
                ▼
      [ domain/models.py ] (Domain data structures flow across boundaries)
```

1. **Bootstrapping**: `app/main.py` runs, loads configuration from `config/settings.py`, and invokes the `core/factory.py`.
2. **Instantiation**: The `AdapterFactory` instantiates concrete classes registered in `core/registry.py` (e.g., `FasterWhisperTranscriber`) and injects them into the `SessionOrchestrator` constructor.
3. **Workflow Execution**: The orchestrator triggers the pipeline stages. High-level objects (`Transcript`, `Summary`, `Session`) are created, updated, and passed between stages.
4. **Boundary Translation**: Concrete adapters capture library-specific data formats, wrap any library-specific exceptions inside domain exceptions, and return standard Domain Models.

---

## 4. Extension Points & Plug-and-Play Modularity

The system utilizes an **Adapter Registry** and **Decorators** to make swapping and adding new adapters seamless. You can switch between local processing (e.g. CPU/GPU offline models) and cloud APIs (e.g. Google Gemini, OpenAI) with zero code modifications to the core Orchestrator or Factory.

### Showcase: Swapping Transcription Providers (Local vs. Cloud)

We have two fully implemented transcribers that can be swapped dynamically:
1. **FasterWhisperTranscriber** (`faster_whisper`): Performs offline transcription locally. It supports loading different model sizes (`base`, `small`, `medium`, `large-v3`) onto CPU or GPU (CUDA), and supports optimized parameters like language-forcing and brand-spelling context prompts to handle strong regional accents.
2. **GeminiAudioTranscriber** (`gemini_audio`): Performs serverless cloud-based multimodal transcription via the Google Gemini API. It uses model `gemini-2.5-flash` to transcribe accented speech natively with high semantic accuracy.

To swap between them, no business logic changes are needed. You only modify the configuration values.

---

### Steps to Register a New Adapter (e.g., adding `OpenAISummarizer`):

1. **Create the Adapter File**:
   Create a class implementing the interface (`BaseSummarizer`) in `modules/summarizers/openai.py` and register it with the decorator:
   ```python
   from core.interfaces import BaseSummarizer
   from core.registry import summarizer_registry
   from domain.models import Transcript, Summary

   @summarizer_registry.register("openai")  # Registers under the key "openai"
   class OpenAISummarizer(BaseSummarizer):
       def __init__(self, api_key: str, model_name: str):
           self.api_key = api_key
           self.model_name = model_name

       def summarize(self, transcript: Transcript) -> Summary:
           # Call OpenAI API, map response to domain Summary model, and return it.
           pass
   ```

2. **Expose the Module**:
   Add the import statement in `modules/summarizers/__init__.py` to ensure the decorator executes on boot:
   ```python
   from .openai import OpenAISummarizer
   ```

3. **Update Settings & Config**:
   Update `config.yaml` to reference the new identifier and configure its parameters:
   ```yaml
   summarizer:
     provider: "openai"
     openai:
       model_name: "gpt-4o"
   ```
   Provide the credentials in `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   ```

---

## 5. Architectural Trade-offs

* **Boilerplate vs. Modularity**: Wrapping inputs, outputs, and errors requires extra lines of code for exception mapping and data class translation. However, this decouples the core logic from external API breakages (e.g. OpenAI v0.x to v1.x upgrades or Gemini API versioning shifts).
* **Synchronous vs. Asynchronous API**: To keep the scaffolding clean and testable, interfaces use synchronous declarations. If heavy multi-threading or async event loops are introduced later, the interfaces can be updated to utilize Python `async/await` without violating Clean Architecture.
