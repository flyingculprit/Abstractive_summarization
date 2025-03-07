import concurrent.futures
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="your api")

def split_audio(audio_path, chunk_length_ms=3 * 60 * 1000):
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_name = f"chunk_{i}.wav"
        chunk.export(chunk_name, format="wav")
        chunk_files.append(chunk_name)
    return chunk_files

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

def analyze_with_gemini(input_text):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"Analyze the following transcript and summarize its key points:\n{input_text}")
    return response.text if hasattr(response, "text") else "No response from Gemini API."

try:
    audio_path = "E:/Git/Abstractive_summarization/a_final/vdo-summ/output_audio.mp3"
    chunk_length_ms = 3 * 60 * 1000  # 3-minute chunks

    print(f"Splitting {audio_path} into smaller chunks...")
    chunk_files = split_audio(audio_path, chunk_length_ms)

    print("Converting audio chunks to text...")
    transcription = transcribe_audio(chunk_files)

    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(transcription)
    print("Transcription saved to transcription.txt.")

    print("Analyzing the transcription using Gemini API...")
    summary = analyze_with_gemini(transcription)

    with open("summarization.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    print("Summary saved to summarization.txt.")

except Exception as e:
    print(f"An error occurred: {e}")

# 2 mins 8 secs