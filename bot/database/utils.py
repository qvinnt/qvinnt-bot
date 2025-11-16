from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

P = ParamSpec("P")
T = TypeVar("T")


def with_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorats function with session management with automatic commit/rollback.

    This decorator:
    - Opens a new database session
    - Passes it as the first argument to the decorated function
    - Commits the session on successful execution
    - Rolls back the session if an exception occurs
    - Re-raises any exceptions that occur

    Args:
        sessionmaker: The SQLAlchemy async sessionmaker instance

    Returns:
        A decorator function that wraps the target function with session management

    Example:
        @with_session(sessionmaker)
        async def my_function(session: AsyncSession, user_id: int) -> None:
            # Your database operations here
            user = await user_service.get_user_by_id(session, user_id)
            # Session will be committed automatically

    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            async with sessionmaker() as session:
                try:
                    # Pass session as the first argument
                    result = await func(session, *args, **kwargs)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                else:
                    return result

        return wrapper

    return decorator


async def with_session_context[T](
    sessionmaker: async_sessionmaker[AsyncSession],
    func: Callable[..., Awaitable[T]],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Context manager function that provides session management with automatic commit/rollback.

    This function:
    - Opens a new database session
    - Passes it as the first argument to the provided function
    - Commits the session on successful execution
    - Rolls back the session if an exception occurs
    - Re-raises any exceptions that occur

    Args:
        sessionmaker: The SQLAlchemy async sessionmaker instance
        func: The function to execute with the session
        *args: Additional arguments to pass to the function
        **kwargs: Additional keyword arguments to pass to the function

    Returns:
        The result of the function execution

    Example:
        async def my_database_operation(session: AsyncSession, user_id: int) -> User:
            return await user_service.get_user_by_id(session, user_id)

        user = await with_session_context(sessionmaker, my_database_operation, user_id=123)

    """
    async with sessionmaker() as session:
        try:
            result = await func(session, *args, **kwargs)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        else:
            return result
