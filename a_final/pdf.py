from flask import Flask, render_template, request, redirect, url_for, send_file
import fitz  # PyMuPDF
import os
import google.generativeai as genai
from fpdf import FPDF  # PDF generation

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "pdf_uploads"
app.config["SUMMARY_FOLDER"] = "pdf_summaries"

# Ensure folders exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["SUMMARY_FOLDER"], exist_ok=True)

# Configure Gemini API Key
genai.configure(api_key="your api")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text() for page in doc])
    return text.strip()

# Function to count words
def count_words(text):
    return len(text.split())

# Function to summarize text using Gemini API
def summarize_text(text):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"Summarize this document: {text}")
    return response.text.strip()

# Function to create a PDF for the summary
def create_summary_pdf(summary_text, filename):
    pdf_path = os.path.join(app.config["SUMMARY_FOLDER"], filename)
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.multi_cell(0, 10, summary_text)
    pdf.output(pdf_path)
    
    return pdf_path

# Route for the upload form
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)
        
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            filename = file.filename
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            
            extracted_text = extract_text_from_pdf(filepath)
            original_word_count = count_words(extracted_text)

            summary = summarize_text(extracted_text)
            summarized_word_count = count_words(summary)

            # Calculate summary ratio
            summary_ratio = round((summarized_word_count / original_word_count) * 100, 2) if original_word_count > 0 else 0

            # Generate a summary PDF
            summary_filename = f"summary_{filename.replace('.pdf', '')}.pdf"
            summary_pdf_path = create_summary_pdf(summary, summary_filename)

            return render_template(
                "pdf_result.html",
                original_text=extracted_text,
                original_word_count=original_word_count,
                summary=summary,
                summarized_word_count=summarized_word_count,
                summary_ratio=summary_ratio,
                summary_pdf=summary_filename
            )

    return render_template("pdf_index.html")

# Route to download summary PDF
@app.route("/download/<filename>")
def download_summary(filename):
    return send_file(os.path.join(app.config["SUMMARY_FOLDER"], filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

#backup code