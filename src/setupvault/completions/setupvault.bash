_setupvault_completions() {
    local cur prev words cword
    _init_completion || return

    local commands="export restore info validate report doctor diff list"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    case "${words[1]}" in
        export)
            case "$prev" in
                --profile|-p)
                    COMPREPLY=($(compgen -W "full minimal packages-only" -- "$cur"))
                    ;;
                --output|-o)
                    _filedir
                    ;;
                --exclude|-e)
                    COMPREPLY=($(compgen -W "system environment shell packages themes fonts dotfiles" -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--profile -p --output -o --compress --exclude -e --help" -- "$cur"))
                    ;;
            esac
            ;;
        restore)
            case "$prev" in
                --profile|-p)
                    COMPREPLY=($(compgen -W "full minimal packages-only" -- "$cur"))
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--profile -p --dry-run --apply --yes -y --help" -- "$cur"))
                    ;;
            esac
            ;;
        info|validate)
            _filedir
            ;;
        report)
            case "$prev" in
                --format|-f)
                    COMPREPLY=($(compgen -W "markdown json html" -- "$cur"))
                    ;;
                --output|-o)
                    _filedir
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--format -f --output -o --help" -- "$cur"))
                    ;;
            esac
            ;;
        doctor)
            COMPREPLY=($(compgen -W "python_version distro_detected shell_detected config_dir_exists snapshots_dir_exists sudo_available pacman_available gsettings_available fc_cache_available" -- "$cur"))
            ;;
        diff)
            _filedir
            ;;
        list)
            case "$prev" in
                --dir|-d)
                    _filedir -d
                    ;;
                *)
                    COMPREPLY=($(compgen -W "--dir -d --help" -- "$cur"))
                    ;;
            esac
            ;;
    esac
} &&
complete -F _setupvault_completions setupvault
