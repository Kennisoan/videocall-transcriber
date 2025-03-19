import os
import json
import openai
from typing import List, Dict, Any, Optional

# Maximum token limit for OpenAI model context window
MAX_TOKENS = 16000  # Conservative estimate for gpt-4o context window
TOKENS_PER_CHAR = 0.4  # Rough estimate for Russian language tokens per character


def generate_tldr(transcript_data: Dict[str, Any]) -> str:
    """
    Generate a TLDR summary of a meeting transcript in Russian.

    Args:
        transcript_data: Dictionary containing the transcript data with "diarized" field

    Returns:
        str: A 1-2 sentence TLDR summary in Russian
    """
    # Set API key and base URL if provided, otherwise use environment variables
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Extract diarized transcript
    diarized_transcript = transcript_data.get("diarized", [])

    if not diarized_transcript:
        return "Недостаточно информации для создания TL;DR."

    # Process transcript in chunks if needed
    tldr = process_transcript_chunks(diarized_transcript)

    # Remove any wrapping quotes if present
    tldr = tldr.strip()
    if tldr.startswith('"') and tldr.endswith('"'):
        tldr = tldr[1:-1].strip()

    return tldr


def process_transcript_chunks(diarized_transcript: List[Dict[str, Any]]) -> str:
    """
    Process transcript in chunks if it exceeds the context window.

    Args:
        diarized_transcript: List of utterances with speaker and text

    Returns:
        str: A TLDR summary in Russian
    """
    # Convert transcript to a simple format for processing
    formatted_text = format_transcript_for_summary(diarized_transcript)

    # If transcript is short enough, process it directly
    if len(formatted_text) * TOKENS_PER_CHAR < MAX_TOKENS * 0.7:  # Leave room for prompt and response
        return generate_summary_from_text(formatted_text)

    # Otherwise, split into chunks and process each chunk
    chunks = split_into_chunks(formatted_text)
    chunk_summaries = []

    for chunk in chunks:
        chunk_summary = generate_summary_from_text(chunk, is_chunk=True)
        chunk_summaries.append(chunk_summary)

    # Combine chunk summaries into a final summary
    combined_summary_text = "\n\n".join(chunk_summaries)
    return generate_final_summary(combined_summary_text)


def format_transcript_for_summary(diarized_transcript: List[Dict[str, Any]]) -> str:
    """
    Format the transcript into a simple text string for summarization.

    Args:
        diarized_transcript: List of utterances with speaker and text

    Returns:
        str: Formatted transcript text
    """
    formatted_lines = []

    for utterance in diarized_transcript:
        speaker = utterance.get("speaker", "Unknown")
        text = utterance.get("text", "")

        if text.strip():
            formatted_lines.append(f"{speaker}: {text}")

    return "\n".join(formatted_lines)


def split_into_chunks(text: str) -> List[str]:
    """
    Split the transcript text into chunks that fit within model context limits.

    Args:
        text: Full transcript text

    Returns:
        List[str]: List of text chunks
    """
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0

    # Target tokens per chunk (conservative to leave room for prompt and response)
    target_length = int(MAX_TOKENS * 0.7 / TOKENS_PER_CHAR)

    for line in lines:
        line_length = len(line)

        # If adding this line would exceed the target length, finish the current chunk
        if current_length + line_length > target_length and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    # Add the last chunk if not empty
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def generate_summary_from_text(text: str, is_chunk: bool = False) -> str:
    """
    Generate a summary from the formatted transcript text using OpenAI API.

    Args:
        text: Formatted transcript text
        is_chunk: Whether this is a chunk of a larger transcript

    Returns:
        str: Generated summary
    """
    if is_chunk:
        prompt = f"""Вот часть стенограммы совещания. Создайте краткое промежуточное резюме основных обсуждаемых тем:

{text}

Промежуточное резюме (на русском языке):"""
    else:
        prompt = f"""Прочтите следующую стенограмму совещания и создайте TLDR (краткое резюме) на русском языке в 1-2 предложениях, 
которые охватывают основные обсуждаемые темы. Перечислите ключевые темы через запятую.
Резюме должно быть похоже на этот пример по стилю: "Интеграция пип-порта, проблемы с редиректом, работа с QR-кодом, обсуждение работы мерчантов, настройка платежной страницы."
Не используйте кавычки в начале и конце резюме.

Стенограмма:
{text}

TLDR (на русском языке):"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Вы - помощник, который создает краткие и точные резюме деловых совещаний на русском языке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return "Ошибка при создании TL;DR."


def generate_final_summary(chunk_summaries_text: str) -> str:
    """
    Generate a final summary from multiple chunk summaries.

    Args:
        chunk_summaries_text: Combined text from all chunk summaries

    Returns:
        str: Final TLDR summary
    """
    prompt = f"""На основе следующих промежуточных резюме различных частей длинного совещания, 
создайте окончательное TLDR (краткое резюме) на русском языке в 1-2 предложениях, 
которые охватывают основные обсуждаемые темы. Перечислите ключевые темы через запятую.
Резюме должно быть похоже на этот пример по стилю: "Интеграция пип-порта, проблемы с редиректом, работа с QR-кодом, обсуждение работы мерчантов, настройка платежной страницы."
Не используйте кавычки в начале и конце резюме.

Промежуточные резюме:
{chunk_summaries_text}

Финальное TLDR (на русском языке):"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Вы - помощник, который создает краткие и точные резюме деловых совещаний на русском языке."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"Error generating final summary: {str(e)}")
        return "Ошибка при создании итогового TL;DR."
