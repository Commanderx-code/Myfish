{
  pkgs,
  lib,
  machine,
  ...
}:
{
  home.username = machine.username;
  home.homeDirectory = machine.homeDirectory;
  # Preserve this value for existing installations when updating packages.
  home.stateVersion = "26.05";
  programs.home-manager.enable = true;
  targets.genericLinux.enable = true;
  xdg.enable = true;
  home.packages = with pkgs; [
    ripgrep
    fd
    bat
    eza
    jq
  ];
  programs.fish = lib.mkIf machine.features.fish {
    enable = true;
    shellAliases = {
      ll = "eza -la";
      gs = "git status";
    };
  };
  programs.starship = {
    enable = machine.features.fish;
    enableFishIntegration = machine.features.fish;
    settings = {
      add_newline = false;
      character.success_symbol = "[❯](bold green)";
    };
  };
  programs.fzf = {
    enable = true;
    enableFishIntegration = machine.features.fish;
  };
  programs.zoxide = {
    enable = true;
    enableFishIntegration = machine.features.fish;
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
