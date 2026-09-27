#!/bin/sh
# Creates (or verifies) the driverless IPP Everywhere queue for the Epson
# EcoTank ET-16600. Idempotent - safe to run on every container start and
# before every print job, so a printer that was asleep at boot time is still
# picked up later. Runs inside the cups container (local CUPS socket).
set -eu

QUEUE="${PRINTER_QUEUE:-ET-16600}"
IP="${PRINTER_IP:-192.168.1.220}"
URI="${PRINTER_URI:-ipp://$IP/ipp/print}"
DESCRIPTION="${PRINTER_DESCRIPTION:-Epson EcoTank ET-16600}"
PRINTER_WAIT="${PRINTER_WAIT_SECONDS:-120}"
IPP_TOOL_TEST="/usr/share/cups/ipptool/get-printer-attributes.test"
[ -f "$IPP_TOOL_TEST" ] || IPP_TOOL_TEST="get-printer-attributes.test"

log() { printf '%s ensure-queue: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

i=0
until lpstat -r >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -gt 30 ]; then
        log "ERROR CUPS scheduler did not start within 30s"
        exit 1
    fi
    sleep 1
done

if lpstat -p "$QUEUE" >/dev/null 2>&1; then
    log "queue $QUEUE already present"
    exit 0
fi

log "waiting for printer $URI (max ${PRINTER_WAIT}s)"
i=0
until timeout 10 ipptool -t -q "$URI" "$IPP_TOOL_TEST" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge "$PRINTER_WAIT" ]; then
        log "ERROR printer $URI did not answer IPP for ${i}s - queue not created"
        exit 1
    fi
    sleep 1
done
log "printer answered, adding queue $QUEUE"

lpadmin -p "$QUEUE" -E -v "$URI" -m everywhere -D "$DESCRIPTION"
lpadmin -p "$QUEUE" -o media=A4 -o print-color-mode=color
lpadmin -d "$QUEUE"
cupsaccept "$QUEUE"
cupsenable "$QUEUE"

log "queue $QUEUE ready -> $URI"
lpstat -p "$QUEUE"
