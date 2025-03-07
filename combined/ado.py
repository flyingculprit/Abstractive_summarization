import os
import concurrent.futures
from flask import Blueprint, render_template, request, send_file
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import google.generativeai as genai
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# Configure Gemini API
genai.configure(api_key="your api")

# IBM Watson API Credentials
API_KEY = 'your api'
SERVICE_URL = 'your api'

# Authenticate Watson TTS
authenticator = IAMAuthenticator(API_KEY)
tts = TextToSpeechV1(authenticator=authenticator)
tts.set_service_url(SERVICE_URL)

# Flask Blueprint
ado_blueprint = Blueprint("ado", __name__, template_folder="templates")

# Upload Folder Setup
UPLOAD_FOLDER = "ado_uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to Split Audio into Chunks
def split_audio(audio_path, chunk_length_ms=3 * 60 * 1000):
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_name = os.path.join(UPLOAD_FOLDER, f"chunk_{i}.wav")
        chunk.export(chunk_name, format="wav")
        chunk_files.append(chunk_name)
    
    return chunk_files

# Function to Transcribe Audio
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
    transcription_path = os.path.join(UPLOAD_FOLDER, "transcription.txt")
    
    with open(transcription_path, "w", encoding="utf-8") as f:
        f.write(full_transcription)
    
    return full_transcription, transcription_path, chunk_files  # Return chunk_files for cleanup

# Function to Analyze with Gemini AI
def analyze_with_gemini(input_text):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Analyze the following transcript and summarize its key points:\n{input_text}")
    
    summary = response.text if hasattr(response, "text") else "No response from Gemini API."
    summary_path = os.path.join(UPLOAD_FOLDER, "summarization.txt")
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    
    return summary, summary_path

# Function to Convert Summary to Speech
def convert_text_to_speech(text):
    audio_path = os.path.join(UPLOAD_FOLDER, "output.mp3")
    with open(audio_path, "wb") as audio_file:
        audio_file.write(
            tts.synthesize(text, voice='en-US_AllisonV3Voice', accept='audio/mp3').get_result().content
        )
    return audio_path

# Function to Clean Up Chunk Files
def cleanup_files(files):
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error deleting {file}: {e}")

# Flask Route - Upload & Process Audio
@ado_blueprint.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "audio_file" not in request.files:
            return "No file uploaded"

        audio_file = request.files["audio_file"]
        if audio_file.filename == "":
            return "No selected file"

        audio_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
        audio_file.save(audio_path)

        try:
            chunk_files = split_audio(audio_path)
            transcription, transcription_path, chunk_files = transcribe_audio(chunk_files)
            summary, summary_path = analyze_with_gemini(transcription)
            audio_output_path = convert_text_to_speech(summary)

            # Cleanup chunk files after processing
            cleanup_files(chunk_files)

            return render_template("ado_index.html", transcription=transcription, summary=summary, audio_file="output.mp3")
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template("ado_index.html", transcription=None, summary=None, audio_file=None)

# Flask Route - Download Processed Files
@ado_blueprint.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)
