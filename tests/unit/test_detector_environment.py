from unittest.mock import patch

from setupvault.detectors.environment import _scan_processes, detect_environment


class TestDetectEnvironment:
    @patch("setupvault.detectors.environment.os.environ.get")
    @patch("setupvault.detectors.environment._scan_processes")
    def test_detect_gnome(self, mock_scan, mock_environ) -> None:
        mock_environ.side_effect = lambda key, default=None: {
            "XDG_CURRENT_DESKTOP": "GNOME",
            "XDG_SESSION_TYPE": "x11",
            "WAYLAND_DISPLAY": "",
            "DISPLAY": ":0",
        }.get(key, default)
        mock_scan.return_value = {"gnome-shell", "systemd"}

        result = detect_environment()
        assert result.desktop_environment == "GNOME"
        assert result.display_server == "x11"
        assert result.session_type == "x11"

    @patch("setupvault.detectors.environment.os.environ.get")
    @patch("setupvault.detectors.environment._scan_processes")
    def test_detect_hyprland(self, mock_scan, mock_environ) -> None:
        mock_environ.side_effect = lambda key, default=None: {
            "XDG_CURRENT_DESKTOP": "Hyprland",
            "XDG_SESSION_TYPE": "wayland",
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": "",
        }.get(key, default)
        mock_scan.return_value = {"hyprland", "systemd"}

        result = detect_environment()
        assert result.desktop_environment == "Hyprland"
        assert result.window_manager == "Hyprland"
        assert result.display_server == "wayland"
        assert result.session_type == "wayland"

    def test_scan_processes_returns_set(self) -> None:
        # Should not crash even without /proc access
        result = _scan_processes()
        assert isinstance(result, set)

    @patch("setupvault.detectors.environment.os.environ.get")
    @patch("setupvault.detectors.environment._scan_processes")
    def test_fallback_to_tty(self, mock_scan, mock_environ) -> None:
        mock_environ.side_effect = lambda key, default=None: {
            "WAYLAND_DISPLAY": "",
            "DISPLAY": "",
        }.get(key, default)
        mock_scan.return_value = {"systemd", "journalctl"}

        result = detect_environment()
        assert result.display_server == "tty"
