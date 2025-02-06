import os
import platform
import logging
import pyaudio
import soundfile as sf
import numpy
import time

logger = logging.getLogger(__name__)


class AudioSystem:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        # Use Linux audio setup if we're in container or on Linux
        self.system = "Linux" if os.environ.get(
            'FORCE_LINUX_AUDIO') else platform.system()
        self.recording_device = None
        self.recording = False
        self._setup_recording_device()

        # Ensure recordings directory exists with proper permissions
        self.recordings_dir = "/home/pulse/app/recordings"
        if not os.path.exists(self.recordings_dir):
            try:
                os.makedirs(self.recordings_dir, exist_ok=True)
                # Ensure directory has proper permissions
                os.chmod(self.recordings_dir, 0o777)
                logger.info(
                    f"Created recordings directory: {self.recordings_dir}")
            except Exception as e:
                logger.error(
                    f"Failed to create recordings directory: {str(e)}")
                raise

    def _setup_recording_device(self):
        """Setup the appropriate recording device based on the platform"""
        if self.system == "Linux":
            # Look for our virtual microphone
            device_found = False
            for i in range(self.pa.get_device_count()):
                device_info = self.pa.get_device_info_by_index(i)
                logger.debug(f"Found audio device: {device_info['name']}")

                # Check for both the source and monitor names as they might appear differently
                device_names = [
                    "pulse",
                    "virtual-mic-out",
                    "virtual-mic.monitor",
                    "virtual-mic Monitor"
                ]

                if any(name.lower() in device_info["name"].lower() for name in device_names):
                    self.recording_device = device_info
                    device_found = True
                    logger.info(
                        f"Found virtual microphone: {device_info['name']}")
                    logger.info(f"Device info: {device_info}")
                    break

            if not device_found:
                # Wait for a short time and retry once, as PulseAudio might need a moment
                logger.info(
                    "Virtual mic not found immediately, waiting for PulseAudio initialization...")
                time.sleep(2)

                for i in range(self.pa.get_device_count()):
                    device_info = self.pa.get_device_info_by_index(i)
                    device_names = [
                        "pulse",
                        "virtual-mic-out",
                        "virtual-mic.monitor",
                        "virtual-mic Monitor"
                    ]

                    if any(name.lower() in device_info["name"].lower() for name in device_names):
                        self.recording_device = device_info
                        device_found = True
                        logger.info(
                            f"Found virtual microphone after retry: {device_info['name']}")
                        logger.info(f"Device info: {device_info}")
                        break

            if not device_found:
                logger.error("No virtual-mic found. Available devices:")
                for i in range(self.pa.get_device_count()):
                    dev_info = self.pa.get_device_info_by_index(i)
                    logger.error(f"Index {i}: {dev_info['name']}")
                raise Exception("virtual-mic not found in container")

        elif self.system == "Darwin":  # macOS (non-containerized)
            logger.warning("Running on macOS without containerization.")
            logger.warning(
                "For better compatibility, please run this application using Docker.")
            logger.warning(
                "Docker setup handles all audio routing internally without requiring BlackHole.")

            # Fall back to BlackHole for non-containerized macOS
            for i in range(self.pa.get_device_count()):
                device_info = self.pa.get_device_info_by_index(i)
                if "BlackHole" in device_info["name"]:
                    self.recording_device = device_info
                    logger.info(
                        f"Found BlackHole device: {device_info['name']}")
                    logger.info(f"Device info: {device_info}")
                    return

            logger.error("BlackHole 2ch not found. Please either:")
            logger.error("1. Run this application using Docker (recommended)")
            logger.error(
                "2. Install BlackHole from https://existential.audio/blackhole/")
            raise Exception("No suitable audio capture device found")

        else:
            raise Exception(f"Unsupported platform: {self.system}")

    def start_recording(self, filename):
        """Start recording audio"""
        if not self.recording_device:
            raise Exception("No recording device configured")

        # Ensure filename is using the correct directory path
        full_path = os.path.join(
            self.recordings_dir, os.path.basename(filename))
        logger.info(f"Recording to file: {full_path}")

        self.recording = True
        CHUNK = 1024
        FORMAT = pyaudio.paFloat32
        CHANNELS = 2  # Force stereo as per PulseAudio config
        RATE = 48000  # Match PulseAudio daemon.conf setting

        logger.info(f"Starting recording with settings:")
        logger.info(f"Device: {self.recording_device['name']}")
        logger.info(f"Channels: {CHANNELS}")
        logger.info(f"Rate: {RATE}")
        logger.info(f"Format: Float32")

        try:
            stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=int(self.recording_device["index"]),
                frames_per_buffer=CHUNK
            )

            with sf.SoundFile(full_path, mode='w', samplerate=RATE,
                              channels=CHANNELS, format='WAV') as audio_file:
                while self.recording:  # Continue while recording flag is True
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        audio_data = numpy.frombuffer(
                            data, dtype=numpy.float32)
                        audio_data = audio_data.reshape(-1, CHANNELS)
                        audio_file.write(audio_data)
                    except IOError as e:
                        if e.errno == -9981:  # Input overflow
                            logger.warning("Audio input overflow occurred")
                            continue
                        else:
                            logger.error(f"IOError during recording: {str(e)}")
                            break
                    except Exception as e:
                        logger.error(f"Error recording audio: {str(e)}")
                        break

            stream.stop_stream()
            stream.close()

        except Exception as e:
            self.recording = False
            logger.error(f"Failed to initialize audio stream: {str(e)}")
            raise

    def stop_recording(self):
        """Stop the recording"""
        self.recording = False

    def cleanup(self):
        """Cleanup audio resources"""
        self.recording = False
        self.pa.terminate()
