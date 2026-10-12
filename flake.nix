{
  description = "Myfish: a portable Linux and macOS home environment";
  inputs = {
    # The 26.05 release is the last that supports Intel Macs (x86_64-darwin);
    # it receives security fixes until the end of 2026.
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-26.05-darwin";
    home-manager = {
      url = "github:nix-community/home-manager/release-26.05";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs =
    { nixpkgs, home-manager, ... }:
    let
      machine = builtins.fromJSON (
        builtins.readFile (
          if builtins.pathExists ./machine.json then ./machine.json else ./machine.example.json
        )
      );
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      makeHome =
        system:
        home-manager.lib.homeManagerConfiguration {
          pkgs = nixpkgs.legacyPackages.${system};
          extraSpecialArgs = { inherit machine; };
          modules = [ ./modules/home.nix ];
        };
    in
    {
      homeConfigurations.commander = makeHome machine.system;
      checks = forAllSystems (system: {
        home = (makeHome system).activationPackage;
      });
      devShells = forAllSystems (system: {
        default = nixpkgs.legacyPackages.${system}.mkShell {
          COMMANDER_TEST_BASH = "${nixpkgs.legacyPackages.${system}.bashInteractive}/bin/bash";
          packages = with nixpkgs.legacyPackages.${system}; [
            python3
            ripgrep
            fish
            zsh
            shellcheck
            starship
          ];
        };
      });
      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt);
    };
}
