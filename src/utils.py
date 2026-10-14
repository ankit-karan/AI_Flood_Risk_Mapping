"""Logging + small helpers shared across modules."""
import logging
import sys

import pandas as pd

from . import config


def get_logger(name: str = "flood") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def ensure_sample_data() -> pd.DataFrame:
    """Load sample CSV, generating it first if missing."""
    if not config.SAMPLE_DATA_PATH.exists():
        from .data_generation import generate_and_save
        return generate_and_save()
    return pd.read_csv(config.SAMPLE_DATA_PATH)
