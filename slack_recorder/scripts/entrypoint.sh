#!/bin/bash
set -e

# Set XDG runtime directory to a writable /tmp directory
export XDG_RUNTIME_DIR=/tmp/runtime-$(id -u)
# Explicitly set PulseAudio runtime directory so that pulseaudio does not fallback to /run/pulse
export PULSE_RUNTIME_PATH="$XDG_RUNTIME_DIR/pulse"
# Set PulseAudio config path explicitly
export PULSE_CONFIG_PATH="$HOME/.config/pulse"

# Clean up any existing PulseAudio files
rm -rf "$XDG_RUNTIME_DIR/pulse" "$HOME/.config/pulse/{*-runtime,*.tdb,*.dat}"

# Ensure runtime directory exists with correct permissions
mkdir -p "$XDG_RUNTIME_DIR/pulse"
chmod 700 "$XDG_RUNTIME_DIR"

# Start PulseAudio daemon
pulseaudio \
    --daemonize=no \
    --system=no \
    --realtime=no \
    --exit-idle-time=-1 \
    -n \
    --file=/home/pulse/.config/pulse/default.pa &

# Wait for PulseAudio to start and create its socket
TIMEOUT=10
COUNT=0
while [ ! -S "$XDG_RUNTIME_DIR/pulse/native" ] && [ $COUNT -lt $TIMEOUT ]; do
    echo "Waiting for PulseAudio socket... ($COUNT/$TIMEOUT)"
    sleep 1
    COUNT=$((COUNT + 1))

done

if [ ! -S "$XDG_RUNTIME_DIR/pulse/native" ]; then
    echo "PulseAudio failed to create socket"
    exit 1
fi

# List audio devices for debugging
echo "PulseAudio devices:"
pactl list short sinks
pactl list short sources

# Run the command
exec "$@"