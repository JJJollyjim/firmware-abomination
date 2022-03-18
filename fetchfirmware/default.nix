{ stdenv, python3, lib, cacert }:
{ syncpoints, offsets, sha256, url, deflate_offset_in_ipsw }:
stdenv.mkDerivation {
  name = "firmware";
  builder = ./builder.sh;
  nativeBuildInputs = [ (python3.withPackages (p: [p.urllib3])) cacert ];
  inherit syncpoints offsets url deflate_offset_in_ipsw;

  downloader = ./downloader.py;

  outputHash = sha256;
  outputHashAlgo = "sha256";
  outputHashMode = "recursive";

  meta.license = lib.licenses.unfree;
}
