function extract --description 'Extract an archive into the current directory'
    if test (count $argv) -ne 1; or not test -f "$argv[1]"
        echo 'Usage: extract <archive-file>' >&2
        return 1
    end
    set -l archive (path resolve -- "$argv[1]")
    switch "$archive"
        case '*.tar' '*.tar.gz' '*.tgz' '*.tar.bz2' '*.tbz2' '*.tar.xz' '*.txz' '*.tar.zst'
            command tar -xf "$archive"
        case '*.zip'
            command unzip "$archive"
        case '*.gz'
            command gunzip -- "$archive"
        case '*.bz2'
            command bunzip2 -- "$archive"
        case '*.xz'
            command unxz -- "$archive"
        case '*.7z' '*.rar'
            if command -q 7z
                command 7z x "$archive"
            else
                command 7zz x "$archive"
            end
        case '*'
            echo "Unsupported archive: $archive" >&2
            return 1
    end
end
