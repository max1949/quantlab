"""Detect pinned NautilusTrader without importing it into business modules."""

from __future__ import annotations

from importlib import import_module, metadata


def nautilus_available() -> bool:
    try:
        import_module("nautilus_trader")
        return True
    except ImportError:
        return False


def nautilus_version() -> str | None:
    if not nautilus_available():
        return None
    try:
        return metadata.version("nautilus_trader")
    except metadata.PackageNotFoundError:
        return None
