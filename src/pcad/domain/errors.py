"""Domain-specific error definitions and codes."""

class PcadError(Exception):
    """Base class for pcad application errors."""
    def __init__(self, message_key: str, detail: str = ""):
        super().__init__(f"{message_key}: {detail}" if detail else message_key)
        self.message_key = message_key
        self.detail = detail

class ValidationError(PcadError):
    """Raised when parameters fail domain validation rules."""
    pass

class GeometryError(PcadError):
    """Raised when CAD kernel fails to construct a valid manifold solid."""
    pass

class TemplateNotFoundError(PcadError):
    """Raised when a requested template ID is not in the registry."""
    pass

class ProjectFileError(PcadError):
    """Raised when loading or saving a .pcad project fails."""
    pass
