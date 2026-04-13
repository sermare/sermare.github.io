#!/bin/bash
# Regenerate data/research_loop.json every 30 min from the /loop JSONL log
# and push the update to GitHub.
#
# Start:  nohup bash scripts/research_loop_daemon.sh > data/research_loop_daemon.log 2>&1 &
# Stop:   touch data/research_loop.stop

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STOPFILE="$SCRIPT_DIR/data/research_loop.stop"
PIDFILE="$SCRIPT_DIR/data/research_loop_daemon.pid"
LOGFILE="$SCRIPT_DIR/data/research_loop_daemon.log"
UPDATER="$SCRIPT_DIR/scripts/update_research_loop.py"
OUT_JSON="$SCRIPT_DIR/data/research_loop.json"

rm -f "$STOPFILE"
echo $$ > "$PIDFILE"
echo "[$(date -u +%FT%TZ)] research_loop daemon started (PID $$)" >> "$LOGFILE"

cd "$SCRIPT_DIR"

while true; do
    if [ -f "$STOPFILE" ]; then
        echo "[$(date -u +%FT%TZ)] stop signal, exiting" >> "$LOGFILE"
        rm -f "$PIDFILE" "$STOPFILE"
        exit 0
    fi

    if python3 "$UPDATER" >> "$LOGFILE" 2>&1; then
        git add "$OUT_JSON"
        if ! git diff --cached --quiet -- "$OUT_JSON"; then
            git commit -m "Auto-update research_loop data ($(date -u +%FT%TZ))" \
                >> "$LOGFILE" 2>&1
            if git push origin main >> "$LOGFILE" 2>&1; then
                echo "[$(date -u +%FT%TZ)] pushed research_loop.json" >> "$LOGFILE"
            else
                echo "[$(date -u +%FT%TZ)] push failed" >> "$LOGFILE"
            fi
        else
            echo "[$(date -u +%FT%TZ)] no change" >> "$LOGFILE"
        fi
    else
        echo "[$(date -u +%FT%TZ)] updater failed" >> "$LOGFILE"
    fi

    # 30 min sleep in 30-sec chunks so stop signal is responsive.
    for i in $(seq 1 60); do
        if [ -f "$STOPFILE" ]; then
            echo "[$(date -u +%FT%TZ)] stop during sleep, exiting" >> "$LOGFILE"
            rm -f "$PIDFILE" "$STOPFILE"
            exit 0
        fi
        sleep 30
    done
done
