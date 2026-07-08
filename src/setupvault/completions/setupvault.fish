complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "export" -d "Export system configuration to a snapshot file"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "restore" -d "Restore system configuration from a snapshot file"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "info" -d "Display information about a snapshot"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "validate" -d "Validate a snapshot file"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "report" -d "Generate a report from a snapshot"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "doctor" -d "Run system diagnostics"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "diff" -d "Compare two snapshots"
complete -c setupvault -f -n "not __fish_seen_subcommand_from export restore info validate report doctor diff list" \
    -a "list" -d "List available snapshots"

# export
complete -c setupvault -n "__fish_seen_subcommand_from export" -l profile -s p -r \
    -a "full minimal packages-only" -d "Profile to use"
complete -c setupvault -n "__fish_seen_subcommand_from export" -l output -s o -r \
    -F -d "Output path"
complete -c setupvault -n "__fish_seen_subcommand_from export" -l compress -d "Compress snapshot"
complete -c setupvault -n "__fish_seen_subcommand_from export" -l exclude -s e -r \
    -a "system environment shell packages themes fonts dotfiles" -d "Section to exclude"

# restore
complete -c setupvault -n "__fish_seen_subcommand_from restore" -l profile -s p -r \
    -a "full minimal packages-only" -d "Profile to use"
complete -c setupvault -n "__fish_seen_subcommand_from restore" -l dry-run -d "Preview changes without applying"
complete -c setupvault -n "__fish_seen_subcommand_from restore" -l apply -d "Apply changes"
complete -c setupvault -n "__fish_seen_subcommand_from restore" -l yes -s y -d "Skip confirmation"

# info / validate
complete -c setupvault -n "__fish_seen_subcommand_from info" -r -F -d "Snapshot file"
complete -c setupvault -n "__fish_seen_subcommand_from validate" -r -F -d "Snapshot file"

# report
complete -c setupvault -n "__fish_seen_subcommand_from report" -l format -s f -r \
    -a "markdown json" -d "Output format"
complete -c setupvault -n "__fish_seen_subcommand_from report" -l output -s o -r \
    -F -d "Output file"

# doctor
complete -c setupvault -n "__fish_seen_subcommand_from doctor" -l -r \
    -a "python_version distro_detected shell_detected config_dir_exists snapshots_dir_exists sudo_available pacman_available gsettings_available fc_cache_available"

# diff
complete -c setupvault -n "__fish_seen_subcommand_from diff" -r -F -d "Left snapshot"
complete -c setupvault -n "__fish_seen_subcommand_from diff" -r -F -d "Right snapshot"

# list
complete -c setupvault -n "__fish_seen_subcommand_from list" -l dir -s d -r \
    -F -d "Snapshot directory"
