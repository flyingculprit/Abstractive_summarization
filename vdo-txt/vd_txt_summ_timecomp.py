import os
import concurrent.futures
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="")  # Replace with your API Key

def extract_audio(video_path, audio_output_path):
    """Extract audio from video file."""
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_output_path)
    print(f"Audio extracted: {audio_output_path}")

def split_audio(audio_path, chunk_length_ms=3 * 60 * 1000):
    """Split audio into chunks of specified duration."""
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_name = f"chunk_{i}.wav"
        chunk.export(chunk_name, format="wav")
        chunk_files.append(chunk_name)
    
    return chunk_files

def transcribe_audio(chunk_files):
    """Convert audio chunks to text using Speech Recognition."""
    recognizer = sr.Recognizer()
    full_transcription = ""

    def transcribe_chunk(chunk_file):
        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                return ""

    with concurrent.futures.ThreadPoolExecutor() as executor:
        transcription_results = list(executor.map(transcribe_chunk, chunk_files))

    full_transcription = " ".join(transcription_results)
    return full_transcription

def analyze_with_gemini(input_text):
    """Summarize text using Gemini AI."""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"Summarize the key points of the following transcript:\n{input_text}")
    return response.text if hasattr(response, "text") else "No response from Gemini API."

# Main Execution
try:
    video_path = "test1.mp4"  # Change this to your video file
    audio_path = "output_audio.mp3"

    print("Extracting audio from video...")
    extract_audio(video_path, audio_path)

    print("Splitting audio into smaller chunks...")
    chunk_files = split_audio(audio_path)

    print("Converting audio chunks to text...")
    transcription = transcribe_audio(chunk_files)

    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(transcription)
    print("Transcription saved to transcription.txt.")

    print("Analyzing the transcription using Gemini API...")
    summary = analyze_with_gemini(transcription)

    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    print("Summary saved to summary.txt.")

except Exception as e:
    print(f"An error occurred: {e}")


#3 mins 30 seconds