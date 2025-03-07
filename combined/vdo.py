import os
import concurrent.futures
from flask import Blueprint, render_template, request, send_file
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import google.generativeai as genai
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# Configure Gemini API
genai.configure(api_key="your api")

# IBM Watson API credentials
API_KEY = "your api"
SERVICE_URL = "your api"

# Authenticate Watson TTS
authenticator = IAMAuthenticator(API_KEY)
tts = TextToSpeechV1(authenticator=authenticator)
tts.set_service_url(SERVICE_URL)

# Flask Blueprint
vdo_blueprint = Blueprint("vdo", __name__, template_folder="templates")

# Define Upload & Processed Folders
UPLOAD_FOLDER = "vdo_uploads"
PROCESSED_FOLDER = "vdo_processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Extract audio from video
def extract_audio(video_path, audio_output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(audio_output_path, codec="mp3")
    audio_clip.close()
    video_clip.close()

# Split audio into smaller chunks
def split_audio(audio_path, chunk_length_ms=180000):  # 3 minutes per chunk
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_name = os.path.join(PROCESSED_FOLDER, f"chunk_{i}.wav")
        chunk.export(chunk_name, format="wav")
        chunk_files.append(chunk_name)
    
    return chunk_files

# Transcribe audio using Google Speech Recognition
def transcribe_audio(chunk_files):
    recognizer = sr.Recognizer()
    
    def transcribe_chunk(chunk_file):
        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)
            try:
                return recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                return ""

    with concurrent.futures.ThreadPoolExecutor() as executor:
        transcription_results = list(executor.map(transcribe_chunk, chunk_files))

    full_transcription = " ".join(transcription_results)
    
    with open(os.path.join(PROCESSED_FOLDER, "transcription.txt"), "w", encoding="utf-8") as f:
        f.write(full_transcription)
    
    return full_transcription

# Summarization using Gemini AI
def analyze_with_gemini(input_text):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Summarize the following transcript:\n{input_text}")
    
    summary = response.text if hasattr(response, "text") else "No response from Gemini API."

    summary_file = os.path.join(PROCESSED_FOLDER, "summary.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)

    return summary, summary_file

# Convert text to speech using IBM Watson
def text_to_speech(text):
    audio_file_path = os.path.join(PROCESSED_FOLDER, "summary_audio.mp3")

    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(
            tts.synthesize(text, voice="en-US_AllisonV3Voice", accept="audio/mp3").get_result().content
        )

    return audio_file_path

# Cleanup function to delete temporary files
def cleanup_files(files):
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error deleting {file}: {e}")

# Flask Route - Upload & Process Video
@vdo_blueprint.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "video_file" not in request.files:
            return "No file uploaded"

        video_file = request.files["video_file"]
        if video_file.filename == "":
            return "No selected file"

        video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
        video_file.save(video_path)

        try:
            # Extract and process audio
            audio_output_path = os.path.join(PROCESSED_FOLDER, "output_audio.mp3")
            extract_audio(video_path, audio_output_path)
            
            chunk_files = split_audio(audio_output_path)
            transcription = transcribe_audio(chunk_files)
            summary, summary_file = analyze_with_gemini(transcription)

            # Convert summary to speech
            audio_summary_file = text_to_speech(summary)

            # Cleanup chunk files & extracted audio after processing
            cleanup_files(chunk_files + [audio_output_path])

            return render_template("vdo_index.html", transcription=transcription, summary=summary, audio_file="summary_audio.mp3")
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template("vdo_index.html", transcription=None, summary=None, audio_file=None)

# Flask Route - Download Processed Files
@vdo_blueprint.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(PROCESSED_FOLDER, filename), as_attachment=True)
