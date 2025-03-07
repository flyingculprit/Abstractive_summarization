from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# IBM Watson API credentials
API_KEY = 'your api'
SERVICE_URL = 'url'

# Authenticate Watson TTS
authenticator = IAMAuthenticator(API_KEY)
tts = TextToSpeechV1(authenticator=authenticator)
tts.set_service_url(SERVICE_URL)

# Read the text file
with open('summarization.txt', 'r', encoding='utf-8') as file:
    text = file.read()

# Convert text to speech
with open('output.mp3', 'wb') as audio_file:
    audio_file.write(
        tts.synthesize(text, voice='en-US_AllisonV3Voice', accept='audio/mp3').get_result().content
    )

print("Conversion complete! Saved as output.mp3")
