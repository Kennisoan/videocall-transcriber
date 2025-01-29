FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Create necessary directories
USER root
RUN mkdir -p /app /app/recordings /app/.session /etc/pulse /root/.config/pulse

# Set the working directory
WORKDIR /app

# Install dependencies and Python 3.12
RUN apt-get update && \
    apt-get install -y \
    software-properties-common \
    gpg-agent \
    wget \
    && wget https://github.com/deadsnakes/python3.12/releases/download/3.12.0/python3.12_3.12.0-1+focal1_arm64.deb \
    && dpkg -i python3.12_3.12.0-1+focal1_arm64.deb || true \
    && apt-get install -f -y \
    && apt-get install -y \
    python3-pip \
    pulseaudio \
    sudo \
    xvfb \
    curl \
    gnupg \
    libnss3-tools \
    ffmpeg \
    libfontconfig \
    libfreetype6 \
    xfonts-cyrillic \
    xfonts-scalable \
    fonts-liberation \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Set up audio
RUN usermod -aG audio root
RUN adduser root pulse-access

ENV DBUS_SESSION_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket
ENV XDG_RUNTIME_DIR=/run/user/0
ENV FORCE_LINUX_AUDIO=1

# Set up D-Bus and PulseAudio
RUN mkdir -p /run/dbus
RUN chmod 755 /run/dbus
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN dbus-daemon --system --fork

# Install PortAudio for PyAudio
RUN wget http://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz && \
    tar -xvf pa_stable_v190700_20210406.tgz && \
    mv portaudio /usr/src/ && \
    rm pa_stable_v190700_20210406.tgz && \
    cd /usr/src/portaudio && \
    ./configure && \
    make && \
    make install && \
    ldconfig

WORKDIR /app

# Copy PulseAudio configuration
COPY pulseaudio.conf /etc/dbus-1/system.d/pulseaudio.conf
COPY default.pa /etc/pulse/default.pa
COPY daemon.conf /etc/pulse/daemon.conf

# Copy application code
COPY . /app

# Install Python dependencies with Python 3.12
RUN python3.12 -m pip install --no-cache-dir -r requirements.txt

# Set Chrome environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set display environment variables
ENV X_SERVER_NUM=1
ENV SCREEN_WIDTH=1920
ENV SCREEN_HEIGHT=1080
ENV SCREEN_RESOLUTION=1920x1080
ENV COLOR_DEPTH=24
ENV DISPLAY=:${X_SERVER_NUM}.0

# Set up X authority
RUN touch /root/.Xauthority
RUN chmod 600 /root/.Xauthority

# Create entrypoint script with PulseAudio setup
RUN echo '#!/bin/bash\n\
# Start PulseAudio\n\
pulseaudio -D --system --disallow-exit --disallow-module-loading --exit-idle-time=-1\n\
sleep 2\n\
# Start Xvfb\n\
Xvfb :${X_SERVER_NUM} -screen 0 ${SCREEN_RESOLUTION}x${COLOR_DEPTH} &\n\
export DISPLAY=:${X_SERVER_NUM}\n\
# Run the application\n\
exec python3.12 main.py "$@"' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"] 