function extract --description 'Extract an archive into the current directory'
    if test (count $argv) -ne 1; or not test -f "$argv[1]"
        echo 'Usage: extract <archive-file>' >&2
        return 1
    end
    set -l archive (path resolve -- "$argv[1]")
    # The given name decides the format; a symlink's target may be named anything.
    set -l name (path basename -- "$argv[1]")
    switch "$name"
        case '*.tar' '*.tar.gz' '*.tgz' '*.tar.bz2' '*.tbz2' '*.tar.xz' '*.txz' '*.tar.zst'
            command tar -xf "$archive"
        case '*.zip'
            command unzip "$archive"
        # Single-file formats write here too, keep the archive and never overwrite.
        case '*.gz'
            command gunzip -c -- "$archive" >? (string replace -r '\.gz$' '' -- "$name")
        case '*.bz2'
            command bunzip2 -c -- "$archive" >? (string replace -r '\.bz2$' '' -- "$name")
        case '*.xz'
            command unxz -c -- "$archive" >? (string replace -r '\.xz$' '' -- "$name")
        case '*.7z' '*.rar'
            # unrar handles every RAR version; 7-Zip covers the rest.
            if string match -q '*.rar' -- "$name"; and command -q unrar
                command unrar x "$archive"
            else if command -q 7z
                command 7z x "$archive"
            else if command -q 7zz
                command 7zz x "$archive"
            else
                echo "Install 7-Zip to extract $archive" >&2
                return 1
            end
        case '*'
            echo "Unsupported archive: $archive" >&2
            return 1
    end
end
