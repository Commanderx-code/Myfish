# shellcheck shell=bash
# Load before Starship; defer taking over the terminal until startup is complete.
case $- in *i*) ;; *) return ;; esac
if [[ -t 0 && -t 1 && -z ${BLE_VERSION-} && ${COMMANDER_BLE:-1} != 0 ]]; then
  _commander_ble=${COMMANDER_BLE_FILE:-$HOME/.local/share/blesh/ble.sh}
  if [[ -r $_commander_ble ]]; then
    command mkdir -p -- "${XDG_CACHE_HOME:-$HOME/.cache}"
    # shellcheck disable=SC1090
    source -- "$_commander_ble" --attach=none
  else
    printf 'Commander-os: ble.sh is missing; rerun the Bash installer.\n' >&2
  fi
  unset _commander_ble
fi
