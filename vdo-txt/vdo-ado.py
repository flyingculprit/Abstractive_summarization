from moviepy.editor import VideoFileClip

# Function to extract audio from a video file
def extract_audio(video_path, audio_output_path):
    try:
        # Load the video file
        video_clip = VideoFileClip(video_path)
        
        # Extract the audio
        audio_clip = video_clip.audio
        
        # Write the audio to the output file
        audio_clip.write_audiofile(audio_output_path)
        
        # Close the audio and video clips
        audio_clip.close()
        video_clip.close()
        
        print(f"Audio successfully extracted to: {audio_output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Input video file path
video_path = "test1.mp4"  # Replace with your video file path

# Output audio file path
audio_output_path = "output_audio.mp3"  # Replace with your desired audio file path

# Call the function
extract_audio(video_path, audio_output_path)
