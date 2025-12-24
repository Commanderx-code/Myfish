# ---------------------------------------------------------
# Safe apt / apt-get wrappers using Nala
# ---------------------------------------------------------

function apt
    command nala $argv
end

function apt-get
    command nala $argv
end

function sudo
    set cmd $argv[1]
    switch $cmd
        case apt
            command sudo nala $argv[2..-1]
        case apt-get
            command sudo nala $argv[2..-1]
        case '*'
            command sudo $argv
    end
end
