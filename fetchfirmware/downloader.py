#!/usr/bin/env python3

import urllib3
from pathlib import Path
import sys
import os
import zlib

# Glossary:
# uoff = offset into uncompressed image
# coff = offset into compressed stream

deflate_offset_in_ipsw = int(os.getenv("deflate_offset_in_ipsw"))
url = os.getenv("url")
outdir = Path(os.getenv("out"))
os.mkdir(os.getenv("out"))

# format: name, uoff, length
files = [(outdir / Path(x[0]), int(x[1]), int(x[2])) for x in (y.split(" ") for y in open(os.getenv("offsets")))]
files.sort(key=lambda x: x[1])

# format: coff, uoff
syncpoints = [(int(x[0]), int(x[1])) for x in (y.split(" ") for y in open(os.getenv("syncpoints")))]


# start of the first desired file
lowest_file_uoff = min((x[1] for x in files))
# end of the last desired file
highest_file_uoff = max((x[1]+x[2] for x in files))

# the sync point right before the first file
optimal_syncpoint = max((x for x in syncpoints if x[1] <= lowest_file_uoff), key=lambda x: x[0])

# the sync point right after the last file. we don't actually need to request this far, but we have to specify a concrete upper bound on our range request, and this is the best we have. in actual fact, we will kill the tcp socket once we've recieved all we need.
upper_bound_coff = max((x for x in syncpoints if x[1] >= highest_file_uoff), key=lambda x: x[0])[0]

print("will download up to %.1fMiB" % ((upper_bound_coff - optimal_syncpoint[0]) / 1024 / 1024))

http = urllib3.PoolManager()
r = http.request(
    'GET', 
    url,
    headers = {
        'Range': "bytes={}-{}".format(deflate_offset_in_ipsw + optimal_syncpoint[0], deflate_offset_in_ipsw + upper_bound_coff)
    },
    preload_content=False
)

class DataHandler:
    def __init__(self):
        self.buf = bytearray()
        self.off = optimal_syncpoint[1]

        self.remaining_files = files[:]

    def next_file_end(self):
        return self.remaining_files[0][1] + self.remaining_files[0][2]

    def buf_end(self):
        return self.off + len(self.buf)

    def handle(self, data):
        self.buf += data

        while self.next_file_end() <= self.buf_end():
            file = self.remaining_files[0]
            try:
                os.mkdir(file[0].parent)
            except FileExistsError:
                pass
            open(file[0], "wb").write(self.buf[(file[1] - self.off):(file[1] - self.off + file[2])])

            del self.remaining_files[0]

            if len(self.remaining_files) == 0:
                return False

        if self.remaining_files[0][1] > self.buf_end():
            self.off += len(self.buf)
            self.buf = bytearray()
        else:
            del self.buf[0:(self.remaining_files[0][1] - self.off)]
            self.off = self.remaining_files[0][1]

        return True

dh = DataHandler()
decomp = zlib.decompressobj(-zlib.MAX_WBITS)

decomp.decompress(b"\x00") # type-zero block header (wouldn't be correctly bit-aligned if we used the original)

while dh.handle(decomp.decompress(r.read(1024)) + decomp.flush()):
    pass
