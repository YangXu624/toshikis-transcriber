import logging
from typing import Dict, Any

from core.interfaces import BaseTranscriber, BaseSummarizer, BaseStorage
from core.registry import transcriber_registry, summarizer_registry, storage_registry

# Import all modules to trigger decorator-based registration
import modules.transcribers  # noqa: F401
import modules.summarizers  # noqa: F401
import modules.storage      # noqa: F401

logger = logging.getLogger(__name__)

class AdapterFactory:
    """Factory responsible for instantiating adapter implementations from configurations."""

    @staticmethod
    def create_transcriber(provider: str, settings: Dict[str, Any]) -> BaseTranscriber:
        """Instantiate a transcriber based on provider name and constructor configuration."""
        logger.info(f"Instantiating Transcriber provider: '{provider}'")
        adapter_cls = transcriber_registry.get(provider)
        return adapter_cls(**settings)

    @staticmethod
    def create_summarizer(provider: str, settings: Dict[str, Any]) -> BaseSummarizer:
        """Instantiate a summarizer based on provider name and constructor configuration."""
        logger.info(f"Instantiating Summarizer provider: '{provider}'")
        adapter_cls = summarizer_registry.get(provider)
        return adapter_cls(**settings)

    @staticmethod
    def create_storage(provider: str, settings: Dict[str, Any]) -> BaseStorage:
        """Instantiate a storage engine based on provider name and constructor configuration."""
        logger.info(f"Instantiating Storage provider: '{provider}'")
        adapter_cls = storage_registry.get(provider)
        return adapter_cls(**settings)
