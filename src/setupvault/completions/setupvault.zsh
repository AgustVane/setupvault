#compdef setupvault

_setupvault_commands() {
    local -a commands
    commands=(
        'export:Export system configuration to a snapshot file'
        'restore:Restore system configuration from a snapshot file'
        'info:Display information about a snapshot'
        'validate:Validate a snapshot file'
        'report:Generate a report from a snapshot'
        'doctor:Run system diagnostics'
        'diff:Compare two snapshots'
        'list:List available snapshots'
    )
    _describe 'command' commands
}

_setupvault() {
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        '1: :_setupvault_commands' \
        '*::arg:->args'

    case $state in
        args)
            case $line[1] in
                export)
                    _arguments \
                        '--profile=[Profile to use]:profile:(full minimal packages-only)' \
                        '-p[Profile to use]' \
                        '--output=[Output path]:file:_files' \
                        '-o[Output path]' \
                        '--compress[Compress snapshot]' \
                        '--exclude=[Section to exclude]:section:(system environment shell packages themes fonts dotfiles)' \
                        '-e[Section to exclude]'
                    ;;
                restore)
                    _arguments \
                        '--profile=[Profile to use]:profile:(full minimal packages-only)' \
                        '-p[Profile to use]' \
                        '--dry-run[Preview changes without applying]' \
                        '--apply[Apply changes]' \
                        '--yes[Skip confirmation]' \
                        '-y[Skip confirmation]'
                    ;;
                info|validate)
                    _arguments '*:snapshot file:_files'
                    ;;
                report)
                    _arguments \
                        '--format=[Output format]:format:(markdown json html)' \
                        '-f[Output format]' \
                        '--output=[Output file]:file:_files' \
                        '-o[Output file]'
                    ;;
                doctor)
                    _arguments '*:check:(python_version distro_detected shell_detected config_dir_exists snapshots_dir_exists sudo_available pacman_available gsettings_available fc_cache_available)'
                    ;;
                diff)
                    _arguments \
                        '1:left snapshot:_files' \
                        '2:right snapshot:_files'
                    ;;
                list)
                    _arguments \
                        '--dir=[Snapshot directory]:directory:_files -/' \
                        '-d[Snapshot directory]'
                    ;;
            esac
            ;;
    esac
}

_setupvault "$@"
