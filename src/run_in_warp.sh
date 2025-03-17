#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <command>"
    exit 1
fi

COMMAND="$1"

osascript <<EOF
tell application "Warp"
    activate
    tell application "System Events"
        keystroke "t" using command down
        delay 0.5
        keystroke "$COMMAND"
        keystroke return
    end tell
end tell
EOF
