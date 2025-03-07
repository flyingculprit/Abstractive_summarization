import concurrent.futures
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import google.generativeai as genai
from moviepy.editor import VideoFileClip

# Configure Gemini API
genai.configure(api_key="your gemini api")

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
    video_path = "test1.mp4"
    audio_output_path = "output_audio.mp3"
    
    # Step 1: Extract audio from video
    print(f"Extracting audio from video: {video_path}")
    extract_audio(video_path, audio_output_path)

    # Step 2: Split the audio into smaller chunks
    chunk_length_ms = 3 * 60 * 1000  # 3-minute chunks
    print(f"Splitting {audio_output_path} into smaller chunks...")
    chunk_files = split_audio(audio_output_path, chunk_length_ms)

    # Step 3: Convert audio chunks to text
    print("Converting audio chunks to text...")
    transcription = transcribe_audio(chunk_files)

    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(transcription)
    print("Transcription saved to transcription.txt.")

    # Step 4: Analyze and summarize the transcription using Gemini API
    print("Analyzing the transcription using AI...")
    summary = analyze_with_gemini(transcription)

    with open("summarization.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    print("Summary saved to summarization.txt.")

except Exception as e:
    print(f"An error occurred: {e}")