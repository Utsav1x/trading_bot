from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_dir: str = "logs", log_file: str = "trading_bot.log") -> logging.Logger:
    logger = logging.getLogger("trading_bot")
    if logger.handlers:
        return logger

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(Path(log_dir) / log_file, encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger

