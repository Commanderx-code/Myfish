{
  description = "Commander-os: a portable Linux home environment";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
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
          packages = with nixpkgs.legacyPackages.${system}; [
            python3
            fish
            zsh
            shellcheck
          ];
        };
      });
      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt);
    };
}
