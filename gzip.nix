(import <nixpkgs> {}).gzip.overrideAttrs (a: {patches = [./0001-gzip-logs.patch];})
