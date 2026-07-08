# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0.dev0] - 2026-07-08

### Added

- **CLI commands**: `export`, `restore`, `info`, `validate`, `report`, `doctor`, `diff`, `list`, `gui`
- **PySide6 GUI** with 9 panels (Export, Restore, Info, Validate, Report, Doctor, Diff, List, Settings)
- **System detection**: distro, kernel, hostname, uptime, architecture
- **Environment detection**: desktop environment, window manager, display server, session type
- **Shell detection**: current shell, all available shells, config file discovery with hashing
- **Package detection**: official repos, AUR (Arch), third-party, Flatpak, Snap
- **Theme detection**: GTK (gsettings, settings.ini, gtkrc) and Qt (qt5ct, qt6ct)
- **Font detection**: system fonts (fc-list), user fonts, fontconfig rendering settings
- **Dotfile capture**: 23 default glob patterns with SHA-256 hashing, base64 content embedding
- **Distro adapters**: Arch, Debian, Ubuntu, Fedora, openSUSE (pluggable adapter pattern)
- **Three restore profiles**: `full`, `minimal`, `packages-only` plus user-defined TOML profiles
- **Plan-then-apply restore** with rollback support for packages, themes, fonts, dotfiles
- **Cross-distro package name mapping** (Arch ↔ Debian ↔ Ubuntu ↔ Fedora ↔ openSUSE)
- **Three-layer validation**: JSON Schema, semantic rules, compatibility warnings
- **Report formats**: Markdown, JSON, standalone HTML
- **Snapshot format**: versioned (v1), optional compression (.json.gz), portable
- **Doctor diagnostics**: 9 system readiness checks
- **Diff tool**: section-by-section comparison between snapshots
- **Storage layer**: local filesystem with XDG-compliant default paths
- **Shell completions**: bash, fish, zsh
- **Export service with progress logging and stat cards** (GUI)
- **Theme engine**: light/dark/system themes, configurable accent colors, density modes
- **Window persistence**: geometry and state restored across sessions
- **Keyboard shortcuts**: Ctrl+1 through Ctrl+9 for panel navigation
- **Configuration**: `~/.config/setupvault/config.toml` with all settings
- **Pre-commit hooks**: ruff lint/format, mypy, trailing-whitespace, end-of-file-fixer, YAML/TOML validation
