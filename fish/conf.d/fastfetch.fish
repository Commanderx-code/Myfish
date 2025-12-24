# ---------------------------------------------------------
# Fastfetch (login only)
# ---------------------------------------------------------
if status is-login
    if command -v fastfetch >/dev/null
        fastfetch
    end
end
