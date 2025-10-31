#!/bin/bash
# Monitor OpenEvolve progress in real-time

LOG_FILE="openevolve_output/logs/openevolve_20251019_221502.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Looking for any log files..."
    LOG_FILE=$(ls -t openevolve_output/logs/openevolve_*.log 2>/dev/null | head -1)
    if [ -z "$LOG_FILE" ]; then
        echo "No log files found. Is evolution running?"
        exit 1
    fi
    echo "✓ Found: $LOG_FILE"
fi

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         OpenEvolve DRAM Optimization - Live Monitor           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Log file: $LOG_FILE"
echo "⏱️  Started: $(date)"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Show last few iterations first
echo "Recent progress:"
grep -E "Iteration [0-9]+:" "$LOG_FILE" | tail -5
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Watching for new iterations..."
echo ""

# Follow the log and filter for key events
tail -f "$LOG_FILE" | grep --line-buffered -E "Iteration [0-9]+:|best solution|combined_score|Island Status" | while read line; do
    echo "[$(date +%H:%M:%S)] $line"
done
