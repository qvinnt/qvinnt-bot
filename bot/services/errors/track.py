from __future__ import annotations

from .base import ServiceError


class TrackServiceError(ServiceError):
    pass


class TrackNotFoundError(TrackServiceError):
    pass


class TrackAlreadyExistsError(TrackServiceError):
    pass
