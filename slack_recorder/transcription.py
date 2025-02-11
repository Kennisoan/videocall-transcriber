import re
import json
import os
import logging
from datetime import datetime, timedelta
import openai

logger = logging.getLogger(__name__)


class TranscriptionManager:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai.base_url = os.getenv(
            'OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.client = openai.Client()

    def get_active_speaker(self, query_time, events, fallback="unknown"):
        """
        Returns the last non-empty speaker from events whose time is <= query_time.
        If none is found, returns fallback.
        """
        active = None
        for e in events:
            if e['time'] <= query_time:
                if e['speakers']:
                    active = e['speakers'][0]
            else:
                break
        return active if active else fallback

    def split_into_sentences(self, text):
        """
        Splits text into sentences based on ending punctuation.
        This simple regex assumes that a sentence ends with period, exclamation, or question mark
        followed by at least one whitespace character.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s for s in sentences if s]

    def diarize_transcription(self, transcription, speaker_timestamps):
        """
        Diarizes transcription by splitting each Whisper segment into full sentences (so sentences never get cut off).
        Each sentence is assigned an approximate absolute start/end time computed using proportional allocation 
        (assuming a constant speech rate within the segment). The speaker is determined by checking the active
        speaker at the sentence's midpoint using speaker_timestamps (ignoring empty events).

        Consecutive sentences for the same speaker are merged when the gap is small.
        """
        # Build a list of valid speaker events (only those with non-empty speakers)
        events = [
            {'time': datetime.fromisoformat(
                evt['timestamp']), 'speakers': evt['speakers']}
            for evt in speaker_timestamps if evt['speakers']
        ]
        events.sort(key=lambda x: x['time'])

        if events:
            base_time = events[0]['time']
        else:
            raise ValueError(
                "No valid speaker timestamps found to derive base time")

        diarized_segments = []

        # Process each Whisper segment
        for seg in transcription['segments']:
            # Compute the absolute start and end times using base_time.
            seg_abs_start = base_time + timedelta(seconds=seg['start'])
            seg_abs_end = base_time + timedelta(seconds=seg['end'])
            seg_duration = (seg_abs_end - seg_abs_start).total_seconds()
            seg_text = seg['text'].strip()
            if not seg_text:
                continue

            # Split the segment into full sentences so that sentences never get cut in half.
            sentences = self.split_into_sentences(seg_text)
            if not sentences:
                sentences = [seg_text]

            # Compute the total characters to proportionally allocate times.
            total_chars = sum(len(s) for s in sentences)
            cumulative_chars = 0

            for sentence in sentences:
                # Allocate absolute times based on the proportion of text.
                sentence_start = seg_abs_start + \
                    timedelta(seconds=(cumulative_chars /
                                       total_chars) * seg_duration)
                cumulative_chars += len(sentence)
                sentence_end = seg_abs_start + \
                    timedelta(seconds=(cumulative_chars /
                                       total_chars) * seg_duration)
                mid_time = sentence_start + (sentence_end - sentence_start) / 2

                # Determine active speaker at the sentence midpoint.
                speaker = self.get_active_speaker(mid_time, events)

                diarized_segments.append({
                    "speaker": speaker,
                    "text": sentence,
                    "start": sentence_start.isoformat(),
                    "end": sentence_end.isoformat()
                })

        # Merge consecutive segments with the same speaker if the gap is negligible.
        merged_segments = []
        merge_gap_threshold = 0.5  # seconds; adjust as needed

        for seg in diarized_segments:
            if not merged_segments:
                merged_segments.append(seg)
            else:
                last_seg = merged_segments[-1]
                last_end = datetime.fromisoformat(last_seg['end'])
                curr_start = datetime.fromisoformat(seg['start'])
                gap = (curr_start - last_end).total_seconds()
                if seg['speaker'] == last_seg['speaker'] and gap < merge_gap_threshold:
                    # Merge the segments by extending the end time and combining text.
                    last_seg['end'] = seg['end']
                    last_seg['text'] = last_seg['text'] + " " + seg['text']
                else:
                    merged_segments.append(seg)

        return merged_segments

    def transcribe_audio(self, audio_path, speaker_timestamps=None):
        try:
            logger.info(f"Starting transcription for: {audio_path}")

            from pydub import AudioSegment
            file_data = open(audio_path, "rb")
            file_size = os.path.getsize(audio_path)
            audio_for_split = AudioSegment.from_file(audio_path)

            MAX_SIZE = 26214400  # Maximum allowed file size in bytes

            if file_size <= MAX_SIZE:
                # Direct transcription without splitting
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file_data,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
                transcript_json = response.model_dump()
                logger.info("Transcription completed successfully")
            else:
                # If file is too large, split compressed audio into chunks for transcription
                # Total duration in milliseconds
                duration_ms = len(audio_for_split)

                # Calculate allowed duration for each chunk (in ms) based on average bytes per ms
                allowed_duration_ms = int(duration_ms * MAX_SIZE / file_size)
                if allowed_duration_ms <= 0:
                    allowed_duration_ms = 10000

                num_chunks = (duration_ms // allowed_duration_ms) + \
                    (1 if duration_ms % allowed_duration_ms > 0 else 0)
                logger.info(
                    f"File size ({file_size} bytes) exceeds limit, splitting into {num_chunks} chunks for transcription")

                merged_segments = []
                merged_text = ""

                for i in range(num_chunks):
                    start_ms = i * allowed_duration_ms
                    end_ms = min((i + 1) * allowed_duration_ms, duration_ms)
                    chunk_audio = audio_for_split[start_ms:end_ms]
                    from io import BytesIO
                    chunk_io = BytesIO()
                    # Export chunk with the same compression settings to mp3
                    chunk_audio.export(chunk_io, format="mp3", bitrate="64k")
                    chunk_io.seek(0)
                    # Provide a name for the API to detect the file type
                    chunk_io.name = f"chunk_{i}.mp3"

                    logger.info(
                        f"Transcribing chunk {i + 1}/{num_chunks} from {start_ms}ms to {end_ms}ms")
                    chunk_response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=chunk_io,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                    chunk_json = chunk_response.model_dump()

                    # Adjust segment timestamps relative to the overall audio
                    chunk_offset = start_ms / 1000.0
                    if "segments" in chunk_json:
                        for segment in chunk_json["segments"]:
                            if "start" in segment:
                                segment["start"] += chunk_offset
                            if "end" in segment:
                                segment["end"] += chunk_offset
                        merged_segments.extend(chunk_json["segments"])
                    if "text" in chunk_json:
                        merged_text = (merged_text + " " +
                                       chunk_json["text"]).strip()

                final_json = {
                    "text": merged_text,
                    "segments": merged_segments
                }
                logger.info(
                    "Transcription of all chunks completed successfully")
                logger.info(f"Final transcription JSON: {final_json}")
                transcript_json = final_json

            # Extract text and create diarized version if speaker timestamps provided
            transcription_text = transcript_json.get('text', '')
            diarized_segments = None
            if speaker_timestamps:
                try:
                    diarized_segments = self.diarize_transcription(
                        transcript_json, speaker_timestamps)
                except Exception as e:
                    logger.error(f"Error during diarization: {str(e)}")

            return {
                'text': transcription_text,
                'diarized': diarized_segments
            }

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return None
