if test (uname -s) = Darwin
    if not set -q HOMEBREW_PREFIX
        if test -x /opt/homebrew/bin/brew
            set -gx HOMEBREW_PREFIX /opt/homebrew
        else if test -x /usr/local/bin/brew
            set -gx HOMEBREW_PREFIX /usr/local
        end
    end
    if set -q HOMEBREW_PREFIX
        # Append here so Nix tools keep priority in Home Manager sessions.
        fish_add_path --append --path "$HOMEBREW_PREFIX/bin" "$HOMEBREW_PREFIX/sbin"
        fish_add_path --append --path "$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin" "$HOMEBREW_PREFIX/opt/gnu-tar/libexec/gnubin" "$HOMEBREW_PREFIX/opt/trash-cli/bin"
    end
end
