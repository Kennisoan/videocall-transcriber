import json
from datetime import datetime


def parse_timestamp(timestamp_str):
    """Convert ISO timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        print(f"Error parsing timestamp '{timestamp_str}': {e}")
        raise


def calculate_relative_time(timestamp, start_time):
    """Calculate seconds elapsed from start_time to timestamp."""
    if not isinstance(start_time, datetime):
        raise TypeError("start_time must be a datetime object")
    if not isinstance(timestamp, datetime):
        raise TypeError("timestamp must be a datetime object")

    delta = timestamp - start_time
    return delta.total_seconds()


def convert_slack_data(slack_data, recording_start, offset=0):
    """
    Convert raw Slack speaker data to speaker activity blocks.

    Args:
        slack_data: Raw Slack data with timestamps and speakers
        recording_start: ISO format timestamp when recording began
        offset: Time adjustment in seconds

    Returns:
        List of speaker activity blocks with start/end times
    """
    start_time = parse_timestamp(recording_start)
    speaking_events = []
    active_speakers = {}

    for entry in slack_data:
        current_time = parse_timestamp(entry['timestamp'])
        relative_time = calculate_relative_time(current_time, start_time)

        current_speakers = set(entry['speakers'])
        previous_speakers = set(active_speakers.keys())

        # Handle speakers who stopped speaking
        for speaker in previous_speakers - current_speakers:
            speaking_events.append({
                "speaker": speaker,
                "start": active_speakers[speaker],
                "end": relative_time
            })
            del active_speakers[speaker]

        # Handle speakers who started speaking
        for speaker in current_speakers - previous_speakers:
            active_speakers[speaker] = relative_time

    # Sort by start time
    speaking_events.sort(key=lambda x: x["start"])

    # Apply offset
    if offset:
        for event in speaking_events:
            event["start"] += offset
            event["end"] += offset

    return speaking_events


def get_speaker_duration(speaker, segment, adjusted_blocks):
    """Calculate how long a speaker is active during a segment."""
    relevant_blocks = [
        block for block in adjusted_blocks
        if block["speaker"] == speaker and
        not (block["end"] <= segment["start"]
             or block["start"] >= segment["end"])
    ]

    total_duration = 0
    for block in relevant_blocks:
        overlap_start = max(block["start"], segment["start"])
        overlap_end = min(block["end"], segment["end"])
        total_duration += overlap_end - overlap_start

    return total_duration


def assign_speakers(speaker_activity, whisper_segments, speaker_offset=0, duration_ratio=10):
    """Assign speakers to segments using the diarization algorithm."""

    # Adjust speaker times by offset
    adjusted_blocks = [
        {
            **block,
            "start": block["start"] + speaker_offset,
            "end": block["end"] + speaker_offset
        }
        for block in speaker_activity
    ]

    result_segments = []

    for segment in whisper_segments:
        segment_start = segment["start"]
        segment_end = segment["end"]

        # Initial speaker assignment using the original rules
        assigned_speaker = None

        # 1. Find block that both starts and ends within segment
        for block in adjusted_blocks:
            if block["start"] >= segment_start and block["end"] <= segment_end:
                assigned_speaker = block["speaker"]
                break

        # 2. Find block that is ongoing at segment start
        if not assigned_speaker:
            for block in adjusted_blocks:
                if block["start"] <= segment_start and block["end"] >= segment_start:
                    assigned_speaker = block["speaker"]
                    break

        # 3. Find block that starts within segment
        if not assigned_speaker:
            for block in adjusted_blocks:
                if block["start"] >= segment_start and block["start"] <= segment_end:
                    assigned_speaker = block["speaker"]
                    break

        # Check if any other speaker has more speaking time
        if assigned_speaker:
            assigned_duration = get_speaker_duration(
                assigned_speaker,
                segment,
                adjusted_blocks
            )

            other_speakers = set(block["speaker"] for block in adjusted_blocks)
            other_speakers.remove(assigned_speaker)

            for other_speaker in other_speakers:
                other_duration = get_speaker_duration(
                    other_speaker,
                    segment,
                    adjusted_blocks
                )
                if other_duration >= assigned_duration * duration_ratio:
                    assigned_speaker = other_speaker
                    break

        # Add the result to output
        result_segments.append({
            "speaker": assigned_speaker,
            "text": segment["text"],
            "start": segment["start"],
            "end": segment["end"]
        })

    return result_segments


def merge_consecutive_segments(segments):
    """Merge consecutive segments that have the same speaker."""
    if not segments:
        return segments

    merged = []
    current = segments[0].copy()

    for next_segment in segments[1:]:
        if (next_segment['speaker'] == current['speaker'] and
                abs(next_segment['start'] - current['end']) < 0.3):  # 300ms threshold
            # Merge segments
            current['text'] = ' '.join(
                (current['text'] + ' ' + next_segment['text']).split()
            )
            current['end'] = next_segment['end']
        else:
            # Add current segment to results and start a new one
            current['text'] = ' '.join(current['text'].split())
            merged.append(current)
            current = next_segment.copy()

    # Add the last segment
    current['text'] = ' '.join(current['text'].split())
    merged.append(current)

    return merged


def diarize_transcript(whisper_output, slack_data, recording_start, speaker_offset=0, duration_ratio=10):
    """
    Main function to process raw Whisper and Slack data and assign speakers.

    Args:
        whisper_output: Raw output from Whisper API
        slack_data: Raw Slack data with timestamps and speakers
        recording_start: ISO format timestamp when recording began
        speaker_offset: Time adjustment for speaker data (in seconds)
        duration_ratio: Threshold for speaker reassignment

    Returns:
        Whisper segments with speakers assigned
    """
    # Extract segments from Whisper output
    whisper_segments = whisper_output.get('segments', [])

    # Convert Slack data to speaker activity blocks
    # offset handled in assign_speakers
    speaker_activity = convert_slack_data(slack_data, recording_start, 0)

    # Assign speakers to segments
    segments = assign_speakers(
        speaker_activity,
        whisper_segments,
        speaker_offset,
        duration_ratio
    )

    # Merge consecutive segments with the same speaker
    return merge_consecutive_segments(segments)


# Example usage
if __name__ == "__main__":
    # Example of how to use the diarizer
    with open('whisper.json', 'r', encoding='utf-8') as f:
        whisper_data = json.load(f)

    with open('slack_data.json', 'r', encoding='utf-8') as f:
        slack_data = json.load(f)

    recording_start = "2025-02-19T08:29:10.059506+00:00"

    result = diarize_transcript(
        whisper_data,
        slack_data,
        recording_start,
        speaker_offset=-2.2,
        duration_ratio=1.5
    )

    # Output the result
    with open('diarized_transcript.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
