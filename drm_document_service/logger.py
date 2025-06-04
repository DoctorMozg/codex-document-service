import logging
import sys
from typing import Literal


def setup_logging(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
) -> None:
    log_level_obj = getattr(logging, log_level.upper())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_obj)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level_obj)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
