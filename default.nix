let pkgs = import <nixpkgs> {};
    fetchFirmware = pkgs.callPackage ./fetchfirmware {};
in

fetchFirmware {
  url = "https://updates.cdn-apple.com/2022SpringFCS/fullrestores/071-08757/74A4F2A1-C747-43F9-A22A-C0AD5FB4ECB6/UniversalMac_12.3_21E230_Restore.ipsw";
  deflate_offset_in_ipsw = 12312884452;
  offsets = ./data/offsets;
  syncpoints = ./data/syncpoints;
  sha256 = "0hi6r66aiixgfwxpzrfaf68ap2giha3mwv5b8ai2vz67kf7rsrk8";
}
