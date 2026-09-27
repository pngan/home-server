#!/bin/sh
# Container entrypoint for the CUPS server: start cupsd, wait for the
# scheduler socket, then make sure the ET-16600 queue exists. A failed queue
# setup must not take the server down, so cupsd keeps running either way.
set -eu

mkdir -p /run/cups /var/spool/cups/tmp 2>/dev/null || true

/usr/sbin/cupsd -f &
cupsd_pid=$!

if ! /printer/scripts/ensure-queue.sh; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') run-cupsd: queue setup failed, cupsd stays up for debugging" >&2
fi

wait "$cupsd_pid"
