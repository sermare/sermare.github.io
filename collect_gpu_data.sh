#!/bin/bash
# Collect Berkeley Savio GPU cluster data and write JSON for the dashboard
# Run: bash collect_gpu_data.sh
# Cron (every 10 min): */10 * * * * cd /global/scratch/users/sergiomar10/sermare-website && bash collect_gpu_data.sh

OUTDIR="$(cd "$(dirname "$0")" && pwd)/data"
OUTFILE="$OUTDIR/gpu_status.json"
HISTFILE="$OUTDIR/gpu_history.json"
TMPNODES=$(mktemp)
TMPJOBS=$(mktemp)
TMPPENDING=$(mktemp)

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

sinfo -p savio3_gpu,savio4_gpu -o "%P|%G|%D|%T|%N" --noheader 2>/dev/null > "$TMPNODES"
squeue -p savio3_gpu,savio4_gpu -t RUNNING --format="%i|%j|%u|%P|%N|%T|%b|%M|%l" --noheader 2>/dev/null > "$TMPJOBS"
squeue -p savio3_gpu,savio4_gpu -t PENDING --format="%i|%j|%u|%P|%T|%b|%V" --noheader 2>/dev/null > "$TMPPENDING"

python3 - "$timestamp" "$TMPNODES" "$TMPJOBS" "$TMPPENDING" "$OUTFILE" "$HISTFILE" << 'PYEOF'
import json, sys, os
from collections import defaultdict

timestamp = sys.argv[1]
nodes_file = sys.argv[2]
jobs_file = sys.argv[3]
pending_file = sys.argv[4]
outfile = sys.argv[5]
histfile = sys.argv[6]

with open(nodes_file) as f:
    node_lines = f.read().strip().split('\n')
with open(jobs_file) as f:
    job_lines = f.read().strip().split('\n')
with open(pending_file) as f:
    pending_lines = f.read().strip().split('\n')

# Parse nodes
gpu_entries = []
summary = defaultdict(lambda: {"total": 0, "allocated": 0, "idle": 0, "down": 0, "mixed": 0, "draining": 0, "drained": 0})

for line in node_lines:
    if not line.strip():
        continue
    parts = line.strip().split('|')
    if len(parts) < 5:
        continue
    partition, gres, num_nodes, state, nodelist = parts[0], parts[1], int(parts[2]), parts[3], parts[4]
    gres_parts = gres.replace('gpu:', '').split(':')
    gpu_type = gres_parts[0]
    gpu_per_node = int(gres_parts[1].split('(')[0]) if len(gres_parts) > 1 else 1
    total_gpus = gpu_per_node * num_nodes
    clean_state = state.rstrip('*~')

    gpu_entries.append({
        "partition": partition, "gpu_type": gpu_type, "gpus_per_node": gpu_per_node,
        "num_nodes": num_nodes, "total_gpus": total_gpus, "state": clean_state, "nodelist": nodelist
    })

    key = partition + "|" + gpu_type
    summary[key]["total"] += total_gpus
    if clean_state == "allocated":
        summary[key]["allocated"] += total_gpus
    elif clean_state == "mixed":
        summary[key]["mixed"] += total_gpus
    elif clean_state == "idle":
        summary[key]["idle"] += total_gpus
    elif clean_state in ("down", "completing"):
        summary[key]["down"] += total_gpus
    elif clean_state == "draining":
        summary[key]["draining"] += total_gpus
    elif clean_state == "drained":
        summary[key]["drained"] += total_gpus

summary_list = []
for key, vals in sorted(summary.items()):
    partition, gpu_type = key.split('|')
    summary_list.append({
        "partition": partition, "gpu_type": gpu_type,
        "total": vals["total"], "in_use": vals["allocated"],
        "mixed": vals["mixed"],
        "free": vals["idle"] + vals["mixed"],
        "unavailable": vals["down"] + vals["drained"] + vals["draining"],
        "down": vals["down"], "drained": vals["drained"], "draining": vals["draining"]
    })

# Parse running jobs
running_jobs = []
for line in job_lines:
    if not line.strip():
        continue
    parts = line.strip().split('|')
    if len(parts) >= 9:
        running_jobs.append({
            "job_id": parts[0].strip(), "name": parts[1].strip(), "user": parts[2].strip(),
            "partition": parts[3].strip(), "nodelist": parts[4].strip(), "state": parts[5].strip(),
            "tres": parts[6].strip(), "elapsed": parts[7].strip(), "time_limit": parts[8].strip()
        })

# Parse pending jobs
pending_list = []
for line in pending_lines:
    if not line.strip():
        continue
    parts = line.strip().split('|')
    if len(parts) >= 7:
        pending_list.append({
            "job_id": parts[0].strip(), "name": parts[1].strip(), "user": parts[2].strip(),
            "partition": parts[3].strip(), "state": parts[4].strip(),
            "tres": parts[5].strip(), "submit_time": parts[6].strip()
        })

# Compute aggregate totals
total_gpus = sum(r["total"] for r in summary_list)
total_in_use = sum(r["in_use"] for r in summary_list)
total_mixed = sum(r["mixed"] for r in summary_list)
total_free = sum(r["free"] for r in summary_list)
total_unavail = sum(r["unavailable"] for r in summary_list)

result = {
    "timestamp": timestamp,
    "nodes": gpu_entries,
    "summary": summary_list,
    "running_jobs": running_jobs,
    "pending_jobs": pending_list,
    "total_running": len(running_jobs),
    "total_pending": len(pending_list)
}

with open(outfile, 'w') as f:
    json.dump(result, f, indent=2)

# --- Append to history file (keep last 7 days = 1008 entries at 10-min intervals) ---
history = []
if os.path.exists(histfile):
    try:
        with open(histfile) as f:
            history = json.load(f)
    except Exception:
        history = []

# Per-partition breakdown for history
partition_breakdown = {}
for r in summary_list:
    p = r["partition"]
    if p not in partition_breakdown:
        partition_breakdown[p] = {"total": 0, "in_use": 0, "mixed": 0, "free": 0, "unavailable": 0}
    partition_breakdown[p]["total"] += r["total"]
    partition_breakdown[p]["in_use"] += r["in_use"]
    partition_breakdown[p]["mixed"] += r["mixed"]
    partition_breakdown[p]["free"] += r["free"]
    partition_breakdown[p]["unavailable"] += r["unavailable"]

history_entry = {
    "t": timestamp,
    "total": total_gpus,
    "in_use": total_in_use,
    "mixed": total_mixed,
    "free": total_free,
    "unavail": total_unavail,
    "running": len(running_jobs),
    "pending": len(pending_list),
    "partitions": partition_breakdown
}

history.append(history_entry)

# Keep last 1008 entries (~7 days at 10-min intervals)
if len(history) > 1008:
    history = history[-1008:]

with open(histfile, 'w') as f:
    json.dump(history, f)

print("Wrote %d node groups, %d running, %d pending -> %s | History: %d points" % (
    len(gpu_entries), len(running_jobs), len(pending_list), outfile, len(history)))
PYEOF

rm -f "$TMPNODES" "$TMPJOBS" "$TMPPENDING"
