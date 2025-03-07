from pydub import AudioSegment
import speech_recognition as sr

# Function to convert MP3 to WAV
def convert_mp3_to_wav(mp3_path, wav_path):
    try:
        print(f"Converting {mp3_path} to {wav_path}...")
        # Load the MP3 file
        audio = AudioSegment.from_file(mp3_path, format="mp3")
        
        # Export to WAV format
        audio.export(wav_path, format="wav")
        print("Conversion successful!")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")

# Function to convert audio to text
def audio_to_text(audio_file_path):
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    try:
        # Load the audio file
        with sr.AudioFile(audio_file_path) as source:
            print("Converting audio to text...")
            audio_data = recognizer.record(source)  # Read the audio file
            
            # Recognize and convert audio to text
            text = recognizer.recognize_google(audio_data)
            print("Conversion successful!")
            return text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Input and output file paths
mp3_path = "output_audio.mp3"  # Replace with your MP3 file path
wav_path = "output_audio.wav"  # Desired WAV file path

# Step 1: Convert MP3 to WAV
convert_mp3_to_wav(mp3_path, wav_path)

# Step 2: Convert WAV to Text
transcribed_text = audio_to_text(wav_path)
if transcribed_text:
    print(f"Transcribed Text:\n{transcribed_text}")
