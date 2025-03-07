from pydub import AudioSegment
from pydub.utils import make_chunks
import speech_recognition as sr

def split_audio(audio_path, chunk_length_ms):
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

    for chunk_file in chunk_files:
        print(f"Processing {chunk_file}...")
        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                full_transcription += text + " "
            except sr.UnknownValueError:
                print(f"Could not understand audio in {chunk_file}.")
            except sr.RequestError as e:
                print(f"Request failed for {chunk_file}: {e}")
    
    return full_transcription

# Main process
try:
    # Path to your audio file
    audio_path = "output_audio.mp3"
    chunk_length_ms = 3 * 60 * 1000  # 5-minute chunks

    print(f"Splitting {audio_path} into smaller chunks...")
    chunk_files = split_audio(audio_path, chunk_length_ms)

    print("Converting audio chunks to text...")
    transcription = transcribe_audio(chunk_files)

    # Save the transcription to a file
    with open("transcription.txt", "w", encoding="utf-8") as f:
        f.write(transcription)
    print("Transcription saved to transcription.txt.")
    
except Exception as e:
    print(f"An error occurred: {e}")
