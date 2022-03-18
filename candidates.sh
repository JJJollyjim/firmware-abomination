#!/bin/bash
cat <(printf "\x1f\x8b\x08\x00\x00\x00\x00\x00" ) ~/Downloads/ipsw-from-deflate-stream | result/bin/gunzip > /dev/null
