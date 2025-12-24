# ---------------------------------------------------------
# Main Fish Config (minimal — modularized via conf.d/)
# ---------------------------------------------------------

# Modular loading happens automatically:
# - conf.d/*.fish loads on every shell
# - functions/*.fish autoload when needed

# Login shell greeting
if status is-login
    echo "⚡ Welcome back, commander"
end
