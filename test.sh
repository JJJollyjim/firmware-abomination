#!/bin/bash

off=$1

echo "" >&2
echo "trying $1..." >&2
file="$(mktemp -u)"

tail -c+$((off-1)) ~/Downloads/ipsw-from-deflate-stream | cat <(printf "\x1f\x8b\x08\x00\x00\x00\x00\x00") <(printf "\x00") - | gunzip > "$file"

if [ -e "$file" ]
then
	len="$(wc -c "$file" | awk '{print $1}')"
	echo "file exists! len $len" >&2

	if [ "$len" -ne "0" ]
	then
		cmp -s "$file" <(tail -c "$len" ~/Downloads/inflated) && echo "match! offset $off gives len $len"
	fi

	rm "$file"
fi

