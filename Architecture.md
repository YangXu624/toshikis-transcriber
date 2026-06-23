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

## 4. Extension Points (Adding a New Adapter)

The system utilizes an **Adapter Registry** and **Decorators** to make adding new adapters seamless without modifying the core Orchestrator or Factory logic.

### Steps to replace/add a Summarizer (e.g., replacing Gemini with OpenAI):

1. **Create the Adapter File**:
   Create `modules/summarizers/openai.py`.

2. **Implement the Interface & Register**:
   ```python
   from core.interfaces import BaseSummarizer
   from core.registry import summarizer_registry
   from domain.models import Transcript, Summary

   @summarizer_registry.register("openai")
   class OpenAISummarizer(BaseSummarizer):
       def __init__(self, api_key: str, model_name: str):
           self.api_key = api_key
           self.model_name = model_name

       def summarize(self, transcript: Transcript) -> Summary:
           # Implementation of OpenAI API call...
           pass
   ```

3. **Update Settings & Config**:
   Update `config.yaml` to reference the new identifier and configure any new parameters:
   ```yaml
   summarizer:
     provider: "openai"
     openai:
       api_key: "${OPENAI_API_KEY}"
       model_name: "gpt-4o"
   ```

No core code modifications are required in `core/orchestrator.py`, `core/pipeline.py`, or `core/factory.py`.

---

## 5. Architectural Trade-offs

* **Boilerplate vs. Modularity**: Wrapping inputs, outputs, and errors requires extra lines of code for exception mapping and data class translation. However, this decouples the core logic from external API breakages (e.g. OpenAI v0.x to v1.x upgrades or Gemini API versioning shifts).
* **Synchronous vs. Asynchronous API**: To keep the scaffolding clean and testable, interfaces use synchronous declarations. If heavy multi-threading or async event loops are introduced later, the interfaces can be updated to utilize Python `async/await` without violating Clean Architecture.
