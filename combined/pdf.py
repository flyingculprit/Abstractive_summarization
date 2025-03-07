from flask import Blueprint, render_template, request, send_file
import fitz  # PyMuPDF
import os
import google.generativeai as genai
from fpdf import FPDF  # PDF generation

# Create Flask Blueprint
pdf_blueprint = Blueprint('pdf', __name__, template_folder="templates")

# Configure upload and summary folders
UPLOAD_FOLDER = "pdf_uploads"
SUMMARY_FOLDER = "pdf_summaries"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

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
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Summarize this document: {text}")
    return response.text.strip()

# Function to create a PDF for the summary
def create_summary_pdf(summary_text, filename):
    pdf_path = os.path.join(SUMMARY_FOLDER, filename)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary_text)
    pdf.output(pdf_path)
    return pdf_path

@pdf_blueprint.route("/", methods=["GET", "POST"])
def upload_file():
    original_text = summary = None
    original_word_count = summarized_word_count = summary_ratio = 0
    summary_filename = None

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".pdf"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            extracted_text = extract_text_from_pdf(filepath)
            original_word_count = count_words(extracted_text)
            summary = summarize_text(extracted_text)
            summarized_word_count = count_words(summary)
            summary_ratio = round((summarized_word_count / original_word_count) * 100, 2) if original_word_count > 0 else 0

            summary_filename = f"summary_{file.filename.replace('.pdf', '')}.pdf"
            create_summary_pdf(summary, summary_filename)

            original_text = extracted_text  # Storing extracted text for rendering

    return render_template("pdf_index.html",
                           original_text=original_text,
                           original_word_count=original_word_count,
                           summary=summary,
                           summarized_word_count=summarized_word_count,
                           summary_ratio=summary_ratio,
                           summary_pdf=summary_filename)

@pdf_blueprint.route("/download/<filename>")
def download_summary(filename):
    return send_file(os.path.join(SUMMARY_FOLDER, filename), as_attachment=True)
