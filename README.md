# hooooo boy.

ok. so. 

macOS includes firmware files for the onboard Broadcom wifi on M1 Macs, which
are not licensed as redistributable.

The official Asahi Linux installer copies these files to the EFI partition, from
where Arch copies them to `/lib/firmware`.

This is all well and good for normal people, but this is NixOS! We don't want to
grab firmware off the EFI partition, we want a reproducible, hermetically-sealed
system closure!

The obvious approach is to have a derivation download the firmware from Apple's
servers. This is great in theory, but starts to look less appealing when you
realise that the firmware is contained in a 13GB macOS update image
([ipsw](https://ipsw.me/MacBookPro18,2)). Since we'd be marking the derivation as
unfree and not building it on Hydra, this would mean every user has to download
the full 13GB - that's a non-starter.

The crux of this idea came when I was downloading an IPSW with `axel`. I
realised that the download was proceeding in parallel, meaning that Apple's CDN
supports range requests. As such, if we can find the byte offset into the IPSW
where the wifi firmware is located, we can skip the rest of the download, and
only locate the exact bytes containing the firmware!

An ipsw, [it turns out](https://www.theiphonewiki.com/wiki/IPSW_File_Format), is
just a zip file. This is fantastic news for our project, as zip is a seekable
format - each file is in a separate compression stream referenced by offset in
the end-of-file directory header, so we can fetch and decompress only a single
file.

Less exciting is what happens once we open up the ipsw and start looking for the
wifi firmware. Unlike most firmware files, the wifi firmware is located inside
the macOS filesystem image. Specificically, it is located inside the 1.9GB
"macOS Base System" APFS image, which is shared by the Recovery OS and by macOS
proper. We could give up here, reducing the necessary download to just this
smaller 1.9GB DMG, but that still feels like too much bandwidth.

To optimise further, we need to understand the deflate algorithm that zip uses
to store this file. [This
website](https://www.bolet.org/~pornin/deflate-flush.html) provides an excellent
rundown of the relevant details, but here's the summary:

Deflated data consists of a series of blocks, of three possible types:

+ **Type 0** blocks are directly copied into the compressed stream. These are
  used for uncompressable data, where applying the normal compression techniques
  could actually *increase* the size of the data.
+ **Type 1** blocks are compressed with LZ77. This means that they require a
  lookbehind window of 32KB, from which they can copy duplicated data.
+ **Type 2** blocks are like Type 1 but with additional Huffman encoding. The
  Huffman tables are self-contained within the block, so they require no
  extra consideration on our part.
  
The key problem we're facing is that if we seek to the middle of a deflate
stream, at the start of a Type 1/2 block, we won't have the necessary context to
perform decompression. However, since the LZ77 lookbehind window is so small at
just 32KB, if we can find a run of Type 0 blocks that exceed 32KB, we can seek
to that point and resume decompression!

In fact, we may not even need 32KB of Type 0 data. There's a pretty good chance
that the next Type 1/2 block doesn't use the full 32KB of lookbehind, so we may
get lucky and survive with a smaller Type 0 block.

To test this theory, I built a [patched `gunzip` binary](./gzip.nix) which prints
the offsets of each Type 0 block it encounters. Once we have this candidate
offset, we can perform a [trial decompression](./test.sh) starting at that offset
in the file, and see if the file we end up with is a suffix of the valid macOS DMG.

We save a list of suitable compressed-uncompressed offset pairs, which we call
"[sync points](./data/syncpoints)". Using this tiny file we can start reading
from any point in the file, downloading, in the worst case, only 30MB of data!

Note that unlike the well-known methods for seeking through deflate streams, we
haven't relied on a cooperating encoder (e.g. issuing a `Z_FULL_FLUSH` every
64kB), nor have we redistributed copyrightable Apple data (e.g. the 32KB
backreference buffer located before our target).

Now we can seek around the DMG, we need to find where the firmware files are
located within it. While it would be lovely to build a full implementation of
[the APFS filesystem](https://developer.apple.com/support/downloads/Apple-File-System-Reference.pdf)
which operates solely over syncronised deflate streams over HTTP range requests,
it's not really necessary for our purposes. Instead, we rely on the fact that
the DMG contains no file fragmentation, and [search for the offset](./offsets.sh)
of each file, storing the results in [a manifest](./data/offsets), along with 
filenames and lengths.

Finally, we can implement a [downloader script](./fetchfirmware/downloader.py)
that uses this data, and call it from a [fixed-output derivation](./fetchfirmware/default.nix).

Activity Monitor reports that the downloader script downloads 16.8MB of data,
and `du` reports that the resulting firmware directory is 17MB - we have
achieved negative overhead, where the unnecessary downloads are exceeded by
savings due to compression! This is almost an 800x bandwith saving over
downloading the full IPSW :)

To download the firmware yourself, replicating macOS's firmware directory layout:

``` sh
$ NIXPKGS_ALLOW_UNFREE=1 nix-build default.nix
/nix/store/q7mzmlbwadvaa5hifs00qzbsj8l4zw4a-firmware
$ ls -lT /nix/store/q7mzmlbwadvaa5hifs00qzbsj8l4zw4a-firmware
dr-xr-xr-x    - root  1 Jan  1970 /nix/store/q7mzmlbwadvaa5hifs00qzbsj8l4zw4a-firmware
.r--r--r-- 2.5k root  1 Jan  1970 ├── atlantis-PlatformConfig.plist
.r--r--r-- 2.6k root  1 Jan  1970 ├── atlantisb-PlatformConfig.plist
.r--r--r-- 2.4k root  1 Jan  1970 ├── bali-PlatformConfig.plist
.r--r--r-- 2.4k root  1 Jan  1970 ├── borneo-PlatformConfig.plist
dr-xr-xr-x    - root  1 Jan  1970 ├── C-4355__s-C1
.r--r--r--  14k root  1 Jan  1970 │  ├── hawaii.clmb
.r--r--r-- 728k root  1 Jan  1970 │  ├── hawaii.trx
.r--r--r--  607 root  1 Jan  1970 │  ├── hawaii.txcb
.r--r--r-- 5.2k root  1 Jan  1970 │  ├── P-hawaii_M-YSBC_V-m__m-2.3.txt
.r--r--r-- 5.2k root  1 Jan  1970 │  ├── P-hawaii_M-YSBC_V-m__m-2.5.txt
.r--r--r-- 5.1k root  1 Jan  1970 │  ├── P-hawaii_M-YSBC_V-u__m-4.1.txt
.r--r--r-- 5.1k root  1 Jan  1970 │  └── P-hawaii_M-YSBC_V-u__m-4.3.txt
...
```
