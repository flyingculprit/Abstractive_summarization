import concurrent.futures
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
from transformers import pipeline

# Load summarization model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

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
def summarize_text(input_text):
    # Split text into chunks to handle large text
    chunk_size = 1000  # Number of characters per chunk
    chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]

    # Use concurrent futures to process the chunks in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        summaries = list(executor.map(summarizer, chunks))
    
    # Combine all summaries into one
    full_summary = " ".join([summary[0]['summary_text'] for summary in summaries])

    return full_summary

# Main process
try:
    audio_path = "output_audio.mp3"
    chunk_length_ms = 3 * 60 * 1000  # 3-minute chunks

    print(f"Splitting {audio_path} into smaller chunks...")
    chunk_files = split_audio(audio_path, chunk_length_ms)

    print("Converting audio chunks to text...")
    transcription = transcribe_audio(chunk_files)

    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(transcription)
    print("Transcription saved to transcription.txt.")

    print("Summarizing the transcription...")
    summary = summarize_text(transcription)

    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    print("Summary saved to summary.txt.")

except Exception as e:
    print(f"An error occurred: {e}")
