#!/bin/bash
# Start Xvfb for virtual display (if not in headless mode)
if [ "$TIKTOK_HEADLESS" = "false" ]; then
    echo "Starting Xvfb for non-headless mode..."
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    export DISPLAY=:99
    sleep 2
fi

# Start the worker
exec python -m app.worker
