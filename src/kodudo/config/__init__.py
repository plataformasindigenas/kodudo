"""Configuration module for kodudo."""

from kodudo.config.loader import load_config
from kodudo.config.types import Config

__all__ = [
    "Config",
    "load_config",
]
