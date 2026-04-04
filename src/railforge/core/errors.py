class RailForgeError(Exception):
    """Base error for RailForge."""


class InvalidTransitionError(RailForgeError):
    """Raised when a state transition is not allowed."""


class ArtifactNotFoundError(RailForgeError):
    """Raised when a persisted artifact cannot be found."""


class ResumeError(RailForgeError):
    """Raised when a run cannot be resumed."""

