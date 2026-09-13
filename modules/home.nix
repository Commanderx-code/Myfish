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
  home.packages = with pkgs; [
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
  ];
  programs.fish = lib.mkIf (shell == "fish") {
    enable = true;
    shellAliases = {
      ll = "eza -la";
      gs = "git status";
    };
  };
  programs.bash = lib.mkIf (shell == "bash") {
    enable = true;
    shellAliases = {
      ll = "eza -la";
      gs = "git status";
    };
  };
  programs.zsh = lib.mkIf (shell == "zsh") {
    enable = true;
    shellAliases = {
      ll = "eza -la";
      gs = "git status";
    };
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
