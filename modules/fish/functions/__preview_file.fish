function __preview_file --argument-names file line
    test -z "$file"; and return

    set file (string replace -r '^~' $HOME -- "$file")

    if not test -e "$file"
        echo "File not found:"
        echo "$file"
        return
    end

    if test -d "$file"
        if command -q eza
            eza -la --tree --level=2 --icons=always --color=always "$file" 2>/dev/null | head -300
        else
            ls -la "$file" 2>/dev/null
        end
        return
    end

    set mime (file --mime-type -Lb "$file" 2>/dev/null)

    switch "$mime"
        case 'text/*' 'application/json' 'application/xml' 'application/x-shellscript' 'application/javascript' 'application/toml'
            if test -n "$line"
                set start (math "$line - 200")
                test $start -lt 1; and set start 1
                set end (math "$line + 200")

                if command -q bat
                    bat --style=numbers --color=always --line-range "$start:$end" --highlight-line "$line" "$file" 2>/dev/null
                else
                    sed -n "$start,$end p" "$file" 2>/dev/null
                end
            else
                if command -q bat
                    bat --style=numbers --color=always --line-range :400 "$file" 2>/dev/null
                else
                    sed -n '1,400p' "$file" 2>/dev/null
                end
            end

        case 'application/pdf'
            if command -q pdftotext
                pdftotext -l 3 "$file" - 2>/dev/null | sed -n '1,220p'
            else
                file "$file"
            end

        case '*'
            file "$file"
            echo
            echo "No text preview for this file type:"
            echo "$mime"
    end
end
