#!/bin/bash
# Auto-push protein design page updates every 15 minutes
# Start: nohup bash auto_push_design.sh &
# Stop:  touch data/auto_push_design.stop

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STOPFILE="$SCRIPT_DIR/data/auto_push_design.stop"
PIDFILE="$SCRIPT_DIR/data/auto_push_design.pid"
LOGFILE="$SCRIPT_DIR/data/auto_push_design.log"

rm -f "$STOPFILE"
echo $$ > "$PIDFILE"
echo "[$(date)] Auto-push design daemon started (PID $$)" >> "$LOGFILE"

while true; do
    # Check for stop signal
    if [ -f "$STOPFILE" ]; then
        echo "[$(date)] Stop file detected, exiting" >> "$LOGFILE"
        rm -f "$PIDFILE" "$STOPFILE"
        exit 0
    fi

    # Sleep 15 minutes (in 30-sec chunks for stop detection)
    for i in $(seq 1 30); do
        if [ -f "$STOPFILE" ]; then
            echo "[$(date)] Stop file detected during sleep, exiting" >> "$LOGFILE"
            rm -f "$PIDFILE" "$STOPFILE"
            exit 0
        fi
        sleep 30
    done

    # Push any changes
    cd "$SCRIPT_DIR"
    git add -A
    git commit -m "Auto-update protein design dashboard ($(date -u +%Y-%m-%dT%H:%M:%SZ))" 2>/dev/null
    if git diff --quiet origin/main..HEAD 2>/dev/null; then
        echo "[$(date)] No changes to push" >> "$LOGFILE"
    else
        if git push origin main 2>&1; then
            echo "[$(date)] Pushed successfully" >> "$LOGFILE"
        else
            echo "[$(date)] Push failed" >> "$LOGFILE"
        fi
    fi
done
