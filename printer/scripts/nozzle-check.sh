#!/bin/sh
# Prints one A4 CMYK nozzle maintenance page to the Epson ET-16600.
#
#   docker compose run --rm nozzle-check
#
# Pre-flight checks run before every job: CUPS scheduler up, printer answering
# IPP on the LAN, queue healthy. The job is then followed until CUPS reports it
# completed. Everything is logged to stdout, so failures show up in
# docker compose logs printer-cron.
set -eu

QUEUE="${PRINTER_QUEUE:-ET-16600}"
IP="${PRINTER_IP:-192.168.1.220}"
QUEUE_URI="${PRINTER_URI:-ipp://$IP/ipp/print}"
GENERATOR="${TESTPAGE_GENERATOR:-/printer/testpage/generate-nozzle-check.py}"
TESTPAGE="${STAMPED_TESTPAGE:-/tmp/nozzle-check.pdf}"
INK_SCALE="${INK_SCALE:-1.0}"
JOB_TIMEOUT="${JOB_TIMEOUT_SECONDS:-180}"
IPP_TOOL_TEST="/usr/share/cups/ipptool/get-printer-attributes.test"
[ -f "$IPP_TOOL_TEST" ] || IPP_TOOL_TEST="get-printer-attributes.test"

log() { printf '%s nozzle-check: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
fail() {
    log "FAIL $*"
    exit 1
}

lpstat -r >/dev/null 2>&1 || fail "CUPS scheduler is not running"

timeout 10 ipptool -t -q "$QUEUE_URI" "$IPP_TOOL_TEST" >/dev/null 2>&1 \
    || fail "printer $QUEUE_URI is not answering - offline, asleep or IP changed?"

/printer/scripts/ensure-queue.sh
lpstat -p "$QUEUE" >/dev/null 2>&1 || fail "queue $QUEUE does not exist"

state=$(lpstat -p "$QUEUE")
log "queue state: $state"
if echo "$state" | grep -qi "disabled\|not accepting"; then
    fail "queue $QUEUE is not taking jobs (check port 631 web UI)"
fi

supplies=$(timeout 10 ipptool -tv "$QUEUE_URI" "$IPP_TOOL_TEST" 2>/dev/null | grep -iE "printer-state-reasons|marker-levels" || true)
[ -n "$supplies" ] && log "printer reports: $(echo "$supplies" | tr '\n' ' ')"
if echo "$supplies" | grep -qiE "media-needed|media-jam|paper-jam|door-open|cover-open|output-area-full|marker-supply-empty|ink-empty|toner-empty|offline"; then
    fail "printer is not ready to print: $supplies"
fi

[ -f "$GENERATOR" ] || fail "test page generator $GENERATOR is missing"
command -v python3 >/dev/null 2>&1 || fail "python3 is not available to generate the test page"

# Regenerate so the page carries the date and time of this print. TZ comes
# from the cups service, so the stamp is in local time (Pacific/Auckland).
log "generating $TESTPAGE with today's timestamp"
python3 "$GENERATOR" "$TESTPAGE" --ink-scale "$INK_SCALE" || fail "could not generate the test page"

log "printing $TESTPAGE (A4, colour) to $QUEUE"
submit=$(lp -d "$QUEUE" -o media=A4 -o print-color-mode=color -o job-sheets=none "$TESTPAGE" 2>&1) \
    || fail "lp could not submit the job: $submit"
jobid=$(echo "$submit" | sed -n 's/^request id is \([^ ]*\).*/\1/p')
[ -n "$jobid" ] || fail "could not read the job id from: $submit"
log "submitted job $jobid"

elapsed=0
while [ "$elapsed" -lt "$JOB_TIMEOUT" ]; do
    if lpstat -W completed -o "$QUEUE" | grep -q "^$jobid "; then
        log "OK job $jobid completed"
        exit 0
    fi
    if ! lpstat -W not-completed -o "$QUEUE" | grep -q "^$jobid "; then
        fail "job $jobid disappeared without completing (cancelled, held or paper tray empty)"
    fi
    sleep 5
    elapsed=$((elapsed + 5))
done

fail "job $jobid is still queued after ${JOB_TIMEOUT}s"
