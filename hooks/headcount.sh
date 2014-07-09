#!/bin/bash
head_count=$(hg heads | grep "^changeset:" | wc -l)
if [ "$head_count" -gt 1 ] ; then
	new_head=$(hg heads | head -n1 | cut -d':' -f3)
	echo "abort: push creates new remote head $new_head!"
	echo "(did you forget to merge? the force won't help you here Luke...)"
	exit 1
fi
exit 0
