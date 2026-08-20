"""Plugin registry for custom track types.

Allows registering custom track types with validation rules and content
heuristics via a simple Python API or entry points.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Type aliases
ValidatorFn = Callable[[str], list[str]]  # returns list of warning messages
HeuristicsFn = Callable[[str], list[str]]  # returns list of warning messages


class TrackTypeRegistry:
    """Registry for custom and built-in track types."""

    def __init__(self) -> None:
        self._types: dict[str, dict[str, Any]] = {}
        self._validators: dict[str, ValidatorFn | None] = {}
        self._heuristics: dict[str, HeuristicsFn | None] = {}
        # Register built-in types
        for t in [
            "primary", "translation", "commentary", "code",
            "reference", "media_ref", "revision",
        ]:
            self._types[t] = {"builtin": True}

    def register(
        self,
        name: str,
        validator: ValidatorFn | None = None,
        heuristics: HeuristicsFn | None = None,
        description: str = "",
    ) -> None:
        """Register a custom track type.

        Args:
            name: Track type identifier (must be unique).
            validator: Optional function that takes content and returns warning messages.
            heuristics: Optional function that takes content and returns content heuristics warnings.
            description: Human-readable description.
        """
        if name in self._types:
            raise ValueError(f"track type '{name}' is already registered")
        self._types[name] = {"builtin": False, "description": description}
        self._validators[name] = validator
        self._heuristics[name] = heuristics

    def unregister(self, name: str) -> None:
        """Remove a custom track type (cannot remove built-in types)."""
        if name not in self._types:
            raise KeyError(name)
        if self._types[name].get("builtin"):
            raise ValueError(f"cannot unregister built-in type '{name}'")
        del self._types[name]
        self._validators.pop(name, None)
        self._heuristics.pop(name, None)

    def is_registered(self, name: str) -> bool:
        """Check if a track type is registered."""
        return name in self._types

    def all_types(self) -> list[str]:
        """Return all registered track type names."""
        return list(self._types.keys())

    def custom_types(self) -> list[str]:
        """Return only custom (non-built-in) track type names."""
        return [name for name, info in self._types.items() if not info.get("builtin")]

    def validate(self, name: str, content: str) -> list[str]:
        """Run the validator for the given track type on the given content."""
        fn = self._validators.get(name)
        if fn is None:
            return []
        return fn(content)

    def check_heuristics(self, name: str, content: str) -> list[str]:
        """Run content heuristics for the given track type."""
        fn = self._heuristics.get(name)
        if fn is None:
            return []
        return fn(content)


# Global registry instance
_registry = TrackTypeRegistry()


def get_registry() -> TrackTypeRegistry:
    """Return the global track type registry."""
    return _registry


def register_track_type(
    name: str,
    validator: ValidatorFn | None = None,
    heuristics: HeuristicsFn | None = None,
    description: str = "",
) -> None:
    """Register a custom track type in the global registry."""
    _registry.register(name, validator, heuristics, description)
