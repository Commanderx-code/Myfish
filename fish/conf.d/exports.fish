# ---------------------------------------------------------
# Environment & PATH
# ---------------------------------------------------------

# XDG Base Directories
set -x XDG_DATA_HOME  "$HOME/.local/share"
set -x XDG_CONFIG_HOME "$HOME/.config"
set -x XDG_STATE_HOME  "$HOME/.local/state"
set -x XDG_CACHE_HOME  "$HOME/.cache"

# Editor
set -x EDITOR nvim
set -x VISUAL nvim

# PATH
fish_add_path $HOME/.local/bin
fish_add_path $HOME/.cargo/bin
fish_add_path /var/lib/flatpak/exports/bin
fish_add_path $HOME/.local/share/flatpak/exports/bin
