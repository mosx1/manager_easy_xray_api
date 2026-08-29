from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from methods.methods import successAuth


class AuthenticationError(Exception):
    """Raised when token validation fails."""


async def require_query_auth(
    token: Annotated[str, Query()],
    db: AsyncSession = Depends(get_session),
) -> None:
    if not await successAuth(db, token):
        raise AuthenticationError()


T = TypeVar("T", bound=BaseModel)


def authenticated_body(model: type[T]) -> Callable[..., T]:
    async def dependency(
        data: model,
        db: AsyncSession = Depends(get_session),
    ) -> T:
        if not await successAuth(db, data.token):
            raise AuthenticationError()
        return data

    return dependency
