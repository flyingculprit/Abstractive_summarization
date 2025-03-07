import os
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
from transformers import pipeline
import concurrent.futures

# Function to extract audio from the video
def extract_audio(video_path, audio_output_path):
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_output_path)
        audio_clip.close()
        video_clip.close()
        print(f"Audio successfully extracted to: {audio_output_path}")
    except Exception as e:
        print(f"An error occurred while extracting audio: {e}")

# Function to split audio into smaller chunks
def split_audio(audio_path, chunk_length_ms=3 * 60 * 1000):
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_name = f"chunk_{i}.wav"
        chunk.export(chunk_name, format="wav")
        chunk_files.append(chunk_name)
    return chunk_files

# Function to transcribe audio chunks into text using parallel processing
def transcribe_audio(chunk_files):
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

# Function to summarize text using distillBART model
def summarize_text(input_text, output_file):
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    
    # Split text into chunks to handle large text
    chunk_size = 1000  # Number of characters per chunk
    chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]

    # Use concurrent futures to process the chunks in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        summaries = list(executor.map(summarizer, chunks))
    
    # Combine all summaries into one
    full_summary = " ".join([summary[0]['summary_text'] for summary in summaries])

    # Save the summary to a file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(full_summary.strip())
    print(f"Summary saved to {output_file}")

# Main process function
def process_video(video_path):
    try:
        # Step 1: Extract audio from video
        audio_output_path = "output_audio.mp3"
        extract_audio(video_path, audio_output_path)

        # Step 2: Split audio into smaller chunks
        chunk_files = split_audio(audio_output_path)

        # Step 3: Transcribe audio chunks into text
        print("Transcribing audio to text...")
        transcription = transcribe_audio(chunk_files)

        # Save the transcription to a file
        with open("transcription.txt", "w", encoding="utf-8") as file:
            file.write(transcription.strip())
        print("Transcription saved to transcription.txt.")

        # Step 4: Summarize the transcription
        print("Summarizing the transcription...")
        summarize_text(transcription, "summarize.txt")

    except Exception as e:
        print(f"An error occurred during the process: {e}")

# Provide the video path here
video_path = "/test1.mp4"  # Replace with your video file path

# Run the entire process
process_video(video_path)
