status is-interactive; or return
# Without eza, ls and tree keep their usual meaning.
command -q eza; or return
# ---------------------------------------------------------
# EZA - Modern ls Replacement
# ---------------------------------------------------------

# Colors
set -x EZA_COLORS \
"da=1;34:\
di=1;36:\
fi=0;37:\
ex=1;32:\
*.zip=1;31:\
*.tar=1;31:\
*.gz=1;31:\
*.jpg=1;35:\
*.png=1;35"
