function fish_user_key_bindings
    if functions -q fzf_key_bindings
        fzf_key_bindings
    end
    bind \cp fzf_open_file
    bind \cf fzf_rg_search
    # History search stays on fzf's own Ctrl-R binding.
    # Tab expands a trailing ** through fzf and otherwise completes as usual.
    bind \t __fzf_starstar_tab
end
