#!/bin/bash
# update_progress.sh — commit and push TTT-PPI progress data to GitHub Pages
cd /clusterfs/nilah/sergio/sermare.github.io
git add data/ttt_ppi/ ttt-ppi.html
git commit -m "Auto-update TTT-PPI progress ($(date -Iseconds))" 2>/dev/null
git push origin main 2>/dev/null
