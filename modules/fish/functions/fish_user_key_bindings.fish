function fish_user_key_bindings
    if functions -q fzf_key_bindings
        fzf_key_bindings
    end
    bind \cp fzf_open_file
    bind \cf fzf_rg_search
    if functions -q fzf-history-widget
        bind \ch fzf-history-widget
    end
    # Keep Ctrl-R available, including terminals that send Backspace as Ctrl-H.
    bind \t __fzf_starstar_tab
end
