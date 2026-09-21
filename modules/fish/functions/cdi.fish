function cdi --description 'Fuzzy cd, including hidden and nested directories'
    __commander_pick_directory --hidden --follow --exclude .git
end
