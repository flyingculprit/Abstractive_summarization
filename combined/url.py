from flask import Blueprint, render_template, request, send_file
from newspaper import Article
import google.generativeai as genai
from fpdf import FPDF
from docx import Document
import os

# Configure Gemini API (Replace with your API Key)
genai.configure(api_key="your api")

# Define Blueprint
url_blueprint = Blueprint("url", __name__, template_folder="templates")

def extract_text(url):
    """Extracts text from the given URL."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def summarize_text(text):
    """Summarizes the given text using Gemini API."""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Summarize this article:\n{text}")
        return response.text if response else "Error in summarization"
    except Exception as e:
        return f"Error in summarization: {str(e)}"

def save_as_pdf(text, filename):
    """Saves the given text as a PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(190, 10, text)
    pdf.output(filename)
    return filename

def save_as_word(text, filename):
    """Saves the given text as a Word document."""
    doc = Document()
    doc.add_paragraph(text)
    doc.save(filename)
    return filename

@url_blueprint.route("/", methods=["GET", "POST"])
def index():
    """Handles text extraction and summarization."""
    extracted_text = None
    word_count = 0
    char_count = 0
    summary = None
    compression_ratio = None
    url = None

    if request.method == "POST":
        url = request.form.get("url")
        if url:
            extracted_text = extract_text(url)
            if "Error" not in extracted_text:
                word_count = len(extracted_text.split())
                char_count = len(extracted_text)
            
            if "summarize" in request.form:
                summary = summarize_text(extracted_text)
                if "Error" not in summary:
                    summary_word_count = len(summary.split())
                    compression_ratio = round((summary_word_count / word_count) * 100, 2) if word_count else 0

    return render_template(
        "url_index.html",
        url=url,
        extracted_text=extracted_text,
        word_count=word_count,
        char_count=char_count,
        summary=summary,
        compression_ratio=compression_ratio
    )

@url_blueprint.route("/download/<format>/<type>")
def download(format, type):
    """Handles file download for PDF or Word."""
    text = request.args.get("text", "")
    filename = f"download.{format}"

    if format == "pdf":
        file_path = save_as_pdf(text, filename)
    elif format == "docx":
        file_path = save_as_word(text, filename)
    else:
        return "Invalid format", 400

    return send_file(file_path, as_attachment=True)
