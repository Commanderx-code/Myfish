# ---------------------------------------------------------
# General Aliases
# ---------------------------------------------------------

alias spico="sudo pico"
alias snano="sudo nano"
alias vim="nvim"

alias web="cd /var/www/html"

alias da='date "+%Y-%m-%d %A %T %Z"'

alias cp="cp -i"
alias mv="mv -i"
alias rm="trash -v"
alias mkdir="mkdir -p"

alias ping="ping -c 10"
alias cls="clear"
alias ps="ps auxf"
alias less="less -R"

alias home="cd ~"

# Directory jumps
if status is-interactive
    abbr -a ..     'cd ..'
    abbr -a ...    'cd ../..'
    abbr -a ....   'cd ../../..'
    abbr -a .....  'cd ../../../..'
    abbr -a bd     'cd -'
    abbr -a home   'cd ~'
end

alias topcpu="/bin/ps -eo pcpu,pid,user,args | sort -k 1 -r | head -10"

alias clickpaste='sleep 3; xdotool type (xclip -o -selection clipboard)'
alias kssh="kitty +kitten ssh"

alias sha1="openssl sha1"
alias mountedinfo="df -hT"

alias docker-clean='docker container prune -f; docker image prune -f; docker network prune -f; docker volume prune -f'

alias hug="systemctl --user restart hugo"
alias lanm="systemctl --user restart lan-mouse"
