import os
import logging
import openai

logger = logging.getLogger(__name__)


class TranscriptionManager:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai.base_url = os.getenv(
            'OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.client = openai.Client()

    def format_transcript(self, response_data):
        """
        Format the transcript into paragraphs based on timing gaps and sentence endings
        """
        segments = response_data.get('segments', [])
        logger.info(f"Received {len(segments)} segments from Whisper API")

        if not segments:
            logger.warning("No segments found in response data")
            return response_data.get('text', '')

        MIN_PAUSE_FOR_BREAK = 0.5

        formatted_text = []
        current_paragraph = []

        for i, segment in enumerate(segments):
            current_text = segment['text'].strip()

            if not current_text:
                continue

            current_paragraph.append(current_text)

            # Check if we should create a paragraph break
            if i < len(segments) - 1:
                current_end = segment['end']
                next_start = segments[i + 1]['start']
                time_gap = next_start - current_end

                last_char = current_text[-1] if current_text else ''

                if time_gap >= MIN_PAUSE_FOR_BREAK and last_char in '.!?':
                    formatted_text.append(' '.join(current_paragraph))
                    logger.debug(
                        f"Created paragraph break after: {' '.join(current_paragraph)}")
                    current_paragraph = []

        # Add the last paragraph if there's anything left
        if current_paragraph:
            formatted_text.append(' '.join(current_paragraph))

        final_text = '\n\n'.join(formatted_text)
        logger.info(
            f"Formatted transcript into {len(formatted_text)} paragraphs")
        logger.debug(f"Final formatted text:\n{final_text}")
        return final_text

    def transcribe_audio(self, audio_path):
        """
        Transcribe audio file using OpenAI Whisper API and return formatted text.
        For audio files that exceed the maximum size limit, the method splits the file into smaller chunks.
        """
        try:
            logger.info(f"Starting transcription for: {audio_path}")
            file_size = os.path.getsize(audio_path)
            MAX_SIZE = 26214400  # Maximum allowed file size in bytes

            if file_size <= MAX_SIZE:
                with open(audio_path, 'rb') as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                    logger.debug(f"Raw API response: {response.model_dump()}")
                    formatted_text = self.format_transcript(
                        response.model_dump())
                    logger.info("Transcription completed successfully")
                    return formatted_text
            else:
                # If file is too large, split it into smaller chunks for transcription
                from pydub import AudioSegment
                from io import BytesIO

                audio = AudioSegment.from_file(audio_path)
                duration_ms = len(audio)  # Total duration in milliseconds

                # Calculate allowed duration per chunk (in ms) based on average bytes per ms
                allowed_duration_ms = int(duration_ms * MAX_SIZE / file_size)
                if allowed_duration_ms <= 0:
                    allowed_duration_ms = 10000

                num_chunks = (duration_ms // allowed_duration_ms) + \
                    (1 if duration_ms % allowed_duration_ms > 0 else 0)
                logger.info(
                    f"File size ({file_size} bytes) exceeds limit, splitting into {num_chunks} chunks for transcription")

                transcripts = []
                for i in range(num_chunks):
                    start_ms = i * allowed_duration_ms
                    end_ms = min((i + 1) * allowed_duration_ms, duration_ms)
                    chunk_audio = audio[start_ms:end_ms]

                    chunk_io = BytesIO()
                    # Export chunk to BytesIO using mp3 format
                    chunk_audio.export(chunk_io, format="mp3")
                    chunk_io.seek(0)
                    # Add a name attribute for OpenAI API to detect file type
                    chunk_io.name = f"chunk_{i}.mp3"

                    logger.info(
                        f"Transcribing chunk {i + 1}/{num_chunks} from {start_ms}ms to {end_ms}ms")
                    chunk_response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=chunk_io,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                    transcript_chunk = self.format_transcript(
                        chunk_response.model_dump())
                    transcripts.append(transcript_chunk)

                full_transcript = " ".join(transcripts)
                logger.info(
                    "Transcription of all chunks completed successfully")
                return full_transcript

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return None
