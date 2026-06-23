from typing import Dict, Type, Generic, TypeVar
from domain.exceptions import RegistryError
from core.interfaces import BaseTranscriber, BaseSummarizer, BaseStorage

T = TypeVar('T')

class AdapterRegistry(Generic[T]):
    """Generic registry for dynamic registration and lookup of adapters."""

    def __init__(self, name: str):
        self.name = name
        self._adapters: Dict[str, Type[T]] = {}

    def register(self, identifier: str):
        """Decorator to register an adapter class under a string identifier."""
        def decorator(cls: Type[T]) -> Type[T]:
            clean_id = identifier.lower().strip()
            if clean_id in self._adapters:
                raise RegistryError(
                    f"Adapter '{clean_id}' is already registered in '{self.name}' registry."
                )
            self._adapters[clean_id] = cls
            return cls
        return decorator

    def get(self, identifier: str) -> Type[T]:
        """Retrieve the registered adapter class by its string identifier."""
        clean_id = identifier.lower().strip()
        if clean_id not in self._adapters:
            raise RegistryError(
                f"Adapter '{clean_id}' not found in '{self.name}' registry. "
                f"Available adapters: {list(self._adapters.keys())}"
            )
        return self._adapters[clean_id]

# Registry instances for each module type
transcriber_registry: AdapterRegistry[BaseTranscriber] = AdapterRegistry("Transcribers")
summarizer_registry: AdapterRegistry[BaseSummarizer] = AdapterRegistry("Summarizers")
storage_registry: AdapterRegistry[BaseStorage] = AdapterRegistry("Storage")
