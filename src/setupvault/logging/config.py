from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from setupvault.utils.paths import setupvault_log_dir

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

_LOGGER_NAME = "setupvault"


def configure(
    *,
    log_dir: str | Path | None = None,
    level: str = "info",
    file_output: bool = True,
    console_output: bool = True,
    verbose: bool = False,
) -> logging.Logger:
    """Configure the SetupVault logger.

    Args:
        log_dir: Directory for log files. Defaults to
                 ``~/.local/share/setupvault/logs/``.
        level: Minimum log level for file output.
        file_output: Enable file-based logging.
        console_output: Enable console-based logging.
        verbose: If True, set console level to DEBUG (implies file level).

    Returns:
        The configured root logger.
    """
    resolved_level = _LOG_LEVELS.get(level.lower(), logging.INFO)
    if verbose:
        resolved_level = logging.DEBUG

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if file_output:
        log_path = Path(log_dir) if log_dir else setupvault_log_dir()
        log_path.mkdir(parents=True, exist_ok=True)
        file_path = log_path / "setupvault.log"

        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(resolved_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        if verbose:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a child logger of the SetupVault logger.

    Args:
        name: Child logger name (e.g. ``export_service``).

    Returns:
        A ``logging.Logger`` instance.
    """
    if name:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)
