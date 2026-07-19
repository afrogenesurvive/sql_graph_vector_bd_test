"""
Centralized logging utility for the SQL → Neo4j GraphRAG pipeline.

Provides structured, visually scannable terminal output with phase
headers, step indicators, progress bars, and emoji status markers.

Usage:
    from scripts.logger import setup_logger, log_phase, log_step, log_ok, log_warn, log_err

    setup_logger()
    log_phase("2", "ETL Migration")
    log_step("Discovering tables...")
    log_ok("8 tables found")
    log_warn("No embeddings for label 'Order'")
    log_err("Connection refused")
"""

import logging
import sys
from typing import Optional

# ── ANSI colours ──────────────────────────────────────
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_RESET = "\033[0m"


class _PipelineFormatter(logging.Formatter):
    """Custom formatter that brightens the level prefix and dims the timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # levelname colouring
        level_colour = {
            "INFO": _GREEN,
            "WARNING": _YELLOW,
            "ERROR": _RED,
            "CRITICAL": _RED,
        }.get(record.levelname, _RESET)
        # Replace the textual level with a coloured version
        padded_level = f"{record.levelname:<8}"
        msg = msg.replace(padded_level, f"{level_colour}{padded_level}{_RESET}", 1)
        return msg


# ── Singleton guard ────────────────────────────────────
_logger_initialised = False


def setup_logger(level: int = logging.INFO) -> None:
    """Call once at application startup to configure the root logger.

    After calling this, any ``get_logger(__name__)`` call will inherit
    the configuration.
    """
    global _logger_initialised
    if _logger_initialised:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(
        _PipelineFormatter(
            fmt="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    _logger_initialised = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger for *name* (normally ``__name__``)."""
    return logging.getLogger(name)


# ── High-level helpers ─────────────────────────────────


def log_phase(number: str, title: str) -> None:
    """Print an eye-catching phase header.

    Example:
        ═══════════════════════════════════════════════
               🚀  Phase 2: ETL Migration
        ═══════════════════════════════════════════════
    """
    sep = "═" * 55
    print(f"\n{_BOLD}{_CYAN}{sep}{_RESET}")
    print(f"{_BOLD}{_CYAN}   🚀  Phase {number}: {title}{_RESET}")
    print(f"{_BOLD}{_CYAN}{sep}{_RESET}")


def log_step(message: str) -> None:
    """Print a step indicator.

    Example:
        ──  Discovering tables...
    """
    print(f"  {_BOLD}{_DIM}──{_RESET}  {message}")


def log_progress(current: int, total: int, label: str = "items") -> None:
    """Print a progress line (every N items, not on every single one).

    Example:
        📊  Progress:  150 / 200  products embedded
    """
    print(f"   📊  Progress:  {current:>4} / {total:<4}  {label}")


def log_ok(message: str) -> None:
    """Print a success confirmation."""
    print(f"   {_GREEN}✅  {message}{_RESET}")


def log_warn(message: str) -> None:
    """Print a warning."""
    print(f"   {_YELLOW}⚠️  {message}{_RESET}")


def log_err(message: str) -> None:
    """Print an error."""
    print(f"   {_RED}❌  {message}{_RESET}")


def log_info(message: str) -> None:
    """Print an info line."""
    print(f"   ℹ️  {message}")
