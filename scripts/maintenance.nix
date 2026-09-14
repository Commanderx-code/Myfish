# Used only by lifecycle.py in a curated temporary flake, with the project lock.
{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
  inputs.home-manager = {
    url = "github:nix-community/home-manager";
    inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs =
    { nixpkgs, home-manager, ... }:
    let
      machine = builtins.fromJSON (builtins.readFile ./machine.json);
      # Retention deliberately refers to the active local generation.
      original = builtins.storePath (builtins.fromJSON (builtins.readFile ./generation.json));
      pkgs = nixpkgs.legacyPackages.${machine.system};
    in
    {
      packages.${machine.system} = {
        remove =
          (home-manager.lib.homeManagerConfiguration {
            inherit pkgs;
            modules = [
              {
                home.username = machine.username;
                home.homeDirectory = machine.homeDirectory;
                uninstall = true;
              }
            ];
          }).activationPackage;
        retained = pkgs.runCommand "commander-os-retained" { } ''
          shopt -s dotglob nullglob
          mkdir -p $out/bin
          for entry in ${original}/home-path/*; do
            name=$(basename "$entry")
            if [ "$name" != bin ]; then ln -s "$entry" "$out/$name"; fi
          done
          for entry in ${original}/home-path/bin/*; do
            name=$(basename "$entry")
            if [ "$name" != home-manager ]; then ln -s "$entry" "$out/bin/$name"; fi
          done
        '';
      };
    };
}
