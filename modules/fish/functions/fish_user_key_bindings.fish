function fish_user_key_bindings
    if functions -q fzf_key_bindings
        fzf_key_bindings
    end
    bind \cp fzf_open_file
    bind \cf fzf_rg_search
    # Ctrl-H opens history search too; Ctrl-R keeps fzf's own binding.
    if functions -q fzf-history-widget
        bind \ch fzf-history-widget
    end
    # Tab expands a trailing ** through fzf and otherwise completes as usual.
    bind \t __fzf_starstar_tab
end
