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
        if not segments:
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
                    current_paragraph = []

        # Add the last paragraph if there's anything left
        if current_paragraph:
            formatted_text.append(' '.join(current_paragraph))

        return '\n\n'.join(formatted_text)

    def transcribe_audio(self, audio_path):
        """
        Transcribe audio file using OpenAI Whisper API and return formatted text
        """
        try:
            logger.info(f"Starting transcription for: {audio_path}")
            with open(audio_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

                formatted_text = self.format_transcript(response.model_dump())
                logger.info("Transcription completed successfully")
                return formatted_text

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return None
