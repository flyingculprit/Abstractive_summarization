from transformers import pipeline

def summarize_text(input_file, output_file):
    try:
        # Read the transcription from the file
        with open(input_file, "r", encoding="utf-8") as file:
            transcription = file.read()

        # Check if the transcription is empty
        if len(transcription.strip()) == 0:
            print("The transcription is empty.")
            return

        # Split the transcription into smaller chunks if it is too long
        chunk_size = 1000  # Number of characters per chunk
        chunks = [transcription[i:i+chunk_size] for i in range(0, len(transcription), chunk_size)]

        # Initialize the summarization pipeline
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

        summary = ""
        for chunk in chunks:
            # Summarize each chunk
            chunk_summary = summarizer(chunk, max_length=300, min_length=100, do_sample=False)
            summary += chunk_summary[0]['summary_text'] + " "

        # Write the summary to an output file
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(summary.strip())
        
        print(f"Summary saved to {output_file}.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Call the function with your transcription file and desired output summary file
input_file = "transcription.txt"  # Path to your transcription file
output_file = "summary.txt"  # Path where the summary will be saved

summarize_text(input_file, output_file)
