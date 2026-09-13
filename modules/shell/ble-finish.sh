# shellcheck shell=bash
case $- in *i*) ;; *) return ;; esac
if [[ ${BLE_VERSION-} ]]; then
  bleopt complete_auto_complete=1
  bleopt highlight_syntax=1
  ble-import integration/fzf-completion
  ble-import integration/fzf-key-bindings
  ble-bind -m emacs -x C-p 'fdi'
  ble-bind -m emacs -x C-f 'rgi'
  # Right arrow accepts a suggestion; Ctrl-F remains our text-search shortcut.
  ble-attach
fi
