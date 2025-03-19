import requests
import os
import json
from pathlib import Path
from collections import defaultdict
import dateutil.parser
import datetime
from statistics import mode
from itertools import groupby
from tldr_generator import generate_tldr

# Minimum utterance length in seconds to consider for speaker identification
MIN_UTTERANCE_LENGTH = 1.0
# Minimum time gap in seconds to consider as a real speaker change
MIN_SPEAKER_CHANGE_GAP = 0.5


def transcribe_audio(audio_path, speaker_timestamps=None, recording_launch_time=None, api_key=None):
    """
    Transcribe audio using ElevenLabs API and perform diarization if speaker timestamps are provided.

    Args:
        audio_path (str): Path to the audio file
        speaker_timestamps (list, optional): List of speaker activity timestamps in the format:
            [{"timestamp": "2025-03-07T08:59:40.530190+00:00", "speakers": ["Speaker Name"]}, ...]
        recording_launch_time (datetime, optional): Start time of the recording as a datetime object
        api_key (str, optional): ElevenLabs API key

    Returns:
        dict: Dictionary with "text" field containing the raw transcript, "diarized" field
            containing the diarized transcript, and "tldr" field containing a short summary in Russian
    """
    # Validate input
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if api_key is None:
        try:
            api_key = os.getenv('ELEVENLABS_API_KEY')
        except ImportError:
            raise ValueError(
                "ElevenLabs API key not provided and could not be imported from config")

    # Step 1: Transcribe the audio using ElevenLabs API
    transcription = _transcribe_audio_elevenlabs(audio_path, api_key)

    if not transcription:
        return {"text": "", "diarized": [], "tldr": ""}

    # Extract raw text
    raw_text = transcription.get('text', '')

    # If no speaker timestamps or recording time provided, return only the raw text
    if not speaker_timestamps or not recording_launch_time:
        return {"text": raw_text, "diarized": [], "tldr": ""}

    # Convert recording_launch_time to string format if it's a datetime object
    if isinstance(recording_launch_time, datetime.datetime):
        recording_launch_time = recording_launch_time.isoformat()

    # Step 2: Process the transcript with speaker information
    # Create speaker mapping
    speaker_map = create_improved_speaker_map(
        transcription, speaker_timestamps, recording_launch_time)

    # Generate diarized transcript
    timestamped_transcript = generate_timestamped_transcript(
        transcription, speaker_map, recording_launch_time)

    # Transform to required output format
    diarized_output = []
    for entry in timestamped_transcript:
        diarized_output.append({
            "speaker": entry["speaker"],
            "text": entry["text"],
            "start": entry["absolute_start"],
            "end": entry["absolute_end"]
        })

    # Create the response dictionary
    result = {
        "text": raw_text,
        "diarized": diarized_output
    }

    # Generate TLDR summary in Russian
    try:
        tldr = generate_tldr(result)
        result["tldr"] = tldr
    except Exception as e:
        print(f"Error generating TLDR: {e}")

    return result


def _transcribe_audio_elevenlabs(file_path, api_key):
    """Transcribe an audio file using ElevenLabs API."""
    url = "https://api.elevenlabs.io/v1/speech-to-text"

    headers = {
        "xi-api-key": api_key
    }

    # Currently, only 'scribe_v1' is available as per the documentation
    model_id = "scribe_v1"

    # Prepare the form data
    files = {"file": (os.path.basename(file_path), open(file_path, "rb"))}
    data = {
        "model_id": model_id,
        "diarize": True,
        "language_code": "rus",
        "timestamps_granularity": "word"
    }

    print(
        f"Uploading {file_path} for transcription with diarization enabled...")

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses

        transcription = response.json()
        return transcription
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def find_speaker_at_time(speaker_activity, time_point):
    """Find the active speaker at a given time point."""
    # Sort activity by timestamp
    sorted_activity = sorted(speaker_activity,
                             key=lambda x: dateutil.parser.parse(x["timestamp"]))

    # Find the last activity entry before the given time point
    current_speaker = None
    for activity in sorted_activity:
        activity_time = dateutil.parser.parse(activity["timestamp"])
        if activity_time <= time_point:
            current_speaker = activity["speakers"][0] if activity["speakers"] else None
        else:
            break

    return current_speaker


def extract_speaker_segments(transcript):
    """Extract segments where each ElevenLabs speaker_id speaks continuously."""
    segments = []
    current_segment = None

    for word in transcript.get("words", []):
        if word.get("type") != "word":
            continue

        speaker_id = word.get("speaker_id")
        if not speaker_id:
            continue

        start_time = word.get("start", 0)
        end_time = word.get("end", start_time)

        # If this is a new speaker or there's a long pause, start a new segment
        if (not current_segment or
            current_segment["speaker_id"] != speaker_id or
                start_time - current_segment["end_time"] > MIN_SPEAKER_CHANGE_GAP):

            if current_segment and current_segment["end_time"] - current_segment["start_time"] >= MIN_UTTERANCE_LENGTH:
                segments.append(current_segment)

            current_segment = {
                "speaker_id": speaker_id,
                "start_time": start_time,
                "end_time": end_time,
                "words": [word.get("text", "")]
            }
        else:
            # Continue the current segment
            current_segment["end_time"] = end_time
            current_segment["words"].append(word.get("text", ""))

    # Add the last segment
    if current_segment and current_segment["end_time"] - current_segment["start_time"] >= MIN_UTTERANCE_LENGTH:
        segments.append(current_segment)

    return segments


