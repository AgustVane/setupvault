import pytest

from setupvault.core.exceptions import SnapshotVersionError
from setupvault.core.versions import (
    CURRENT_SNAPSHOT_VERSION,
    MINIMUM_SNAPSHOT_VERSION,
    VersionInfo,
    is_supported,
    schema_resource_path,
    supported_versions,
    validate_version,
)


class TestVersionInfo:
    def test_valid_version(self) -> None:
        v = VersionInfo(major=1)
        assert v.major == 1
        assert str(v) == "1"

    def test_invalid_version_raises(self) -> None:
        with pytest.raises(ValueError, match=">= 1"):
            VersionInfo(major=0)

        with pytest.raises(ValueError, match=">= 1"):
            VersionInfo(major=-1)


class TestSupportedVersions:
    def test_current_version_is_supported(self) -> None:
        assert is_supported(CURRENT_SNAPSHOT_VERSION) is True

    def test_minimum_version_is_supported(self) -> None:
        assert is_supported(MINIMUM_SNAPSHOT_VERSION) is True

    def test_future_version_not_supported(self) -> None:
        assert is_supported(CURRENT_SNAPSHOT_VERSION + 1) is False

    def test_past_version_not_supported(self) -> None:
        assert is_supported(0) is False
        assert is_supported(-1) is False

    def test_supported_versions_list(self) -> None:
        versions = supported_versions()
        assert len(versions) >= 1
        assert all(isinstance(v, VersionInfo) for v in versions)
        assert versions[-1].major == CURRENT_SNAPSHOT_VERSION


class TestValidateVersion:
    def test_valid_version_passes(self) -> None:
        validate_version(CURRENT_SNAPSHOT_VERSION)

    def test_invalid_version_raises(self) -> None:
        with pytest.raises(SnapshotVersionError):
            validate_version(99)


class TestSchemaResourcePath:
    def test_path_format(self) -> None:
        path = schema_resource_path(1)
        assert path == "setupvault/validation/schemas/snapshot-v1.json"

    def test_path_for_different_version(self) -> None:
        path = schema_resource_path(42)
        assert path == "setupvault/validation/schemas/snapshot-v42.json"
