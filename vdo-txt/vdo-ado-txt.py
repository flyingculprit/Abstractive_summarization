from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import concurrent.futures

# Function to extract audio from a video file
def extract_audio(video_path, audio_output_path):
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_output_path)
        audio_clip.close()
        video_clip.close()
        print(f"Audio successfully extracted to: {audio_output_path}")
    except Exception as e:
        print(f"An error occurred during audio extraction: {e}")

# Function to split audio into chunks
def split_audio(audio_path, chunk_length_ms):
    try:
        audio = AudioSegment.from_file(audio_path)
        chunks = make_chunks(audio, chunk_length_ms)
        chunk_files = []
        
        for i, chunk in enumerate(chunks):
            chunk_name = f"chunk_{i}.wav"
            chunk.export(chunk_name, format="wav")
            chunk_files.append(chunk_name)
        
        print(f"Audio split into {len(chunk_files)} chunks.")
        return chunk_files
    except Exception as e:
        print(f"An error occurred during audio splitting: {e}")
        return []

# Function to transcribe audio from a chunk
def transcribe_chunk(chunk_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print(f"Transcribed {chunk_file}")
            return text
    except sr.UnknownValueError:
        print(f"Could not understand audio in {chunk_file}.")
        return ""
    except sr.RequestError as e:
        print(f"Request failed for {chunk_file}: {e}")
        return ""

# Function to transcribe audio chunks in parallel
def transcribe_audio_parallel(chunk_files):
    full_transcription = ""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Parallelize the transcription of chunks
        results = executor.map(transcribe_chunk, chunk_files)
        full_transcription = " ".join(results)
    
    return full_transcription

# Main process
def main(video_path, audio_output_path, chunk_length_ms):
    try:
        # Extract audio from video
        extract_audio(video_path, audio_output_path)

        # Split the extracted audio into smaller chunks
        chunk_files = split_audio(audio_output_path, chunk_length_ms)
        
        if not chunk_files:
            return

        # Transcribe audio chunks in parallel
        print("Converting audio chunks to text...")
        transcription = transcribe_audio_parallel(chunk_files)

        # Save the transcription to a file
        with open("transcription.txt", "w", encoding="utf-8") as f:
            f.write(transcription)
        
        print("Transcription saved to transcription.txt.")
    except Exception as e:
        print(f"An error occurred during the process: {e}")

# Paths to the video and audio output files
video_path = "test1.mp4"  # Replace with your video file path
audio_output_path = "output_audio.mp3"  # Replace with your desired audio file path

# Define the chunk length in milliseconds (e.g., 3 minutes per chunk)
chunk_length_ms = 3 * 60 * 1000

# Run the process
main(video_path, audio_output_path, chunk_length_ms)
