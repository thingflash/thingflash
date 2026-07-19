from __future__ import annotations


class ThingFlashError(Exception):
    """Base class for all ThingFlash errors."""

    code: str = "THINGFLASH_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.hint = hint


class ManifestValidationError(ThingFlashError):
    """The manifest failed schema or semantic validation."""

    code = "MANIFEST_INVALID"


class ValidationError(ThingFlashError):
    """A user-supplied value failed validation before use."""

    code = "VALIDATION_ERROR"


class NotFoundError(ThingFlashError):
    """A requested resource does not exist in the registry or AWS."""

    code = "NOT_FOUND"


class AlreadyExistsError(ThingFlashError):
    """A resource with the requested identity already exists."""

    code = "ALREADY_EXISTS"
