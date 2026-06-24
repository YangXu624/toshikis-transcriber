import pytest
from pathlib import Path
from config.settings import Settings, AppConfig, TranscriberConfig, StructurizerConfig, SummarizerConfig, StorageConfig
from core.factory import AdapterFactory
from core.orchestrator import SessionOrchestrator

def test_complete_pipeline_integration(mocker, tmp_path, mock_audio_path):
    """Integration test checking that configuration -> factory -> orchestrator -> storage

    works end-to-end with the initial scaffolding.
    """
    # Mock WhisperModel in integration test to avoid running PyTorch inference or downloading model weights
    mock_whisper = mocker.patch("faster_whisper.WhisperModel")
    mock_segment = mocker.MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 2.5
    mock_segment.text = "Hello and welcome to this session."
    mock_info = mocker.MagicMock()
    mock_info.language = "en"
    mock_whisper.return_value.transcribe.return_value = ([mock_segment], mock_info)

    # Mock GenerativeModel in integration test to avoid real Google API calls
    mock_gemini = mocker.patch("google.generativeai.GenerativeModel")
    mock_gemini_response = mocker.MagicMock()
    mock_gemini_response.text = (
        '{"content": "This is an integrated summary", '
        '"key_points": ["Point A"], "action_items": ["Action B"], '
        '"topics": ["Topic C"]}'
    )
    mock_gemini.return_value.generate_content.return_value = mock_gemini_response

    # 1. Arrange: Create programmatic Settings override targeting the temporary path
    settings = Settings(
        app=AppConfig(environment="testing", log_level="DEBUG"),
        transcriber=TranscriberConfig(provider="faster_whisper", settings={}),
        structurizer=StructurizerConfig(provider="gemini", settings={}),
        summarizer=SummarizerConfig(provider="gemini", settings={"api_key": "test-key"}),
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


def test_complete_pipeline_with_structurizer_integration(mocker, tmp_path, mock_audio_path):
    """Integration test checking that the full 3-module pipeline works end-to-end."""
    # Mock WhisperModel
    mock_whisper = mocker.patch("faster_whisper.WhisperModel")
    mock_segment = mocker.MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 2.5
    mock_segment.text = "Hello and welcome. Is there any question?"
    mock_info = mocker.MagicMock()
    mock_info.language = "en"
    mock_whisper.return_value.transcribe.return_value = ([mock_segment], mock_info)

    # Mock GenerativeModel with different responses for structure and summary
    mock_gen_model = mocker.MagicMock()
    mocker.patch("google.generativeai.GenerativeModel", return_value=mock_gen_model)

    # First call is for structurizer, second call is for summarizer
    mock_structure_res = mocker.MagicMock()
    mock_structure_res.text = '{"presentation": "Hello and welcome.", "q_and_a": "[Question]: Is there any question?"}'
    
    mock_summary_res = mocker.MagicMock()
    mock_summary_res.text = '{"content": "Integrated QA summary", "key_points": ["QA point"], "action_items": [], "topics": []}'
    
    mock_gen_model.generate_content.side_effect = [mock_structure_res, mock_summary_res]

    settings = Settings(
        app=AppConfig(environment="testing", log_level="DEBUG"),
        transcriber=TranscriberConfig(provider="faster_whisper", settings={}),
        structurizer=StructurizerConfig(provider="gemini", settings={"api_key": "test-key"}),
        summarizer=SummarizerConfig(provider="gemini", settings={"api_key": "test-key"}),
        storage=StorageConfig(provider="json", settings={"output_dir": str(tmp_path)})
    )

    transcriber = AdapterFactory.create_transcriber(settings.transcriber.provider, settings.transcriber.settings)
    structurizer = AdapterFactory.create_structurizer(settings.structurizer.provider, settings.structurizer.settings)
    summarizer = AdapterFactory.create_summarizer(settings.summarizer.provider, settings.summarizer.settings)
    storage = AdapterFactory.create_storage(settings.storage.provider, settings.storage.settings)

    orchestrator = SessionOrchestrator(
        transcriber=transcriber,
        structurizer=structurizer,
        summarizer=summarizer,
        storage=storage
    )

    session = orchestrator.run_pipeline(audio_path=mock_audio_path, title="Full Pipeline Test")

    assert session.presentation_text == "Hello and welcome."
    assert session.structured_qa_text == "[Question]: Is there any question?"
    assert session.summary.content == "Integrated QA summary"

    # Verify separate files exist
    pres_file = tmp_path / f"{session.session_id}_presentation.txt"
    qa_file = tmp_path / f"{session.session_id}_q_and_a.txt"
    json_file = tmp_path / f"{session.session_id}.json"

    assert pres_file.exists()
    assert qa_file.exists()
    assert json_file.exists()
    assert pres_file.read_text(encoding="utf-8") == "Hello and welcome."
    assert qa_file.read_text(encoding="utf-8") == "[Question]: Is there any question?"
