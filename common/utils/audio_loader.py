import logging
import math
import tempfile
from io import BytesIO

import ffmpeg
import openai
from pydub import AudioSegment
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)

WHISPER_MODEL = 'whisper-1'


def split_audio_by_size(data, file_name, format, chunk_size_mb=20):
    file_p = BytesIO(data)
    audio = AudioSegment.from_file(file_p, format)
    chunk_size_bytes = chunk_size_mb * 1024 * 1024
    num_chunks = math.ceil(len(audio) / chunk_size_bytes)
    output_chunks = []
    for i in range(num_chunks):
        output_stream = BytesIO()
        chunk_start = i * chunk_size_bytes
        chunk_end = min((i + 1) * chunk_size_bytes, len(audio))
        chunk = audio[chunk_start:chunk_end]
        output_chunks.append(chunk.export(output_stream, format=format))
    return output_chunks


def partition_audio(data, mime_type, openai_key, file_name='audio_file.mp3'):
    """
    Extract text from audio data
    """
    if openai_key is None:
        raise Exception(
            'OpenAI API key is missing, it is required for audio partitioning.',
        )

    openai.api_key = openai_key
    extension = 'mp3'
    if mime_type.endswith('mp3'):
        extension = 'mp3'
    elif mime_type.endswith('mpeg'):
        extension = 'mp3'
    elif mime_type.endswith('mp4'):
        extension = 'mp4'
    elif mime_type.endswith('webm'):
        extension = 'webm'

    # Whisper only accpets max 25 MBs of audio file break a file into chunks
    file_chunks = split_audio_by_size(data, file_name, extension, 20)
    result = []
    for chunk in file_chunks:
        file_p = chunk
        file_p.name = file_name
        response = openai.Audio.transcribe(
            model=WHISPER_MODEL, file=file_p,
        )
        result.append(response.text)
    return result


def extract_audio_from_video(video_data: bytes, video_format: str, audio_format: str = 'mp3') -> bytes:
    with tempfile.TemporaryDirectory() as dir:
        with tempfile.NamedTemporaryFile(suffix=f'.{video_format}', dir=dir) as video_temp_file:

            # Write video data to temp file
            video_temp_file.write(video_data)
            video_temp_file.flush()

            # Extract audio using FFmpeg
            stream = ffmpeg.input(video_temp_file.name)

            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', dir=dir, delete=True) as audio_temp_file:
                stream = ffmpeg.output(
                    stream, audio_temp_file.name, format=audio_format,
                ).overwrite_output()
                ffmpeg.run(stream)
                # Read audio data from temp file
                audio_data = audio_temp_file.read()

    return audio_data


def partition_video(data, mime_type, openai_key, file_name='video_file'):
    extension = 'mp4'
    if mime_type.endswith('mp4'):
        extension = 'mp4'
    elif mime_type.endswith('webm'):
        extension = 'webm'
    else:
        raise Exception('Unsupported video format')

    # Extract audio from video
    audio_data = extract_audio_from_video(data, extension)
    return partition_audio(audio_data, 'audio/mp3', openai_key, 'audio_file.mp3')


def partition_youtube_audio(url, openai_key):
    # Create a temp directory to store the audio file
    with tempfile.TemporaryDirectory() as dir:
        ydl_opts = {
            'format': 'bestaudio/best',
            'paths': {'temp': dir, 'home': dir},
            'noplaylist': True,
            'quiet': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict['title']
            description = info_dict['description']
            audio_file_name = ydl.prepare_filename(info_dict)
            mime_type = info_dict['ext']

        with open(audio_file_name, 'rb') as audio_file:
            audio_data = audio_file.read()

        result = partition_audio(
            audio_data, file_name=audio_file_name, mime_type=mime_type, openai_key=openai_key,
        )
        return [f'Description : {description}', f'Title : {title}'] + result
