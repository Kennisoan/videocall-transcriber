import os
import time
import logging
import sys
import platform
import argparse
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
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
        logging.FileHandler('slack_recorder.log')
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()


class SlackHuddleRecorder:
    def __init__(self, app_token, user_token, headless=True):
        self.app_token = app_token
        self.user_token = user_token
        self.web_client = WebClient(token=self.user_token)
        self.socket_client = None
        self.driver = None
        self.recording = False
        self.recorder_thread = None
        self.running = True
        self.last_huddle_leave_time = 0
        self.is_joining_huddle = False
        self.current_huddle_link = None
        self.headless = headless

        # Initialize managers
        self.db_manager = DatabaseManager()
        self.transcription_manager = TranscriptionManager()
        self.audio_system = None

        # Create directories
        os.makedirs('recordings', exist_ok=True)

        # Initialize Slack clients
        try:
            auth_test = self.web_client.auth_test()
            logger.info(f"Connected to Slack as: {auth_test['user']}")

            self.socket_client = SocketModeClient(
                app_token=self.app_token,
                web_client=self.web_client
            )
        except Exception as e:
            logger.error(f"Failed to connect to Slack: {str(e)}")
            raise

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

    # Specialized function for clicking using JavaScript
    def _js_click(self, element):
        try:
            self.driver.execute_script(
                "arguments[0].click();", element)
            logger.info("Clicked button using JS. HTML: %s",
                        element.get_attribute('outerHTML'))
        except Exception as e:
            logger.error("JS click failed: %s", e)

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

        if self.headless:
            options.add_argument('--headless=new')

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

        # Check if we need to login
        self.driver.get("https://app.slack.com")
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".ss-c-workspaces")
                )
            )
            logger.info("Using existing session")
        except:
            # Get environment variables for login
            workspace_url = os.environ.get("SLACK_WORKSPACE_URL")
            email = os.environ.get("SLACK_EMAIL")
            password = os.environ.get("SLACK_PASSWORD")

            if not all([workspace_url, email, password]):
                raise Exception(
                    "Missing required environment variables: SLACK_WORKSPACE_URL, SLACK_EMAIL, and SLACK_PASSWORD must be set")

            try:
                logger.info("Starting Slack login process...")
                self.driver.get("https://slack.com/workspace-signin")

                # Enter workspace URL
                logger.info("Entering workspace URL...")
                workspace_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-qa='signin_domain_input']"))
                )
                # Extract everything before .slack.com
                workspace_name = workspace_url.split('.')[0]
                workspace_input.send_keys(workspace_name)

                # Click continue button
                logger.info("Clicking continue button...")
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[data-qa='submit_team_domain_button']"))
                )
                continue_button.click()

                # Click "sign in with password" link
                logger.info("Clicking 'sign in with password' link...")
                password_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[data-qa='sign_in_password_link']"))
                )
                password_link.click()

                # Enter email and password
                logger.info("Entering email and password...")
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-qa='login_email']"))
                )
                password_input = self.driver.find_element(
                    By.CSS_SELECTOR, "[data-qa='login_password']")

                email_input.send_keys(email)
                password_input.send_keys(password)

                # Click sign in button
                logger.info("Clicking sign in button...")
                signin_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[data-qa='signin_button']"))
                )
                signin_button.click()

                # Wait for successful login
                logger.info("Waiting for successful login...")
                browser_link = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR,
                         "[data-qa='ssb_redirect_open_in_browser']")
                    )
                )
                browser_link.click()
                logger.info("Checking login status...")
                time.sleep(10)
                self.driver.get("https://app.slack.com")
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".ss-c-workspaces")
                        )
                    )
                    logger.info("Logged in successfully!")
                except Exception as e:
                    logger.error(f"Failed to log in to Slack: {str(e)}")
                    raise

            except Exception as e:
                logger.error(f"Failed to log in to Slack: {str(e)}")
                raise

    def join_huddle(self, huddle_link):
        """Join a Slack huddle using its link"""
        if self.is_joining_huddle or self.recording:
            logger.info(
                f"Already in or joining a huddle, ignoring join request for: {huddle_link}")
            return

        try:
            self.is_joining_huddle = True
            self.current_huddle_link = huddle_link
            logger.info(f"Joining huddle: {huddle_link}")

            self.driver.get(huddle_link)

            # Wait for and manually follow the "use Slack in your browser" link
            browser_link_element = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-qa='ssb_redirect_open_in_browser']"))
            )
            browser_link = browser_link_element.get_attribute('href')
            logger.info("Following join link: %s", browser_link)
            self.driver.get(browser_link)

            # Wait for the join button
            logger.info("Waiting for join button...")
            join_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-qa='huddle_from_link_speed_bump_modal_old_go']"))
            )

            self._js_click(join_btn)

            # Start recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.start_recording(f"huddle_recording_{timestamp}.wav")

            # Monitor huddle status
            def check_huddle_status():
                time.sleep(10)

                while self.recording:
                    try:
                        # Find the peer list and count huddle participants
                        peer_list = self.driver.find_element(
                            By.CLASS_NAME, "p-peer_tile_list")
                        participant_tiles = peer_list.find_elements(
                            By.CLASS_NAME, "p-peer_tile__container")

                        if len(participant_tiles) <= 1:
                            logger.info(
                                "Only bot remaining in huddle, disconnecting...")
                            self.stop_recording()
                            break

                        # Check every 3 seconds
                        time.sleep(3)

                    except Exception as e:
                        logger.info(f"Huddle ended or disconnected: {str(e)}")
                        self.stop_recording()
                        break

            threading.Thread(target=check_huddle_status, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to join huddle: {str(e)}")
            try:
                page_source = self.driver.page_source
                logger.error("Current page HTML at time of failure:")
                logger.error(page_source)
            except Exception as page_error:
                logger.error(f"Could not get page source: {str(page_error)}")
            self.is_joining_huddle = False
            self.current_huddle_link = None

    def start_recording(self, filename):
        """Start recording a huddle"""
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

            # Leave the huddle
            try:
                leave_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "[data-qa='huddle_mini_player_leave_button']"))
                )
                self._js_click(leave_button)
            except Exception as e:
                logger.error(f"Failed to click leave huddle button: {str(e)}")

            # Reset huddle state
            self.is_joining_huddle = False
            self.current_huddle_link = None
            self.last_huddle_leave_time = time.time()

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
                        source="slack",
                        transcript=transcript
                    )
                except Exception as e:
                    logger.error(f"Failed to process recording: {str(e)}")
                    # Still try to save the recording without transcript
                    try:
                        self.db_manager.add_recording(
                            filename=os.path.basename(
                                self.current_recording_filename),
                            source="slack",
                            transcript=None
                        )
                    except Exception as db_error:
                        logger.error(
                            f"Failed to add recording to database: {str(db_error)}")

    def process_event(self, client, req):
        """Process incoming Slack events"""
        try:
            # Ignore huddle events if we're in cooldown period
            if time.time() - self.last_huddle_leave_time < 30:
                logger.info("Ignoring huddle event - in cooldown period")
                if hasattr(req, 'envelope_id'):
                    response = SocketModeResponse(envelope_id=req.envelope_id)
                    client.send_socket_mode_response(response)
                return

            # Ignore huddle events if we're already in or joining a huddle
            if self.is_joining_huddle or self.recording:
                logger.info(
                    "Ignoring huddle event - already in or joining a huddle")
                if hasattr(req, 'envelope_id'):
                    response = SocketModeResponse(envelope_id=req.envelope_id)
                    client.send_socket_mode_response(response)
                return

            if req.payload.get("type") == "event_callback":
                event = req.payload.get("event", {})
                logger.info(f"Event callback details: {event}")

                if event.get("type") == "message" and event.get("subtype") == "huddle_thread":
                    logger.info(f"Huddle event detected: {event}")
                    huddle_link = event.get("room", {}).get("huddle_link")
                    if huddle_link:
                        logger.info(f"Huddle link found: {huddle_link}")
                        self.join_huddle(huddle_link)

                    # Acknowledge the event
                    if hasattr(req, 'envelope_id'):
                        response = SocketModeResponse(
                            envelope_id=req.envelope_id)
                        client.send_socket_mode_response(response)

        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")

    def start(self):
        """Start listening for huddles"""
        try:
            logger.info("Starting huddle recorder...")
            self.socket_client.socket_mode_request_listeners.append(
                self.process_event)
            self.socket_client.connect()
            logger.info("Connected and listening for huddles")

            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Shutting down...")
        self.running = False
        if self.recording:
            self.stop_recording()

        # Close socket client
        if self.socket_client:
            self.socket_client.close()

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


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Slack Huddle Recorder')
        parser.add_argument('--no-headless', action='store_true',
                            help='Run in non-headless mode (useful for initial login)')
        args = parser.parse_args()

        # Get environment variables and validate them
        SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
        SLACK_USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
        SLACK_WORKSPACE_URL = os.environ.get("SLACK_WORKSPACE_URL")
        SLACK_EMAIL = os.environ.get("SLACK_EMAIL")
        SLACK_PASSWORD = os.environ.get("SLACK_PASSWORD")

        required_vars = {
            "SLACK_APP_TOKEN": SLACK_APP_TOKEN,
            "SLACK_USER_TOKEN": SLACK_USER_TOKEN,
            "SLACK_WORKSPACE_URL": SLACK_WORKSPACE_URL,
            "SLACK_EMAIL": SLACK_EMAIL,
            "SLACK_PASSWORD": SLACK_PASSWORD
        }

        missing_vars = [k for k, v in required_vars.items() if not v]
        if missing_vars:
            logger.error(
                f"Missing required environment variables: {', '.join(missing_vars)}")
            sys.exit(1)

        # Create and start recorder
        recorder = SlackHuddleRecorder(
            SLACK_APP_TOKEN, SLACK_USER_TOKEN, headless=not args.no_headless)
        recorder.start()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
