from pathlib import Path
from unittest.mock import patch

from setupvault.detectors.dotfiles import detect_dotfiles


class TestDetectDotfiles:
    def test_detect_dotfiles_with_real_files(self) -> None:
        import tempfile

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(Path, "home", return_value=Path(tmpdir)),
        ):
            zshrc = Path(tmpdir) / ".zshrc"
            zshrc.write_text("export PATH=$PATH:~/bin\n")

            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("alias ll='ls -la'\n")

            results = detect_dotfiles([".zshrc", ".bashrc"])
            assert len(results) == 2

            paths = {r.path for r in results}
            assert ".zshrc" in paths
            assert ".bashrc" in paths

            for entry in results:
                assert entry.hash is not None
                assert len(entry.hash) == 64
                assert entry.size is not None
                assert entry.permissions is not None

    def test_detect_dotfiles_empty_globs(self) -> None:
        results = detect_dotfiles([])
        assert results == ()

    def test_detect_dotfiles_no_matches(self) -> None:
        import tempfile

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(Path, "home", return_value=Path(tmpdir)),
        ):
            results = detect_dotfiles([".nonexistent"])
            assert results == ()
