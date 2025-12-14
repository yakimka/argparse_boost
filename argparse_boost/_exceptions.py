class ArgparseBoostError(Exception):
    """Error during CLI setup."""


class FieldNameConflictError(ArgparseBoostError):
    """Raised when flattened dataclass field names collide."""


class UnsupportedFieldTypeError(ArgparseBoostError):
    """Raised when dataclass fields use unsupported types."""
