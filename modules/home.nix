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
  targets.genericLinux.enable = true;
  xdg.enable = true;
  fonts.fontconfig.enable = true;
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
        libnotify
        git
      ]
    );
  xdg.configFile = {
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
    initExtra = lib.mkAfter ''
      source ${./shell/common.sh}
      source ${./shell/bash.sh}
    '';
  };
  programs.zsh = lib.mkIf (shell == "zsh") {
    enable = true;
    autosuggestion.enable = true;
    syntaxHighlighting.enable = true;
    initContent = lib.mkAfter ''
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
  programs.fzf = {
    enable = true;
    enableFishIntegration = shell == "fish";
    enableBashIntegration = shell == "bash";
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
    initLua = ''
      vim.opt.number = true
      vim.opt.relativenumber = true
      vim.opt.expandtab = true
      vim.opt.shiftwidth = 2
      vim.opt.tabstop = 2
      vim.opt.ignorecase = true
      vim.opt.smartcase = true
      vim.opt.termguicolors = true
      vim.g.mapleader = " "
    '';
  };
  programs.git.enable = machine.features.development;
  programs.lazygit.enable = machine.features.development;
}
