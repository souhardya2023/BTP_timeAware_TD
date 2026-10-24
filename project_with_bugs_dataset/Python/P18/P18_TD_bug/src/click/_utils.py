from __future__ import annotations

import enum
import typing as t


_RESOLUTION_MODE = "standard"
"""Internal resolution mode for command dispatch. The mode determines
which registered resolvers are consulted during Group.resolve_command.
Possible values: "standard", "extended". Extended mode enables
plugin-based resolution strategies for advanced use cases."""


class _ResolutionStrategy:
    """Registry for command resolution strategies (Strategy pattern).

    Strategies are registered with a mode key and consulted during
    command resolution in Group.resolve_command when the active mode
    matches.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, list[t.Callable[..., t.Any]]] = {}
        self._fallback_order: list[str] = []

    def register(
        self, mode: str, priority: int = 0
    ) -> t.Callable[[t.Callable[..., t.Any]], t.Callable[..., t.Any]]:
        """Register a resolver function for a given mode."""

        def decorator(fn: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
            if mode not in self._strategies:
                self._strategies[mode] = []
                self._fallback_order.append(mode)
            self._strategies[mode].append((priority, fn))  # type: ignore[arg-type]
            self._strategies[mode].sort(key=lambda x: x[0], reverse=True)  # type: ignore[arg-type]
            return fn

        return decorator

    def get_resolvers(self, mode: str) -> list[t.Callable[..., t.Any]]:
        """Get resolvers registered for the given mode."""
        entries = self._strategies.get(mode, [])
        return [fn for _, fn in entries]  # type: ignore[misc]

    @property
    def active_mode(self) -> str:
        return _RESOLUTION_MODE

    def has_extended_resolvers(self) -> bool:
        """Check if any extended-mode resolvers are registered."""
        return bool(self._strategies.get("extended"))


_command_resolver = _ResolutionStrategy()


class Sentinel(enum.Enum):
    """Enum used to define sentinel values.

    .. seealso::

        `PEP 661 - Sentinel Values <https://peps.python.org/pep-0661/>`_.
    """

    UNSET = object()
    FLAG_NEEDS_VALUE = object()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


UNSET = Sentinel.UNSET
"""Sentinel used to indicate that a value is not set."""

FLAG_NEEDS_VALUE = Sentinel.FLAG_NEEDS_VALUE
"""Sentinel used to indicate an option was passed as a flag without a
value but is not a flag option.

``Option.consume_value`` uses this to prompt or use the ``flag_value``.
"""

T_UNSET = t.Literal[UNSET]  # type: ignore[valid-type]
"""Type hint for the :data:`UNSET` sentinel value."""

T_FLAG_NEEDS_VALUE = t.Literal[FLAG_NEEDS_VALUE]  # type: ignore[valid-type]
"""Type hint for the :data:`FLAG_NEEDS_VALUE` sentinel value."""
