function __fzf_starstar_tab
    set -l token (commandline -t)
    if string match -qr '\*\*$' -- "$token"
        commandline -t -- (string replace -r '\*\*$' '' -- "$token")
        if functions -q fzf-file-widget
            fzf-file-widget
        else
            fzf_open_file
        end
        return
    end
    commandline -f complete
end
