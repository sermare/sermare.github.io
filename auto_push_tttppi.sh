#!/bin/bash
# Auto-push TTT-PPI dashboard updates every 15 minutes
# 1. Regenerates data JSONs from latest experiment results
# 2. Commits & pushes to GitHub Pages
#
# Start: nohup bash auto_push_tttppi.sh &
# Stop:  touch data/auto_push_tttppi.stop

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="/global/scratch/users/sergiomar10/twoproteinsallyouneed"
STOPFILE="$SCRIPT_DIR/data/auto_push_tttppi.stop"
PIDFILE="$SCRIPT_DIR/data/auto_push_tttppi.pid"
LOGFILE="$SCRIPT_DIR/data/auto_push_tttppi.log"

rm -f "$STOPFILE"
echo $$ > "$PIDFILE"
echo "[$(date)] Auto-push TTT-PPI daemon started (PID $$)" >> "$LOGFILE"

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

    # Regenerate data from latest results
    echo "[$(date)] Regenerating TTT-PPI data..." >> "$LOGFILE"
    cd "$PROJECT_DIR"
    python3 scripts/generate_website_data.py >> "$LOGFILE" 2>&1

    # Push any changes
    cd "$SCRIPT_DIR"
    git add data/ttt_ppi/ ttt-ppi.html
    git commit -m "Auto-update TTT-PPI dashboard ($(date -u +%Y-%m-%dT%H:%M:%SZ))" 2>/dev/null
    if git diff --quiet origin/main..HEAD 2>/dev/null; then
        echo "[$(date)] No changes to push" >> "$LOGFILE"
    else
        if git push origin main 2>&1 >> "$LOGFILE"; then
            echo "[$(date)] Pushed TTT-PPI update successfully" >> "$LOGFILE"
        else
            echo "[$(date)] Push failed" >> "$LOGFILE"
        fi
    fi
done
