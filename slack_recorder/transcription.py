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

    def diarize_transcription(self, transcription, speaker_timestamps, recording_launch_time):
        """
        Diarizes transcription using the diarization module.

        Args:
            transcription: Whisper transcription output
            speaker_timestamps: List of speaker events with timestamps and speakers
            recording_launch_time: ISO format timestamp when recording began

        Returns:
            List of diarized segments with speaker, text, start and end times in ISO format
        """
        import diarization

        if not speaker_timestamps:
            raise ValueError("No speaker timestamps provided")

        # Ensure recording_launch_time is in ISO format string
        if isinstance(recording_launch_time, datetime):
            recording_launch_time = recording_launch_time.isoformat()

        # Format speaker timestamps if needed
        formatted_timestamps = []
        for event in speaker_timestamps:
            # Ensure timestamp is in ISO format
            if isinstance(event['timestamp'], datetime):
                event['timestamp'] = event['timestamp'].isoformat()
            formatted_timestamps.append(event)

        # Use the diarization module to process the transcription
        diarized_segments = diarization.diarize_transcript(
            whisper_output=transcription,
            slack_data=formatted_timestamps,
            recording_start=recording_launch_time,
            speaker_offset=-2.2,
            duration_ratio=1.5
        )

        # Convert the segment times to ISO format timestamps
        base_time = datetime.fromisoformat(recording_launch_time)
        formatted_segments = []

        for segment in diarized_segments:
            start_time = base_time + timedelta(seconds=segment['start'])
            end_time = base_time + timedelta(seconds=segment['end'])

            formatted_segments.append({
                'speaker': segment['speaker'] or 'unknown',
                'text': segment['text'],
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            })

        return formatted_segments

    def generate_tldr(self, transcript_text):
        """Generate a TLDR summary for the transcript using GPT-4"""
        try:
            prompt = """Our Slack calls are recorded and transcribed for later use, but it's hard to find a needed call in our system. Our solution — provide every recording a short field called "what's this call about". The idea is to have very short (7 words per topic max) but precise overview of a call, for example "Конфигурация SSL для  проекта по записи звноков, ...", where the topics are listed with commas. Your task is to provide a "what's this call about" filed for the call below. Only return the text of the field and nothing else. Your answer must be in Russian.

Transcript:
{}""".format(transcript_text)

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=75
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating TLDR: {str(e)}")
            return None

    def transcribe_audio(self, audio_path, speaker_timestamps=None, recording_launch_time=None):
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
                logger.info(
                    f"Final transcription JSON: {json.dumps(final_json)}")
                transcript_json = final_json

            # Extract text and create diarized version if speaker timestamps provided
            transcription_text = transcript_json.get('text', '')
            diarized_segments = None
            if speaker_timestamps:
                try:
                    diarized_segments = self.diarize_transcription(
                        transcript_json, speaker_timestamps, recording_launch_time)
                except Exception as e:
                    logger.error(f"Error during diarization: {str(e)}")

            # Generate TLDR after successful transcription
            tldr = None
            if transcription_text:
                tldr = self.generate_tldr(transcription_text)

            return {
                'text': transcription_text,
                'diarized': diarized_segments,
                'tldr': tldr
            }

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return None
