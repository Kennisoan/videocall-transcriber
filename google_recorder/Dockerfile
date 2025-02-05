FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies including Chromium and build tools
RUN apt-get update && apt-get install -y \
    pulseaudio \
    libsndfile1 \
    portaudio19-dev \
    dbus \
    dbus-x11 \
    chromium \
    chromium-driver \
    gcc \
    python3-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Create symlink for Chrome
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome-stable

# Set up pulse user and directories
RUN mkdir -p /var/lib/pulse /run/user/pulse /home/pulse/.config/pulse && \
    useradd -m -d /home/pulse pulse || true && \
    usermod -d /home/pulse pulse && \
    usermod -aG audio pulse && \
    chown -R pulse:pulse /var/lib/pulse /run/user/pulse /home/pulse && \
    mkdir -p /home/pulse/.config/pulse && \
    chown -R pulse:pulse /home/pulse/.config

# Install Python packages from requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy the complete application code into the image
COPY . /home/pulse/app
RUN chown -R pulse:pulse /home/pulse/app

# Set up PulseAudio configuration and entrypoint script
RUN cp /home/pulse/app/pulse/default.pa /home/pulse/.config/pulse/default.pa && \
    cp /home/pulse/app/scripts/entrypoint.sh /entrypoint.sh && chmod +x /entrypoint.sh

USER pulse
WORKDIR /home/pulse/app

ENV XDG_RUNTIME_DIR=/run/user/pulse
ENV PYTHONPATH=/home/pulse/app

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"] 