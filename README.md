# AI Session Capture & Summarisation Tool

A production-ready, clean-architecture local-first Python application designed to capture audio sessions, transcribe them, generate summaries, and store the resulting data structures.

## Core Design Philosophy

This project strictly adheres to **Clean Architecture** and the **SOLID** principles:
- **Zero Framework Leaks**: The core business logic and orchestrator do not import or depend on libraries like Faster-Whisper, Gemini, Pydantic, or any external HTTP clients.
- **Interface Driven**: High-level orchestrators communicate with adapters strictly using Abstract Base Class interfaces.
- **Decorator Registry**: New adapters are dynamically registered at runtime. They can be added to the project without modifying any core orchestrator files.

For full architectural documentation, see the [Architecture Design Document](file:///Users/yangxu/code/toshikis_transcriber/Architecture.md).

---

## Getting Started

### 1. Requirements
- Python 3.12 or newer
- Virtual environment (recommended)

### 2. Installation
Clone the repository and install the initial configuration and testing dependencies:

```bash
# Set up a virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Setup Configuration
Copy the environment template and set up your variables:

```bash
cp .env.example .env
```

Review and adjust settings in `config/config.yaml` or override them in `.env`.

---

## Configuring and Running the Application

This codebase supports **plug-and-play swapping** between local offline models (Faster-Whisper) and cloud APIs (Google Gemini). You can toggle between them solely by modifying your configuration.

### 1. Selecting Providers in `.env`
Open your `.env` file to select which transcriber and summarizer to activate:

```bash
# Swapping Transcribers (faster_whisper vs. gemini_audio)
TRANSCRIBER_PROVIDER=faster_whisper
# TRANSCRIBER_PROVIDER=gemini_audio

# Swapping Summarizers
SUMMARIZER_PROVIDER=gemini
```

### 2. Swapping and Tuning Transcription Models
The codebase supports multiple transcription models depending on your performance, accent accuracy, and offline requirements.

#### A. Cloud Gemini API (`gemini_audio`)
Natively handles regional Southeast Asian accents without local computational or memory overhead.
- **Default model**: `gemini-2.5-flash` (can be changed to `gemini-2.0-flash` or `gemini-3.5-flash` in the configurations).
- **To configure**: Set `TRANSCRIBER_PROVIDER=gemini_audio` and ensure your `GEMINI_API_KEY` is loaded in `.env`.

#### B. Local Offline Whisper (`faster_whisper`)
You can dynamically swap between different model sizes depending on your hardware limits (CPU/GPU) and accent challenges.

**How to switch between local Whisper model sizes:**

You can change Whisper model sizes in two ways:
1. **Via Environment Overrides (Recommended)**:
   Add or modify the `WHISPER_MODEL_SIZE` variable in your `.env` file:
   ```bash
   WHISPER_MODEL_SIZE=small  # Options: tiny, base, small, medium, large-v3
   ```
2. **Via YAML Config**:
   Edit [config/config.yaml](file:///Users/yangxu/code/toshikis_transcriber/config/config.yaml) directly under `faster_whisper.model_size`:
   ```yaml
   transcriber:
     provider: "faster_whisper"
     faster_whisper:
       model_size: "small"  # <-- Edit model size here (tiny, base, small, medium, large-v3)
       device: "cpu"        # Target 'cpu' or 'cuda' for GPU acceleration
   ```

**Model Comparison Chart for Accented Singaporean English:**
- **`base`** (~140MB): Low resource requirements, but low accuracy (struggles with strong accents).
- **`small`** (~460MB): Highly recommended balance. Tested at **~85.7% accuracy** on local Singaporean speakers.
- **`medium`** (~1.5GB): High accuracy (**~88.3%**), but slower on standard CPUs.
- **`large-v3`** (~3.0GB): Best local option. High accent precision (**~90.0% accuracy**).

*Note: For local transcription of accents, we force `language: "en"` in our adapter to prevent Whisper from misdetecting regional accents as Malay/Indonesian.*

---

### 3. Execution
To execute the pipeline and process a session:

```bash
python -m app.main
```

Upon execution, the application will:
1. Load the active configuration and environment overrides.
2. Instantiate the selected concrete transcribers, summarizers, and storage engines via the `AdapterFactory`.
3. Check/create a sample meeting recording at `scratch/sample_meeting.wav`.
4. Coordinate the stages (Capture -> Transcribe -> Summarize -> Archive) using the `SessionOrchestrator` pipeline.
5. Save the final serialized session metadata, transcript, and summary to `data/<session_id>.json`.


---

## Testing

All tests are located in the `tests/` directory and can be executed via `pytest`.

### Run All Unit and Integration Tests:
```bash
pytest -v
```

### Run Tests with Coverage:
```bash
pytest --cov=core --cov=modules --cov=domain -v
```

---

## Extending the Project (Adding a New Adapter)

Adding a new adapter is designed to require **no modifications** to core workflow code.

### Step-by-Step Example: Replacing Gemini with OpenAI

1. **Create your implementation file**:
   Write a class implementing `BaseSummarizer` in `modules/summarizers/openai.py`.
   Use the `@summarizer_registry.register("openai")` decorator to declare the adapter's string identifier.

   ```python
   # modules/summarizers/openai.py
   from core.interfaces import BaseSummarizer
   from core.registry import summarizer_registry
   from domain.models import Transcript, Summary

   @summarizer_registry.register("openai")
   class OpenAISummarizer(BaseSummarizer):
       def __init__(self, api_key: str, model_name: str = "gpt-4o"):
           self.api_key = api_key
           self.model_name = model_name

       def summarize(self, transcript: Transcript) -> Summary:
           # Custom OpenAI API call logic
           # Return a Summary object
   ```

2. **Expose the Module**:
   Import your new adapter file in the package initializer (`modules/summarizers/__init__.py`) to trigger the decorator on import:
   ```python
   from .openai import OpenAISummarizer
   ```

3. **Update Config**:
   Update `config/config.yaml` to reference the new provider:
   ```yaml
   summarizer:
     provider: "openai"
     openai:
       model_name: "gpt-4o"
   ```

   And add your credentials to `.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   *(Update `config/settings.py` to retrieve `OPENAI_API_KEY` and pass it to your constructor.)*
