import pytest

from setupvault.core.config import SetupVaultConfig, DEFAULT_PROFILE, DEFAULT_EXPORT_DIR
from setupvault.core.exceptions import ConfigError


class TestSetupVaultConfig:
    def test_default_values(self) -> None:
        config = SetupVaultConfig()
        assert config.export_dir == DEFAULT_EXPORT_DIR
        assert config.default_profile == DEFAULT_PROFILE
        assert config.compress_by_default is False
        assert config.always_backup is True
        assert len(config.dotfile_globs) > 0

    def test_load_from_missing_file_returns_defaults(self, tmp_path) -> None:
        missing = tmp_path / "does-not-exist.toml"
        config = SetupVaultConfig.load(missing)
        assert config.default_profile == DEFAULT_PROFILE

    def test_load_from_valid_toml(self, tmp_path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[core]\n"
            'export_dir = "/tmp/exports"\n'
            "compress_by_default = true\n"
            "excluded_sections = [\"fonts\"]\n"
            "\n"
            "[dotfiles]\n"
            'globs = [".zshrc", ".bashrc"]\n'
        )
        config = SetupVaultConfig.load(config_path)
        assert config.export_dir == "/tmp/exports"
        assert config.compress_by_default is True
        assert config.excluded_sections == ["fonts"]
        assert config.dotfile_globs == [".zshrc", ".bashrc"]

    def test_load_from_invalid_toml_raises(self, tmp_path) -> None:
        config_path = tmp_path / "bad.toml"
        config_path.write_text("[[[invalid]]]\n")
        with pytest.raises(ConfigError):
            SetupVaultConfig.load(config_path)

    def test_dict_round_trip(self) -> None:
        config = SetupVaultConfig(
            export_dir="/tmp/x",
            compress_by_default=True,
        )
        d = config.dict()
        assert d["export_dir"] == "/tmp/x"
        assert d["compress_by_default"] is True
