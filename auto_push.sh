#!/bin/bash
# Auto-push GPU data to GitHub every hour
# Start: nohup bash auto_push.sh &
# Stop:  touch data/auto_push.stop

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STOPFILE="$SCRIPT_DIR/data/auto_push.stop"
PIDFILE="$SCRIPT_DIR/data/auto_push.pid"
LOGFILE="$SCRIPT_DIR/data/auto_push.log"

rm -f "$STOPFILE"
echo $$ > "$PIDFILE"
echo "[$(date)] Auto-push daemon started (PID $$)" >> "$LOGFILE"

while true; do
    # Check for stop signal
    if [ -f "$STOPFILE" ]; then
        echo "[$(date)] Stop file detected, exiting" >> "$LOGFILE"
        rm -f "$PIDFILE" "$STOPFILE"
        exit 0
    fi

    # Sleep 1 hour (in 30-sec chunks for stop detection)
    for i in $(seq 1 120); do
        if [ -f "$STOPFILE" ]; then
            echo "[$(date)] Stop file detected during sleep, exiting" >> "$LOGFILE"
            rm -f "$PIDFILE" "$STOPFILE"
            exit 0
        fi
        sleep 30
    done

    # Push
    cd "$SCRIPT_DIR"
    git add data/gpu_status.json data/gpu_history.json
    git commit -m "Auto-update GPU monitor data ($(date -u +%Y-%m-%dT%H:%M:%SZ))" 2>/dev/null
    if git push origin main 2>&1; then
        echo "[$(date)] Pushed successfully" >> "$LOGFILE"
    else
        echo "[$(date)] Push failed" >> "$LOGFILE"
    fi
done
