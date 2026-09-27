#!/bin/sh
# Health report for the Epson ET-16600 queue: queues known to CUPS, the device
# URI in use, whether the printer answers IPP, ink markers and recent jobs.
#
#   docker compose run --rm printer-status
set -eu

QUEUE="${PRINTER_QUEUE:-ET-16600}"
IP="${PRINTER_IP:-192.168.1.220}"
QUEUE_URI="${PRINTER_URI:-ipp://$IP/ipp/print}"
IPP_TOOL_TEST="/usr/share/cups/ipptool/get-printer-attributes.test"
[ -f "$IPP_TOOL_TEST" ] || IPP_TOOL_TEST="get-printer-attributes.test"

echo "===== CUPS scheduler ====="
lpstat -r || true
lpstat -d
echo
echo "===== queue $QUEUE ====="
lpstat -p "$QUEUE" || echo "queue $QUEUE is unknown to CUPS"
lpstat -v "$QUEUE" || true
echo
echo "===== printer $QUEUE_URI ====="
timeout 10 ipptool -tv "$QUEUE_URI" "$IPP_TOOL_TEST" 2>&1 \
    | grep -iE "printer-state|printer-make-and-model|printer-info|state-reasons|marker-|media-ready" \
    || echo "no answer from $QUEUE_URI"
echo
echo "===== recent jobs ====="
lpstat -W all -o "$QUEUE" | tail -10 || echo "no job history"
