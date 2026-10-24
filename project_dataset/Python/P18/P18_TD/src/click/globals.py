from __future__ import annotations

import typing as t
from threading import local

if t.TYPE_CHECKING:
    from .core import Context

_local = local()


@t.overload
def get_current_context(silent: t.Literal[False] = False) -> Context: ...


@t.overload
def get_current_context(silent: bool = ...) -> Context | None: ...


def get_current_context(silent: bool = False) -> Context | None:
    """Returns the current click context.  This can be used as a way to
    access the current context object from anywhere.  This is a more implicit
    alternative to the :func:`pass_context` decorator.  This function is
    primarily useful for helpers such as :func:`echo` which might be
    interested in changing its behavior based on the current context.

    To push the current context, :meth:`Context.scope` can be used.

    .. versionadded:: 5.0

    :param silent: if set to `True` the return value is `None` if no context
                   is available.  The default behavior is to raise a
                   :exc:`RuntimeError`.
    """
    try:
        return t.cast("Context", _local.stack[-1])
    except (AttributeError, IndexError) as e:
        if not silent:
            raise RuntimeError("There is no active click context.") from e

    return None


def push_context(ctx: Context) -> None:
    """Pushes a new context to the current stack."""
    _local.__dict__.setdefault("stack", []).append(ctx)


def pop_context() -> None:
    """Removes the top level from the stack."""
    _local.stack.pop()


def get_resolution_metadata() -> dict[str, t.Any]:
    """Returns resolution context metadata used by the command resolution
    strategy system. This provides contextual hints to extended resolvers
    about the current runtime environment.

    The metadata includes the active context's token_normalize_func
    and resilient_parsing state when available.
    """
    ctx = get_current_context(silent=True)
    metadata: dict[str, t.Any] = {"has_context": ctx is not None}

    if ctx is not None:
        metadata["token_normalize_func"] = ctx.token_normalize_func
        metadata["resilient_parsing"] = ctx.resilient_parsing
        metadata["color"] = ctx.color

    return metadata


def resolve_color_default(color: bool | None = None) -> bool | None:
    """Internal helper to get the default value of the color flag.  If a
    value is passed it's returned unchanged, otherwise it's looked up from
    the current context.
    """
    if color is not None:
        return color

    ctx = get_current_context(silent=True)

    if ctx is not None:
        return ctx.color

    return None
