from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RecorderState(str, Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    WAITING = "waiting"
    JOINING = "joining"
    RECORDING = "recording"
    PROCESSING = "processing"


# Global state variable
current_state = RecorderState.INITIALIZING


def set_state(new_state: RecorderState):
    global current_state
    logger.info(f"State changing from {current_state} to {new_state}")
    current_state = new_state


def get_state() -> RecorderState:
    return current_state
