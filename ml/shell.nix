{ pkgs ? import <nixpkgs> {} }:
(pkgs.buildFHSEnv {
  name = "ml-env";
  targetPkgs = pkgs: with pkgs; [
    uv
    python313
    stdenv.cc.cc.lib
    expat
    zlib
  ];
}).env
