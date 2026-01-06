# Go environment (Fish)

# Where Go workspace lives
set -Ux GOPATH $HOME/go

# Where "go install" drops binaries
set -Ux GOBIN $GOPATH/bin

# Add Go bins to PATH safely (no duplicates, no reorder chaos)
# Only add if the directories exist
if test -d /usr/local/go/bin
    fish_add_path -g /usr/local/go/bin
end

if test -d $GOBIN
    fish_add_path -g $GOBIN
end
