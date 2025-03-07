import os
import concurrent.futures
from flask import Flask, render_template, request, send_file
from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="your api")

app = Flask(__name__)

UPLOAD_FOLDER = "ado_uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def split_audio(audio_path, chunk_length_ms=3 * 60 * 1000):
    audio = AudioSegment.from_file(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    chunk_files = []
    
    for i, chunk in enumerate(chunks):
        chunk_name = os.path.join(UPLOAD_FOLDER, f"chunk_{i}.wav")
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
                return recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                return ""

    with concurrent.futures.ThreadPoolExecutor() as executor:
        transcription_results = list(executor.map(transcribe_chunk, chunk_files))

    full_transcription = " ".join(transcription_results)
    
    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(full_transcription)
    
    return full_transcription

def analyze_with_gemini(input_text):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Analyze the following transcript and summarize its key points:\n{input_text}")
    
    summary = response.text if hasattr(response, "text") else "No response from Gemini API."

    with open("summarization.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    return summary

@app.route("/", methods=["GET", "POST"])
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
            transcription = transcribe_audio(chunk_files)
            summary = analyze_with_gemini(transcription)

            return render_template("ado_index.html", transcription=transcription, summary=summary)
        except Exception as e:
            return f"An error occurred: {e}"

    return render_template("ado_index.html", transcription=None, summary=None)

@app.route("/download/<filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
