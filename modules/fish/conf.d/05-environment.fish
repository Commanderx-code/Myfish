# Session defaults also apply to noninteractive Fish. Preserve user overrides.
set -q BAT_PAGER; or set -gx BAT_PAGER ''
for directory in "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/go/bin"
    if test -d "$directory"
        fish_add_path --global --path "$directory"
    end
end
if command -q nvim
    set -q EDITOR; or set -gx EDITOR nvim
    set -q VISUAL; or set -gx VISUAL nvim
end
