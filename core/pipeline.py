import logging
import time
from typing import Callable, TypeVar, Generic

T = TypeVar('T')
U = TypeVar('U')

logger = logging.getLogger(__name__)

class PipelineStep(Generic[T, U]):
    """Represents a discrete executable stage in the processing pipeline.

    Wraps step actions with unified logging, error catching, and performance metrics.
    """

    def __init__(self, name: str, action: Callable[[T], U]):
        self.name = name
        self.action = action

    def execute(self, data: T) -> U:
        """Execute the stage action, timing the execution duration."""
        start_time = time.perf_counter()
        logger.info(f"[Pipeline] Starting step: '{self.name}'")
        try:
            result = self.action(data)
            duration = time.perf_counter() - start_time
            logger.info(f"[Pipeline] Step '{self.name}' completed in {duration:.3f} seconds.")
            return result
        except Exception as e:
            logger.error(f"[Pipeline] Step '{self.name}' failed: {e}")
            raise
