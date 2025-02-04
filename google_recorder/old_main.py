import os
import time
import logging
import sys
import argparse
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from datetime import datetime
from database import DatabaseManager
from transcription import TranscriptionManager
from audio import AudioSystem


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('meet_recorder.log')
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()


class GoogleMeetRecorder:
    def __init__(self, meet_url, headless=True):
        self.meet_url = meet_url
        self.driver = None
        self.recording = False
        self.recorder_thread = None
        self.running = True
        self.headless = headless
        self.cleanup_complete = False

        # Initialize managers
        self.db_manager = DatabaseManager()
        self.transcription_manager = TranscriptionManager()
        self.audio_system = None

        # Create directories
        os.makedirs('recordings', exist_ok=True)
        os.makedirs('.session', exist_ok=True)

        try:
            self._initialize_browser()
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise

        try:
            self.audio_system = AudioSystem()
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {str(e)}")
            raise

    def _initialize_browser(self):
        """Initialize or reinitialize the Chrome browser with appropriate options"""
        options = webdriver.ChromeOptions()

        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--autoplay-policy=no-user-gesture-required')

        # Chrome session persistence
        user_data_dir = os.path.abspath('.session/chrome_data')
        os.makedirs(user_data_dir, exist_ok=True)
        options.add_argument(f'--user-data-dir={user_data_dir}')

        if self.headless:
            options.add_argument('--headless=new')

        # Chrome binary and ChromeDriver
        chrome_binary = os.environ.get('CHROME_BIN')
        if chrome_binary:
            options.binary_location = chrome_binary

        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
        if chromedriver_path:
            self.driver = webdriver.Chrome(
                executable_path=chromedriver_path, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        logger.info(f"Browser initialized in {
                    'headless' if self.headless else 'normal'} mode")

    def login_to_google(self):
        """Login to Google account"""
        try:
            # First try to access Google Meet to check if we're already logged in
            self.driver.get('https://meet.google.com')
            time.sleep(3)  # Give it a moment to load/redirect

            # Check if we're on the login page by looking for the login button
            try:
                self.driver.find_element(By.CSS_SELECTOR, '[data-noaft]')
                logger.info("Already logged into Google account")
                return
            except:
                logger.info(
                    "No active Google session found, manual login required")

                # Go to Google login page
                self.driver.get('https://accounts.google.com')

                print("\nPlease log in manually in the browser window.")
                print("After logging in, press Enter to continue...")
                input()

                # Verify login was successful
                self.driver.get('https://meet.google.com')
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, '[data-noaft]'))
                    )
                    logger.info("Successfully logged into Google account")
                except:
                    raise Exception(
                        "Login verification failed. Please try again.")

        except Exception as e:
            logger.error(f"Failed to handle Google login: {str(e)}")
            raise

    def join_meet(self):
        """Join a Google Meet call"""
        try:
            logger.info(f"Joining meet: {self.meet_url}")
            self.driver.get(self.meet_url)

            # Wait for and click the join button
            join_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='Ask to join']]")
                )
            )
            join_button.click()
            logger.info("Clicked 'Ask to join' button")

            # Try to turn off microphone and camera if they're on
            try:
                mic_button = self.driver.find_element(
                    By.CSS_SELECTOR, "[aria-label='Turn off microphone']")
                mic_button.click()
                logger.info("Turned off microphone")
            except:
                logger.info("Microphone already off or button not found")

            try:
                camera_button = self.driver.find_element(
                    By.CSS_SELECTOR, "[aria-label='Turn off camera']")
                camera_button.click()
                logger.info("Turned off camera")
            except:
                logger.info("Camera already off or button not found")

            # Wait to be let into the meeting
            logger.info("Waiting to be admitted...")
            max_wait_time = 300
            wait_start_time = time.time()
            while time.time() - wait_start_time < max_wait_time:
                try:
                    leave_button = self.driver.find_element(
                        By.CSS_SELECTOR, "[aria-label='Leave call']")
                    logger.info("Successfully joined the meeting!")
                    break
                except:
                    logger.info(
                        "Still waiting to be admitted to the meeting...")
                    time.sleep(5)
            else:
                logger.error("Timed out waiting to be admitted to the meeting")
                raise Exception(
                    "Failed to join meeting: Admission timeout after 5 minutes")

            # Start recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.start_recording(f"meet_recording_{timestamp}.wav")

            # Monitor meet status
            def check_meet_status():
                time.sleep(10)
                # Make sure the participants list is visible
                people_button = self.driver.find_element(
                    By.CSS_SELECTOR, "[aria-label='People']")
                people_button.click()
                time.sleep(2)

                while self.recording:
                    try:
                        # Check number of participants
                        participants_list = self.driver.find_elements(
                            By.CSS_SELECTOR, "div.AE8xFb.OrqRRb.GvcuGe.goTdfd div[role='listitem']")
                        if len(participants_list) <= 1:
                            logger.info(
                                "Only one participant left, leaving the call")
                            leave_button = self.driver.find_element(
                                By.CSS_SELECTOR, "[aria-label='Leave call']")
                            leave_button.click()
                            self.stop_recording()
                            break

                        time.sleep(3)
                    except Exception as e:
                        logger.info(f"Meeting ended or disconnected: {str(e)}")
                        self.stop_recording()
                        break

                # Wait for cleanup to complete
                while not self.cleanup_complete:
                    time.sleep(1)

            monitor_thread = threading.Thread(target=check_meet_status)
            monitor_thread.start()

        except Exception as e:
            logger.error(f"Failed to join meet: {str(e)}")
            raise

    def start_recording(self, filename):
        """Start recording a meet"""
        if not self.recording:
            self.current_recording_filename = os.path.join(
                'recordings', filename)
            self.recording = True
            self.recorder_thread = threading.Thread(target=self._record)
            self.recorder_thread.start()

    def _record(self):
        """Internal method to handle recording"""
        try:
            self.audio_system.start_recording(self.current_recording_filename)
        except Exception as e:
            logger.error(f"Recording failed: {str(e)}")
            self.recording = False

    def stop_recording(self):
        """Stop the recording, transcribe it, and add it to database"""
        if self.recording and self.recorder_thread:
            self.audio_system.stop_recording()
            self.recorder_thread.join()
            self.recording = False

            # Process recording
            if hasattr(self, 'current_recording_filename'):
                try:
                    # Transcribe the audio
                    transcript = self.transcription_manager.transcribe_audio(
                        self.current_recording_filename)

                    # Add to database
                    self.db_manager.add_recording(
                        filename=os.path.basename(
                            self.current_recording_filename),
                        source="google_meet",
                        transcript=transcript
                    )
                    logger.info("Recording added to database")

                except Exception as e:
                    logger.error(f"Failed to process recording: {str(e)}")
                    # Still try to save the recording without transcript
                    try:
                        self.db_manager.add_recording(
                            filename=os.path.basename(
                                self.current_recording_filename),
                            source="google_meet",
                            transcript=None
                        )
                    except Exception as db_error:
                        logger.error(f"Failed to add recording to database: {
                                     str(db_error)}")

            # Shutdown
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Shutting down...")
        self.running = False
        if self.recording:
            self.stop_recording()

        # Handle WebDriver cleanup
        if self.driver:
            try:
                self.driver.close()
                self.driver.quit()
            except Exception as e:
                pass

        # Cleanup audio system
        if self.audio_system:
            self.audio_system.cleanup()

        # Close database session
        self.db_manager.close()

        self.cleanup_complete = True
        logger.info("Cleanup completed")


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Google Meet Recorder')
        parser.add_argument('meet_url', help='URL of the Google Meet to join')
        parser.add_argument('--no-headless', action='store_true',
                            help='Run in non-headless mode')
        args = parser.parse_args()

        # Create and start recorder
        recorder = GoogleMeetRecorder(
            args.meet_url, headless=not args.no_headless)

        # Login to Google
        recorder.login_to_google()

        # Join the meet and start recording
        recorder.join_meet()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        if 'recorder' in locals():
            recorder.cleanup()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        if 'recorder' in locals():
            recorder.cleanup()
        sys.exit(1)
