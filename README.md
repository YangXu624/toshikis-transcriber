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

## Running the Application

To run the bootstrapped scaffold demonstrating the pipeline:

```bash
python -m app.main
```

Upon execution, the application will:
1. Load configuration from `config/config.yaml` and environment variables.
2. Initialize mock instances of the `faster_whisper` transcriber and the `gemini` summarizer using the `AdapterFactory`.
3. Create a dummy audio file at `scratch/sample_meeting.wav`.
4. Run the full capture, transcription, summarization, and local storage archiving sequence.
5. Save the final JSON object in the directory configured (defaults to `./data/`).

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
