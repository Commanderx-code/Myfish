# ---------------------------------------------------------
# Environment & PATH
# ---------------------------------------------------------

# XDG Base Directories
set -gx XDG_DATA_HOME  "$HOME/.local/share"
set -gx XDG_CONFIG_HOME "$HOME/.config"
set -gx XDG_STATE_HOME  "$HOME/.local/state"
set -gx XDG_CACHE_HOME  "$HOME/.cache"

# Bat behavior
set -gx BAT_PAGER ""

# Editor
set -gx EDITOR nvim
set -gx VISUAL nvim

# PATH (Fish-native)

# User bins (highest priority)
if test -d "$HOME/.local/bin"
    fish_add_path -g "$HOME/.local/bin"
end

# Linuxbrew (if installed)
if test -d "/home/linuxbrew/.linuxbrew/bin"
    fish_add_path -g "/home/linuxbrew/.linuxbrew/bin"
end
if test -d "/home/linuxbrew/.linuxbrew/sbin"
    fish_add_path -g "/home/linuxbrew/.linuxbrew/sbin"
end

# Rust/Cargo bins
if test -d "$HOME/.cargo/bin"
    fish_add_path -g "$HOME/.cargo/bin"
end

# Flatpak exports
if test -d "/var/lib/flatpak/exports/bin"
    fish_add_path -g "/var/lib/flatpak/exports/bin"
end
if test -d "$HOME/.local/share/flatpak/exports/bin"
    fish_add_path -g "$HOME/.local/share/flatpak/exports/bin"
end

# Snap (optional)
if test -d "/snap/bin"
    fish_add_path -g "/snap/bin"
end
