#!/bin/bash
# GPU monitor daemon - runs collect_gpu_data.sh every 10 minutes
# Start: nohup bash gpu_monitor_daemon.sh &
# Stop:  kill $(cat data/gpu_daemon.pid)
# Or:    touch data/gpu_daemon.stop (graceful stop)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$SCRIPT_DIR/data/gpu_daemon.pid"
STOPFILE="$SCRIPT_DIR/data/gpu_daemon.stop"
LOGFILE="$SCRIPT_DIR/data/gpu_daemon.log"

# Remove stop file if exists
rm -f "$STOPFILE"

# Write PID
echo $$ > "$PIDFILE"
echo "[$(date)] GPU monitor daemon started (PID $$)" >> "$LOGFILE"

while true; do
    # Check for stop signal
    if [ -f "$STOPFILE" ]; then
        echo "[$(date)] Stop file detected, exiting" >> "$LOGFILE"
        rm -f "$PIDFILE" "$STOPFILE"
        exit 0
    fi

    # Collect data
    bash "$SCRIPT_DIR/collect_gpu_data.sh" >> "$LOGFILE" 2>&1

    # Sleep 10 minutes (in 30-sec chunks so we can detect stop file)
    for i in $(seq 1 20); do
        if [ -f "$STOPFILE" ]; then
            echo "[$(date)] Stop file detected during sleep, exiting" >> "$LOGFILE"
            rm -f "$PIDFILE" "$STOPFILE"
            exit 0
        fi
        sleep 30
    done
done
