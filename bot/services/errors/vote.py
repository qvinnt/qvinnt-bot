from __future__ import annotations

from .base import ServiceError


class VoteServiceError(ServiceError):
    pass


class VoteAlreadyExistsError(VoteServiceError):
    pass