def create_improved_speaker_map(transcript, speaker_activity, recording_start_time):
    """Create a more robust mapping between speaker_ids and actual speakers."""
    reference_time = dateutil.parser.parse(recording_start_time)

    # Extract continuous speech segments by speaker_id
    segments = extract_speaker_segments(transcript)

    # Count which real speaker was active during each segment
    speaker_votes = defaultdict(lambda: defaultdict(int))

    for segment in segments:
        # Sample multiple points within the segment to find who was speaking
        segment_duration = segment["end_time"] - segment["start_time"]
        # Sample at least 3 points or every 0.5 seconds
        num_samples = max(3, int(segment_duration / 0.5))

        for i in range(num_samples):
            sample_time_seconds = segment["start_time"] + \
                (segment_duration * i / (num_samples - 1))
            sample_time = reference_time + \
                datetime.timedelta(seconds=sample_time_seconds)

            # Find who was active at this time
            active_speaker = find_speaker_at_time(
                speaker_activity, sample_time)
            if active_speaker:
                speaker_votes[segment["speaker_id"]][active_speaker] += 1

    # For each ElevenLabs speaker_id, find the most frequently active real speaker
    speaker_map = {}
    for speaker_id, votes in speaker_votes.items():
        if votes:
            # Find the real speaker with the most votes
            speaker_map[speaker_id] = max(votes.items(), key=lambda x: x[1])[0]

    # Debug output
    print("Speaker votes distribution:")
    for speaker_id, votes in speaker_votes.items():
        print(f"  Speaker ID '{speaker_id}' votes: {dict(votes)}")

    return speaker_map


def consolidate_speaker_turns(transcript_with_speakers, min_gap=1.0):
    """Consolidate speaker turns to avoid unrealistic rapid speaker changes."""
    if not transcript_with_speakers:
        return []

    consolidated = []
    current_group = transcript_with_speakers[0].copy()

    for entry in transcript_with_speakers[1:]:
        # If same speaker and small time gap, merge
        if (entry["speaker"] == current_group["speaker"] and
                entry["start_time"] - current_group["end_time"] < min_gap):
            current_group["text"] += " " + entry["text"]
            current_group["end_time"] = entry["end_time"]
            current_group["absolute_end"] = entry["absolute_end"]
        else:
            # Add the completed group and start a new one
            consolidated.append(current_group)
            current_group = entry.copy()

    # Add the last group
    consolidated.append(current_group)

    return consolidated


def generate_timestamped_transcript(transcript, speaker_map, recording_start_time):
    """Generate a timestamped transcript with speaker information."""
    result = []
    reference_time = dateutil.parser.parse(recording_start_time)

    current_speaker = None
    current_text = []
    start_time = None

    for word in transcript.get("words", []):
        if word.get("type") != "word":
            continue

        speaker_id = word.get("speaker_id")
        speaker_name = speaker_map.get(
            speaker_id, f"Unknown Speaker ({speaker_id})")

        # If start time is not set, set it (for the first word)
        if start_time is None:
            start_time = word.get("start", 0)

        # If speaker changed, add the previous utterance to the result
        if speaker_name != current_speaker and current_text:
            end_time = word.get("start", 0)
            absolute_start = reference_time + \
                datetime.timedelta(seconds=start_time)
            absolute_end = reference_time + \
                datetime.timedelta(seconds=end_time)

            result.append({
                "speaker": current_speaker,
                "text": " ".join(current_text),
                "start_time": start_time,
                "end_time": end_time,
                "absolute_start": absolute_start.isoformat(),
                "absolute_end": absolute_end.isoformat()
            })

            # Reset for new speaker
            current_text = []
            start_time = word.get("start", 0)

        # Add word to current utterance
        current_text.append(word.get("text", ""))
        current_speaker = speaker_name

    # Add the last utterance
    if current_text and current_speaker:
        end_time = transcript["words"][-1].get("end",
                                               0) if transcript.get("words") else 0
        absolute_start = reference_time + \
            datetime.timedelta(seconds=start_time)
        absolute_end = reference_time + datetime.timedelta(seconds=end_time)

        result.append({
            "speaker": current_speaker,
            "text": " ".join(current_text),
            "start_time": start_time,
            "end_time": end_time,
            "absolute_start": absolute_start.isoformat(),
            "absolute_end": absolute_end.isoformat()
        })

    # Consolidate speaker turns to avoid unrealistic rapid changes
    result = consolidate_speaker_turns(result)

    return result
