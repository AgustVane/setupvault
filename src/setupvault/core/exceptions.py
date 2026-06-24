class SetupVaultError(Exception):
    """Base exception for all SetupVault errors."""


class SnapshotError(SetupVaultError):
    """Base exception for snapshot-related errors."""


class InvalidSnapshotError(SnapshotError):
    """Raised when a snapshot fails validation."""


class SnapshotVersionError(SnapshotError):
    """Raised when a snapshot version is not supported."""


class ConfigError(SetupVaultError):
    """Raised when user configuration is invalid."""


class ProfileError(SetupVaultError):
    """Raised when a profile definition is invalid."""


class UnsupportedDistributionError(SetupVaultError):
    """Raised when the detected distribution is not supported."""


class DistributionDetectionError(SetupVaultError):
    """Raised when distribution detection fails."""


class PackageManagerError(SetupVaultError):
    """Raised when a package manager operation fails."""


class PermissionError(SetupVaultError):
    """Raised when required permissions are not available."""


class ValidationError(SetupVaultError):
    """Raised when validation of data or state fails."""


class DoctorCheckError(SetupVaultError):
    """Raised when a doctor diagnostic check fails critically."""


class StorageError(SetupVaultError):
    """Raised when storage read/write operations fail."""


class RestoreError(SetupVaultError):
    """Base exception for restore-related errors."""


class ExportError(SetupVaultError):
    """Base exception for export-related errors."""


class FilterError(SetupVaultError):
    """Raised when filter patterns are invalid."""


class MergeError(SetupVaultError):
    """Raised when a merge operation fails."""


class PathTraversalError(SetupVaultError):
    """Raised when path traversal is detected in snapshot data."""
