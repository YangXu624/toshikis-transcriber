import pytest
from pathlib import Path
from core.registry import storage_registry
from core.interfaces import BaseStorage
from modules.storage.json_storage import LocalJsonStorage
from domain.exceptions import SessionNotFoundError

def test_storage_registered_successfully():
    # Assert json is registered in the storage registry
    cls = storage_registry.get("json")
    assert cls is LocalJsonStorage
    assert issubclass(cls, BaseStorage)

def test_json_storage_saves_and_loads_correctly(tmp_path, sample_session):
    # Given a storage initialized with a temp output path
    storage = LocalJsonStorage(output_dir=str(tmp_path))

    # When we save a session
    storage.save(sample_session)

    # Then a JSON file should exist on the disk
    expected_file = tmp_path / f"{sample_session.session_id}.json"
    assert expected_file.exists()

    # And when we load that session back
    loaded_session = storage.load(sample_session.session_id)

    # Then the reconstructed session should match the original session
    assert loaded_session.session_id == sample_session.session_id
    assert loaded_session.metadata.title == sample_session.metadata.title
    assert loaded_session.metadata.duration_seconds == sample_session.metadata.duration_seconds
    assert loaded_session.metadata.created_at == sample_session.metadata.created_at
    
    # Assert deep parity of nested models
    assert loaded_session.transcript.raw_text == sample_session.transcript.raw_text
    assert len(loaded_session.transcript.segments) == len(sample_session.transcript.segments)
    assert loaded_session.transcript.segments[0].text == sample_session.transcript.segments[0].text
    
    assert loaded_session.summary.content == sample_session.summary.content
    assert loaded_session.summary.key_points == sample_session.summary.key_points
    assert loaded_session.summary.action_items == sample_session.summary.action_items

def test_json_storage_raises_not_found_on_missing_session(tmp_path):
    # Given
    storage = LocalJsonStorage(output_dir=str(tmp_path))

    # When / Then
    with pytest.raises(SessionNotFoundError) as exc_info:
        storage.load("non-existent-uuid")

    assert "does not exist" in str(exc_info.value)
