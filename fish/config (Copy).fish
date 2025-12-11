# -----------------------------
# Fish Core Environment
# -----------------------------

# XDG Base Directories
set -Ux XDG_DATA_HOME $HOME/.local/share
set -Ux XDG_CONFIG_HOME $HOME/.config
set -Ux XDG_STATE_HOME $HOME/.local/state
set -Ux XDG_CACHE_HOME $HOME/.cache

# Editor
set -Ux EDITOR nvim
set -Ux VISUAL nvim

# PATH
set -Ux PATH $PATH \
    $HOME/.local/bin \
    $HOME/.cargo/bin \
    /var/lib/flatpak/exports/bin \
    $HOME/.local/share/flatpak/exports/bin

# -----------------------------
# Starship + Zoxide + Fastfetch
# -----------------------------

starship init fish | source
zoxide init fish | source

echo "⚡ Welcome back, commander"
status is-interactive; and fastfetch

# -----------------------------
# Aliases
# -----------------------------

alias spico="sudo pico"
alias snano="sudo nano"
alias vim="nvim"

alias web="cd /var/www/html"
alias alert='notify-send --urgency=low (test $status -eq 0; and echo terminal; or echo error) (history | tail -n1)'

alias ebrc="nvim ~/.bashrc"
alias da='date "+%Y-%m-%d %A %T %Z"'

alias cp="cp -i"
alias mv="mv -i"
alias rm="trash -v"
alias mkdir="mkdir -p"
alias ps="ps auxf"
alias ping="ping -c 10"
alias less="less -R"
alias cls="clear"
alias apt-get="sudo apt-get"
alias multitail="multitail --no-repeat -c"
alias freshclam="sudo freshclam"
alias vi="nvim"
alias svi="sudo vi"
alias vis='nvim "+set si"'

alias home="cd ~"
alias cd..="cd .."
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."
alias bd="cd -"

alias rmd="/bin/rm --recursive --force --verbose"

alias la="ls -Alh"
alias ls="ls -aFh --color=always"
alias lx="ls -lXBh"
alias lk="ls -lSrh"
alias lc="ls -ltcrh"
alias lu="ls -lturh"
alias lr="ls -lRh"
alias lt="ls -ltrh"
alias lm="ls -alh | more"
alias lw="ls -xAh"
alias ll="ls -Fls"
alias labc="ls -lap"
alias lf="ls -l | egrep -v '^d'"
alias ldir="ls -l | egrep '^d'"
alias lla="ls -Al"
alias las="ls -A"
alias lls="ls -l"

alias mx="chmod a+x"
alias 000="chmod -R 000"
alias 644="chmod -R 644"
alias 666="chmod -R 666"
alias 755="chmod -R 755"
alias 777="chmod -R 777"

alias h="history | grep "
alias p="ps aux | grep "
alias topcpu="/bin/ps -eo pcpu,pid,user,args | sort -k 1 -r | head -10"
alias f="find . | grep "
alias diskspace="du -S | sort -n -r | more"
alias folders="du -h --max-depth=1"
alias treed="tree -CAFd"
alias mountedinfo="df -hT"

alias mktar="tar -cvf"
alias mkbz2="tar -cvjf"
alias mkgz="tar -cvzf"
alias untar="tar -xvf"
alias unbz2="tar -xvjf"
alias ungz="tar -xvzf"

function logs
    sudo find /var/log -type f -exec file {} \; \
        | grep text \
        | cut -d" " -f1 \
        | sed 's/:$//' \
        | xargs tail -f
end

alias sha1="openssl sha1"
alias clickpaste='sleep 3; xdotool type (xclip -o -selection clipboard)'
alias kssh="kitty +kitten ssh"
alias docker-clean='docker container prune -f; docker image prune -f; docker network prune -f; docker volume prune -f'

alias hug="systemctl --user restart hugo"
alias lanm="systemctl --user restart lan-mouse"

# -----------------------------
# Git Functions
# -----------------------------

function gcom
    git add .
    git commit -m "$argv"
end

# -----------------------------
# Apt-nala update
# -----------------------------

function apt
    command nala $argv
end

function apt-get
    command nala $argv
end

function sudo
    if test (count $argv) -ge 1; and test $argv[1] = "apt"
        command sudo nala $argv[2..-1]
    else if test (count $argv) -ge 1; and test $argv[1] = "apt-get"
        command sudo nala $argv[2..-1]
    else
        command sudo $argv
    end
end

# -----------------------------
# update all 
# -----------------------------

function updateall
    sudo nala update; and sudo nala upgrade -y; and flatpak update -y; and sudo snap refresh
end

# -----------------------------
# Fish utils
# -----------------------------

function mkcd
    mkdir -p $argv[1]; and cd $argv[1]
end

# Universal archive extractor
function extract
    if test -f $argv[1]
        switch $argv[1]
            case "*.tar.bz2"
                tar xvjf $argv[1]
            case "*.tar.gz"
                tar xvzf $argv[1]
            case "*.bz2"
                bunzip2 $argv[1]
            case "*.rar"
                unrar x $argv[1]
            case "*.gz"
                gunzip $argv[1]
            case "*.tar"
                tar xvf $argv[1]
            case "*.tbz2"
                tar xvjf $argv[1]
            case "*.tgz"
                tar xvzf $argv[1]
            case "*.zip"
                unzip $argv[1]
            case "*.Z"
                uncompress $argv[1]
            case "*.7z"
                7z x $argv[1]
            case "*"
                echo "❌ Cannot extract: $argv[1]"
        end
    else
        echo "❌ File does not exist: $argv[1]"
    end
end

# Quick Python web server in current directory
function serve
    set port 8000
    if test (count $argv) -ge 1
        set port $argv[1]
    end
    python3 -m http.server $port
end

# Search for running processes (better than ps | grep)
function psg
    ps aux | grep -i $argv[1] | grep -v grep
end

# Show size of current directory
function dirsize
    du -sh .
end

# -----------------------------
# EZA (modern ls replacement)
# -----------------------------

# -----------------------------
# EZA (modern ls replacement)
# -----------------------------

# Keep colors consistent everywhere
set -Ux EZA_COLORS \
"da=1;34:\
di=1;36:\
fi=0;37:\
ex=1;32:\
*.zip=1;31:\
*.tar=1;31:\
*.gz=1;31:\
*.jpg=1;35:\
*.png=1;35"

# Basic replacement
alias ls="eza --icons --group-directories-first --colour=always"

# Long listing
alias ll="eza -lh --icons --group-directories-first --time-style=long-iso"

# All files (including hidden)
alias la="eza -lha --icons --group-directories-first"

# Tree view
alias tree="eza --tree --level=2 --icons"

# Sort variations
alias lx="eza -lh --sort=extension --icons"
alias lk="eza -lh --sort=size --icons"
alias lt="eza -lh --sort=modified --icons"

# List only directories / files
alias ldir="eza -l --icons --filter=dir"
alias lf="eza -l --icons --filter=file"

# Git-aware listing
alias lg="eza -l --git --icons"

# One-column list
alias l1="eza -1 --icons"

# Recursive list
alias lr="eza -R --icons"

# -----------------------------
# FZF + EZA Preview Integration
# -----------------------------

set -Ux NNN_FIFO /tmp/nnn.fifo
set -Ux NNN_OPTS "e"
set -Ux FZF_DEFAULT_COMMAND "eza --icons --recurse --ignore-glob=.git --color=always"
set -Ux FZF_DEFAULT_OPTS "--ansi --preview 'eza --icons --tree --level=3 --color=always {} | head -200'"

function fcd
    set dir (eza -D --color=always | fzf)
    cd $dir
end







