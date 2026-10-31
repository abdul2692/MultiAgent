"""
Centralized Logging Infrastructure for Multi-Agent System.
Configures structured formatting for console and file logging.
"""
import os
import sys
import logging

LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "assistant.log")

def setup_logger(name: str = "multi_agent", level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a structured logger instance.
    Writes to both terminal stdout and logs/assistant.log.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    # Format: Timestamp | Level | Component | Message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Default package logger
logger = setup_logger()

