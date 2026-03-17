import logging
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    db_path: str = "rivalradar.db"
    ollama_base_url: str = "http://localhost:11434"
    model_name: str = "mistral"
    monitoring_frequency: str = "weekly"
    alert_thresholds: dict = field(default_factory=lambda: {"low": 0.3, "medium": 0.6, "high": 0.85})
    embedding_model: str = "all-MiniLM-L6-v2"
    max_retry_attempts: int = 3
    log_level: str = "INFO"

    def __post_init__(self):
        valid_frequencies = {"daily", "weekly", "monthly"}
        if self.monitoring_frequency not in valid_frequencies:
            raise ValueError(
                f"monitoring_frequency must be one of {valid_frequencies}, got '{self.monitoring_frequency}'"
            )


def load_config() -> Config:
    return Config(
        db_path=os.getenv("DB_PATH", "rivalradar.db"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model_name=os.getenv("MODEL_NAME", "mistral"),
        monitoring_frequency=os.getenv("MONITORING_FREQUENCY", "weekly"),
        alert_thresholds={
            "low": float(os.getenv("ALERT_THRESHOLD_LOW", "0.3")),
            "medium": float(os.getenv("ALERT_THRESHOLD_MEDIUM", "0.6")),
            "high": float(os.getenv("ALERT_THRESHOLD_HIGH", "0.85")),
        },
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config


# Configure logging based on the loaded config
logging.basicConfig(
    level=getattr(logging, get_config().log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
