alias spico="sudo pico"
alias snano="sudo nano"
alias vim="nvim"

alias web="cd /var/www/html"
alias da='date "+%Y-%m-%d %A %T %Z"'
alias cp="cp -i"
alias mv="mv -i"
alias rm="trash -v"
alias mkdir="mkdir -p"

# Use batcat by default
alias cat="batcat"

# Escape hatches
alias ccat="/bin/cat"
alias rbatcat="/usr/bin/batcat"

alias ping="ping -c 10"
alias cls="clear"
alias ps="ps auxf"
alias less="less -R"
alias fd="fdfind"
alias grep="rg"

alias home="cd ~"

# Directory jumps
if status is-interactive
    abbr -a ..     'cd ..'
    abbr -a ...    'cd ../..'
    abbr -a ....   'cd ../../..'
    abbr -a .....  'cd ../../../..'
    abbr -a bd     'cd -'
    abbr -a home   'cd ~'
    abbr -a up 'update'
    abbr -a ug 'upgrade'
    abbr -a fu 'full-upgrade'
    abbr -a cl 'cleanup'
    abbr -a tg "topgrade"

end

alias topcpu="/bin/ps -eo pcpu,pid,user,args | sort -k 1 -r | head -10"
alias clickpaste='sleep 3; xdotool type (xclip -o -selection clipboard)'
alias kssh="kitty +kitten ssh"
alias sha1="openssl sha1"
alias mountedinfo="df -hT"
alias docker-clean='docker container prune -f; docker image prune -f; docker network prune -f; docker volume prune -f'
alias hug="systemctl --user restart hugo"
alias lanm="systemctl --user restart lan-mouse"

# Fuzzy search inside files (rg + fzf)
function rgi
    rg --line-number --no-heading --color=always $argv \
    | fzf --ansi --delimiter ':' \
          --preview 'batcat --style=numbers --color=always {1} --highlight-line {2}'
end

# Fuzzy file finder
function fdi
    set file (fd . | fzf --preview 'batcat --color=always {}')
    test -n "$file"; and nvim "$file"
end

# Fuzzy cd
function cdi
    set dir (fd --type d . | fzf)
    test -n "$dir"; and cd "$dir"
end
