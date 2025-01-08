from transformers import pipeline
import streamlit as st
import requests
from bs4 import BeautifulSoup
import html
import time
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.enums import TA_JUSTIFY
import PyPDF2
from docx import Document

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Set page layout
st.set_page_config(layout="wide", page_title="Enhanced Summarizer")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from Word document
def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Function to create PDF with justified text
def create_pdf(text):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    justified_style = ParagraphStyle(
        name="JustifiedStyle",
        parent=styles["BodyText"],
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=15
    )
    paragraph = Paragraph(text, justified_style)
    doc.build([paragraph])
    pdf_buffer.seek(0)
    return pdf_buffer

# Function to summarize chunks of text
def summarize_text(text, max_chunk=300):
    text = text.replace('.', '.<eos>').replace('?', '?<eos>').replace('!', '!<eos>')
    sentences = text.split('<eos>')
    current_chunk = 0
    chunks = [[]]

    for sentence in sentences:
        if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
            chunks[current_chunk].extend(sentence.split(' '))
        else:
            current_chunk += 1
            chunks.append(sentence.split(' '))

    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = ' '.join(chunks[chunk_id])

    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=120, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    return ' '.join(summaries)

# Main application
def main():
    st.title("Enhanced Summarizer")
    st.markdown("Summarize online articles, PDFs, and Word documents using AI.")

    # Sidebar for input selection
    st.sidebar.header("Input Type")
    input_type = st.sidebar.radio("Select the input type:", ["Online Article", "PDF", "Word Document"])

    text = ""

    if input_type == "Online Article":
        url = st.text_input("Enter the URL of an article:")
        if url:
            try:
                response = requests.get(url)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all(['h1', 'p'])
                text = ' '.join([html.unescape(result.get_text()) for result in results])
                st.text_area("Extracted Article", text, height=300)
            except Exception as e:
                st.error(f"Error fetching article: {e}")

    elif input_type == "PDF":
        pdf_file = st.file_uploader("Upload a PDF file:", type=["pdf"])
        if pdf_file:
            try:
                text = extract_text_from_pdf(pdf_file)
                st.text_area("Extracted PDF Content", text, height=300)
            except Exception as e:
                st.error(f"Error reading PDF: {e}")

    elif input_type == "Word Document":
        docx_file = st.file_uploader("Upload a Word document:", type=["docx"])
        if docx_file:
            try:
                text = extract_text_from_docx(docx_file)
                st.text_area("Extracted Word Document Content", text, height=300)
            except Exception as e:
                st.error(f"Error reading Word document: {e}")

    # Summarization
    if text:
        st.markdown(f"**Text Length:** {len(text.split())} words")
        if st.button("Summarize"):
            with st.spinner("Summarizing..."):
                summary = summarize_text(text)
                st.subheader("Summary")
                st.text_area("Summarized Text", summary, height=300)
                st.markdown(f"**Summary Length:** {len(summary.split())} words")

                # Compression ratio
                compression_ratio = (len(summary.split()) / len(text.split())) * 100
                st.markdown(f"### Compression Ratio: {round(compression_ratio)}%")

                # Generate PDF
                pdf_buffer = create_pdf(summary)
                st.download_button(
                    label="Download Summary as PDF",
                    data=pdf_buffer,
                    file_name="summarized_text.pdf",
                    mime="application/pdf"
                )

if __name__ == '__main__':
    main()
