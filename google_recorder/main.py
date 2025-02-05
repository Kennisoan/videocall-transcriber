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
from state import set_state, RecorderState


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
    def __init__(self, headless=True):
        self.meet_url = None
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

        # Basic options
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--autoplay-policy=no-user-gesture-required')

        if self.headless:
            options.add_argument('--headless=new')
            options.add_argument(
                '--disable-blink-features=AutomationControlled')

        # Chrome binary and ChromeDriver with platform-specific defaults
        if sys.platform == "darwin":
            chrome_binary = os.environ.get(
                'CHROME_BIN', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
            chromedriver_path = os.environ.get(
                'CHROMEDRIVER_PATH', '/opt/homebrew/bin/chromedriver')
        else:
            chrome_binary = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
            chromedriver_path = os.environ.get(
                'CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

        options.binary_location = chrome_binary
        options.add_argument('--browser-binary=' + chrome_binary)

        from selenium.webdriver.chrome.service import Service
        service = Service(executable_path=chromedriver_path)
        service.creation_flags = 0  # Ensure no special flags are set
        self.driver = webdriver.Chrome(service=service, options=options)

        logger.info(
            f"Browser initialized in {'headless' if self.headless else 'normal'} mode")

    def login_to_google(self):
        """Login to Google account"""
        try:
            self._get_page_with_timeout('https://meet.google.com', timeout=10)
            self.driver.find_element(By.CSS_SELECTOR, '[data-noaft]')
            logger.info("Already logged into Google account")
            return
        except Exception:
            logger.info("No active Google session found")

            # Get credentials from environment
            email = os.getenv('GOOGLE_EMAIL')
            password = os.getenv('GOOGLE_PASSWORD')

            if not email or not password:
                raise Exception(
                    "GOOGLE_EMAIL and GOOGLE_PASSWORD environment variables must be set")

            logger.info("Starting automated login sequence...")
            self._get_page_with_timeout(
                'https://accounts.google.com', timeout=10)

            # Enter email
            try:
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[type="email"]'))
                )
                email_input.clear()
                email_input.send_keys(email)
                email_input.send_keys(webdriver.Keys.RETURN)
                logger.info("Email entered successfully")

                # Wait for email page to be processed
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, 'input[type="email"]'))
                )
            except Exception as e:
                raise Exception(f"Failed to enter email: {str(e)}")

            # Enter password
            try:
                # Wait for password field to be both present AND interactable
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'input[type="password"]'))
                )
                password_input.clear()
                password_input.send_keys(password)
                password_input.send_keys(webdriver.Keys.RETURN)
                logger.info("Password entered successfully")
            except Exception as e:
                raise Exception(f"Failed to enter password: {str(e)}")

            # Verify login success
            time.sleep(5)
            self.driver.get('https://meet.google.com')
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-noaft]'))
                )
                logger.info("Successfully logged into Google account")
            except Exception:
                raise Exception("Login failed.")

    def join_meet(self, meet_url: str):
        """Join a Google Meet call using the provided meeting URL"""
        self.meet_url = meet_url
        try:
            logger.info(f"Joining meet: {meet_url}")
            self.driver.get(meet_url)

            # Wait for and click the join button
            join_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='Ask to join']]")
                )
            )
            join_button.click()
            logger.info("Clicked 'Ask to join' button")
            set_state(RecorderState.WAITING)

            # Try to turn off microphone and camera if they're on
            try:
                mic_button = self.driver.find_element(
                    By.CSS_SELECTOR, "[aria-label='Turn off microphone']")
                mic_button.click()
                logger.info("Turned off microphone")
            except Exception:
                logger.info("Microphone already off or button not found")

            try:
                camera_button = self.driver.find_element(
                    By.CSS_SELECTOR, "[aria-label='Turn off camera']")
                camera_button.click()
                logger.info("Turned off camera")
            except Exception:
                logger.info("Camera already off or button not found")

            # Wait to be admitted to the meeting
            logger.info("Waiting to be admitted...")
            max_wait_time = 300
            wait_start_time = time.time()
            while time.time() - wait_start_time < max_wait_time:
                try:
                    leave_button = self.driver.find_element(
                        By.CSS_SELECTOR, "[aria-label='Leave call']")
                    logger.info("Successfully joined the meeting!")
                    break
                except Exception:
                    logger.info(
                        "Still waiting to be admitted to the meeting...")
                    time.sleep(5)
            else:
                logger.error("Timed out waiting to be admitted to the meeting")
                set_state(RecorderState.READY)
                raise Exception(
                    "Failed to join meeting: Admission timeout after 5 minutes")

            # Start recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            set_state(RecorderState.RECORDING)
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
            logger.error(f"Error joining meet: {e}")
            raise e

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
            set_state(RecorderState.READY)

    def stop_recording(self):
        """Stop the recording, transcribe it, and add it to database"""
        if self.recording and self.recorder_thread:
            self.audio_system.stop_recording()
            self.recorder_thread.join()
            self.recording = False
            set_state(RecorderState.PROCESSING)

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
                        logger.error(
                            f"Failed to add recording to database: {str(db_error)}")

            # Reset for next meeting without closing the WebDriver session
            self.reset_meeting()
            set_state(RecorderState.READY)

    def reset_meeting(self):
        """Reset the recorder state for a new meeting without closing the WebDriver session"""
        self.meet_url = None
        self.current_recording_filename = None
        self._get_page_with_timeout('https://meet.google.com', timeout=15)
        logger.info("Recorder reset to a neutral state.")

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

    def _get_page_with_timeout(self, url: str, timeout: int = 10) -> bool:
        """
        Load a page with timeout, gracefully stopping if it takes too long.

        Args:
            url: The URL to load
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if page loaded completely, False if stopped due to timeout
        """
        original_timeout = self.driver.timeouts.page_load
        try:
            self.driver.set_page_load_timeout(timeout)
            try:
                self.driver.get(url)
                return True
            except Exception as e:
                if "timeout" in str(e).lower():
                    logger.warning(
                        f"Page load timed out after {timeout}s, stopping further loading: {url}")
                    self.driver.execute_script("window.stop();")
                    return False
                else:
                    logger.error(f"Error loading page {url}: {str(e)}")
                    raise
        finally:
            self.driver.set_page_load_timeout(original_timeout)


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Google Meet Recorder")
    parser.add_argument("--meet_url", help="The Google Meet URL to record")
    parser.add_argument("--headless", dest="headless",
                        action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--no-headless", dest="headless",
                        action="store_false", help="Run Chrome with UI (non-headless)")
    parser.set_defaults(headless=os.path.exists("/.dockerenv"))
    args = parser.parse_args()

    if not args.meet_url:
        import os
        args.meet_url = os.getenv("MEET_URL")
    if not args.meet_url:
        print("Error: No meeting URL provided via command line argument or MEET_URL environment variable.")
        exit(1)

    recorder = GoogleMeetRecorder(args.headless)
    recorder.login_to_google()
    recorder.join_meet(args.meet_url)

    try:
        while True:
            import time
            time.sleep(5)
    except KeyboardInterrupt:
        recorder.cleanup()
