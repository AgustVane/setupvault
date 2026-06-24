from setupvault.core.exceptions import (
    ConfigError,
    DistributionDetectionError,
    ExportError,
    FilterError,
    InvalidSnapshotError,
    MergeError,
    PathTraversalError,
    PermissionError,
    ProfileError,
    RestoreError,
    SetupVaultError,
    SnapshotError,
    SnapshotVersionError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_base_exception(self) -> None:
        assert issubclass(SnapshotError, SetupVaultError)
        assert issubclass(ConfigError, SetupVaultError)
        assert issubclass(ProfileError, SetupVaultError)
        assert issubclass(ValidationError, SetupVaultError)
        assert issubclass(ExportError, SetupVaultError)
        assert issubclass(RestoreError, SetupVaultError)

    def test_snapshot_exceptions(self) -> None:
        assert issubclass(InvalidSnapshotError, SnapshotError)
        assert issubclass(SnapshotVersionError, SnapshotError)

    def test_security_exception(self) -> None:
        assert issubclass(PathTraversalError, SetupVaultError)

    def test_functional_exceptions(self) -> None:
        assert issubclass(DistributionDetectionError, SetupVaultError)
        assert issubclass(PermissionError, SetupVaultError)
        assert issubclass(FilterError, SetupVaultError)
        assert issubclass(MergeError, SetupVaultError)

    def test_exception_message(self) -> None:
        err = InvalidSnapshotError("test message")
        assert str(err) == "test message"
        assert isinstance(err, SetupVaultError)
