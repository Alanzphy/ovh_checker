#!/bin/bash

# Wrapper script to run the OVH checker with the correct virtual environment
# This script ensures the correct Python is used and handles logs

# Get the directory where this script is located (portable)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Get timestamp for the log
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="logs/ovh_checker_${TIMESTAMP}.log"

# Execute the script using the virtual environment's Python
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/ovh_daily_checker.py" >> "$LOG_FILE" 2>&1

# Optional: Keep only the last 30 logs (delete old logs)
find logs/ -name "ovh_checker_*.log" -mtime +30 -delete

echo "Execution completed. Log saved in: $LOG_FILE"
