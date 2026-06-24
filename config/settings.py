import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

@dataclass
class AppConfig:
    environment: str = "development"
    log_level: str = "INFO"

@dataclass
class TranscriberConfig:
    provider: str = "faster_whisper"
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SummarizerConfig:
    provider: str = "gemini"
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StructurizerConfig:
    provider: str = "gemini"
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StorageConfig:
    provider: str = "json"
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Settings:
    app: AppConfig = field(default_factory=AppConfig)
    transcriber: TranscriberConfig = field(default_factory=TranscriberConfig)
    structurizer: StructurizerConfig = field(default_factory=StructurizerConfig)
    summarizer: SummarizerConfig = field(default_factory=SummarizerConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Load settings from yaml configuration and environment variable overrides."""
    if config_path is None:
        # Resolve config/config.yaml relative to current project root
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / "config" / "config.yaml"

    yaml_data: Dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            try:
                yaml_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse config file: {e}")

    # Build AppConfig
    app_data = yaml_data.get("app", {})
    app_config = AppConfig(
        environment=os.getenv("APP_ENV", app_data.get("environment", "development")),
        log_level=os.getenv("LOG_LEVEL", app_data.get("log_level", "INFO"))
    )

    # Build TranscriberConfig
    transcriber_data = yaml_data.get("transcriber", {})
    trans_provider = os.getenv("TRANSCRIBER_PROVIDER", transcriber_data.get("provider", "faster_whisper"))
    trans_settings = transcriber_data.get(trans_provider, {})
    # Override settings using specific env variables if present
    if trans_provider == "faster_whisper":
        trans_settings["model_size"] = os.getenv("WHISPER_MODEL_SIZE", trans_settings.get("model_size", "base"))
        trans_settings["device"] = os.getenv("WHISPER_DEVICE", trans_settings.get("device", "cpu"))
    elif trans_provider == "gemini_audio":
        trans_settings["api_key"] = os.getenv("GEMINI_API_KEY", trans_settings.get("api_key", ""))
        trans_settings["model_name"] = os.getenv("GEMINI_MODEL_NAME", trans_settings.get("model_name", "gemini-2.5-flash"))

    trans_config = TranscriberConfig(provider=trans_provider, settings=trans_settings)

    # Build SummarizerConfig
    summarizer_data = yaml_data.get("summarizer", {})
    sum_provider = os.getenv("SUMMARIZER_PROVIDER", summarizer_data.get("provider", "gemini"))
    sum_settings = summarizer_data.get(sum_provider, {})
    # Inject API Keys from environment
    if sum_provider == "gemini":
        sum_settings["api_key"] = os.getenv("GEMINI_API_KEY", sum_settings.get("api_key", ""))
        sum_settings["model_name"] = os.getenv("GEMINI_MODEL_NAME", sum_settings.get("model_name", "gemini-2.5-flash"))

    sum_config = SummarizerConfig(provider=sum_provider, settings=sum_settings)

    # Build StructurizerConfig
    structurizer_data = yaml_data.get("structurizer", {})
    struct_provider = os.getenv("STRUCTURIZER_PROVIDER", structurizer_data.get("provider", "gemini"))
    struct_settings = structurizer_data.get(struct_provider, {})
    if struct_provider == "gemini":
        struct_settings["api_key"] = os.getenv("GEMINI_API_KEY", struct_settings.get("api_key", ""))
        struct_settings["model_name"] = os.getenv("GEMINI_MODEL_NAME", struct_settings.get("model_name", "gemini-2.5-flash"))

    struct_config = StructurizerConfig(provider=struct_provider, settings=struct_settings)

    # Build StorageConfig
    storage_data = yaml_data.get("storage", {})
    stor_provider = os.getenv("STORAGE_PROVIDER", storage_data.get("provider", "json"))
    stor_settings = storage_data.get(stor_provider, {})
    if stor_provider == "json":
        stor_settings["output_dir"] = os.getenv("STORAGE_JSON_DIR", stor_settings.get("output_dir", "./data"))

    stor_config = StorageConfig(provider=stor_provider, settings=stor_settings)

    return Settings(
        app=app_config,
        transcriber=trans_config,
        structurizer=struct_config,
        summarizer=sum_config,
        storage=stor_config
    )
