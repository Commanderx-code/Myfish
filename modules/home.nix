{
  pkgs,
  lib,
  machine,
  ...
}:
let
  shell = machine.shell or (if machine.features.fish then "fish" else "keep");
in
{
  home.username = machine.username;
  home.homeDirectory = machine.homeDirectory;
  # Preserve this value for existing installations when updating packages.
  home.stateVersion = "26.05";
  programs.home-manager.enable = true;
  targets.genericLinux.enable = pkgs.stdenv.isLinux;
  xdg.enable = true;
  fonts.fontconfig.enable = pkgs.stdenv.isLinux;
  home.packages =
    with pkgs;
    [
      # Keep login shells available if the user declines a later shell change.
      bashInteractive
      fish
      zsh
      ripgrep
      fd
      bat
      eza
      jq
      nerd-fonts.jetbrains-mono
    ]
    ++ lib.optionals (shell != "keep") (
      with pkgs;
      [
        fastfetch
        broot
        chafa
        file
        poppler-utils
        trash-cli
        unzip
        p7zip
        gnutar
        gzip
        bzip2
        xz
        python3
        git
      ]
    )
    ++ lib.optionals (shell != "keep" && pkgs.stdenv.isLinux) [ pkgs.libnotify ]
    ++ lib.optionals (shell != "keep" && pkgs.stdenv.isDarwin) [
      pkgs.coreutils
      pkgs.findutils
    ]
    ++ lib.optionals (shell == "bash") [ pkgs.blesh ];
  home.sessionPath = lib.optionals pkgs.stdenv.isDarwin [
    (if pkgs.stdenv.hostPlatform.isAarch64 then "/opt/homebrew/bin" else "/usr/local/bin")
  ];
  home.file."Library/Fonts/Commander-os" = lib.mkIf pkgs.stdenv.isDarwin {
    source = "${pkgs.nerd-fonts.jetbrains-mono}/share/fonts/truetype/NerdFonts/JetBrainsMono";
    recursive = true;
  };
  xdg.configFile = {
    "nvim/lua" = lib.mkIf machine.features.neovim {
      source = ./neovim/lua;
      recursive = true;
    };
    "nvim/LICENSE" = lib.mkIf machine.features.neovim { source = ./neovim/LICENSE; };
    "nvim/UPSTREAM.md" = lib.mkIf machine.features.neovim { source = ./neovim/UPSTREAM.md; };
    "nvim/stylua.toml" = lib.mkIf machine.features.neovim { source = ./neovim/stylua.toml; };
    "commander-os/greeting.txt" = lib.mkIf (shell != "keep") {
      text =
        lib.replaceStrings [ "{user}" ] [ machine.username ] (machine.greeting or "Hello, {user} ⚡") + "\n";
    };
    "fastfetch/config.jsonc" = lib.mkIf (shell != "keep") {
      source = ./fastfetch.jsonc;
    };
    "fastfetch/png" = lib.mkIf (shell != "keep") {
      source = ./fastfetch-png;
      recursive = true;
    };
    "fish/conf.d" = lib.mkIf (shell == "fish") {
      source = ./fish/conf.d;
      recursive = true;
    };
    "fish/functions" = lib.mkIf (shell == "fish") {
      source = ./fish/functions;
      recursive = true;
    };
  };
  home.file.".local/bin/fzf-preview" = lib.mkIf (shell != "keep") {
    source = ./fzf-preview;
    executable = true;
  };
  programs.fish = lib.mkIf (shell == "fish") {
    enable = true;
    interactiveShellInit = lib.mkAfter "fish_user_key_bindings";

  };
  programs.bash = lib.mkIf (shell == "bash") {
    enable = true;
    bashrcExtra = lib.mkBefore ''
      COMMANDER_BLE_FILE=${pkgs.blesh}/share/blesh/ble.sh
      source ${./shell/ble-start.sh}
    '';
    initExtra = lib.mkOrder 3000 ''
      source ${./shell/common.sh}
      source ${./shell/bash.sh}
      source ${./shell/ble-finish.sh}
    '';
  };
  programs.zsh = lib.mkIf (shell == "zsh") {
    enable = true;
    autosuggestion.enable = true;
    syntaxHighlighting.enable = true;
    initContent = lib.mkAfter ''
      ZSH_AUTOSUGGEST_STRATEGY=(history completion)
      ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=244"
      source ${./shell/common.sh}
      source ${./shell/zsh.zsh}
    '';
  };
  programs.starship = {
    enable = shell != "keep";
    enableFishIntegration = shell == "fish";
    enableBashIntegration = shell == "bash";
    enableZshIntegration = shell == "zsh";
    settings = builtins.fromTOML (builtins.readFile ./starship.toml);
  };
  programs.zellij = lib.mkIf (shell != "keep") {
    enable = true;
    enableFishIntegration = false;
    enableBashIntegration = false;
    enableZshIntegration = false;
    settings = {
      theme = "tokyo-night-storm";
      default_mode = "locked";
      default_shell =
        if shell == "bash" then "${pkgs.bashInteractive}/bin/bash" else "${pkgs.${shell}}/bin/${shell}";
    };
  };
  programs.fzf = {
    enable = true;
    enableFishIntegration = shell == "fish";
    enableBashIntegration = false; # ble.sh owns the Bash fzf integration.
    enableZshIntegration = shell == "zsh";
  };
  programs.zoxide = {
    enable = true;
    enableFishIntegration = shell == "fish";
    enableBashIntegration = shell == "bash";
    enableZshIntegration = shell == "zsh";
  };
  programs.neovim = lib.mkIf machine.features.neovim {
    enable = true;
    extraPackages = with pkgs; [
      git
      curl
      unzip
      gnutar
      gzip
      tree-sitter
      stdenv.cc
    ];
    initLua = builtins.readFile ./neovim/init.lua;
  };
  programs.git.enable = machine.features.development;
  programs.lazygit.enable = machine.features.development;
}
