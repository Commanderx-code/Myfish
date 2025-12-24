# ---------------------------------------------------------
# FZF Integration
# ---------------------------------------------------------
set -x NNN_FIFO /tmp/nnn.fifo
set -x NNN_OPTS "e"
set -x FZF_DEFAULT_COMMAND "eza --icons --recurse --ignore-glob=.git --color=always"
set -x FZF_DEFAULT_OPTS "--ansi --preview 'eza --icons --tree --level=3 --color=always {} | head -200'"
