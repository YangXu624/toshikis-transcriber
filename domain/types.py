from pathlib import Path
from typing import Union, Dict, Any, TypeAlias

# Type Alias for filepath arguments
FilePath: TypeAlias = Union[str, Path]

# Type Alias for adapter configuration parameters
AdapterConfig: TypeAlias = Dict[str, Any]
