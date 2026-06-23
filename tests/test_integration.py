import pytest
from pathlib import Path
from config.settings import Settings, AppConfig, TranscriberConfig, SummarizerConfig, StorageConfig
from core.factory import AdapterFactory
from core.orchestrator import SessionOrchestrator

def test_complete_pipeline_integration(tmp_path, mock_audio_path):
    """Integration test checking that configuration -> factory -> orchestrator -> storage

    works end-to-end with the initial scaffolding.
    """
    # 1. Arrange: Create programmatic Settings override targeting the temporary path
    settings = Settings(
        app=AppConfig(environment="testing", log_level="DEBUG"),
        transcriber=TranscriberConfig(provider="faster_whisper", settings={}),
        summarizer=SummarizerConfig(provider="gemini", settings={}),
        storage=StorageConfig(provider="json", settings={"output_dir": str(tmp_path)})
    )

    # 2. Act: Instantiating adapters using the Factory
    transcriber = AdapterFactory.create_transcriber(
        provider=settings.transcriber.provider,
        settings=settings.transcriber.settings
    )
    summarizer = AdapterFactory.create_summarizer(
        provider=settings.summarizer.provider,
        settings=settings.summarizer.settings
    )
    storage = AdapterFactory.create_storage(
        provider=settings.storage.provider,
        settings=settings.storage.settings
    )

    # 3. Act: Constructing the Orchestrator with the factory-created adapters
    orchestrator = SessionOrchestrator(
        transcriber=transcriber,
        summarizer=summarizer,
        storage=storage
    )

    # 4. Act: Running the pipeline
    session = orchestrator.run_pipeline(
        audio_path=mock_audio_path,
        title="Integration Test Session"
    )

    # 5. Assert: Verify the complete session output structure
    assert session is not None
    assert session.session_id is not None
    assert session.metadata.title == "Integration Test Session"
    assert session.transcript is not None
    assert session.summary is not None

    # 6. Assert: Verify files are correctly persisted to the storage layer output directory
    expected_output_json = tmp_path / f"{session.session_id}.json"
    assert expected_output_json.exists()

    # 7. Assert: Reload from disk and verify structural details match
    reloaded_session = storage.load(session.session_id)
    assert reloaded_session.session_id == session.session_id
    assert reloaded_session.transcript.raw_text == session.transcript.raw_text
    assert reloaded_session.summary.content == session.summary.content
