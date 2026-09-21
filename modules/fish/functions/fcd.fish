function fcd --description 'Fuzzy cd to an immediate, visible subdirectory'
    __commander_pick_directory --max-depth 1 --no-ignore --follow
end
