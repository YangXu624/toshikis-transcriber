import logging
import time
from typing import Callable, TypeVar, Generic, List, Any

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

class SessionPipeline:
    """Coordinates and executes a sequence of PipelineStep stages on a data context."""

    def __init__(self):
        self._steps: List[PipelineStep[Any, Any]] = []

    def add_step(self, step: PipelineStep[Any, Any]) -> 'SessionPipeline':
        """Register a new pipeline step at the end of the sequence."""
        self._steps.append(step)
        return self

    def run(self, initial_val: Any) -> Any:
        """Run all steps sequentially, passing the output of one step as the input to the next."""
        current_val = initial_val
        for step in self._steps:
            current_val = step.execute(current_val)
        return current_val

