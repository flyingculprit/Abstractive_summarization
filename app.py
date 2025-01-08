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

# Initialize the summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Set page layout
st.set_page_config(layout="wide", page_title="Enhanced Article Summarizer")

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

# Main application
def main():
    st.title("Enhanced Article Extractor and Summarizer")
    st.markdown("A tool to extract and summarize online articles with an **abstractive summarization model**.")

    url = st.text_input("Enter the URL of an article:", key="url")
    max_chunk = 300  # Max tokens for each chunk of text

    if url:
        try:
            # Fetch and process the article
            response = requests.get(url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all(['h1', 'p'])
            text = [html.unescape(result.get_text()) for result in results]
            article = ' '.join(text)

            # Display the extracted article
            st.subheader("Extracted Article Content")
            st.text_area("Article", article, height=300)
            st.markdown(f"**Article Length:** {len(article)} characters")

            # Break article into chunks
            article = article.replace('.', '.<eos>').replace('?', '?<eos>').replace('!', '!<eos>')
            sentences = article.split('<eos>')
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

            # Summarize each chunk
            progress_bar = st.progress(0)
            status_text = st.empty()
            summaries = []
            start_time = time.time()

            for i, chunk in enumerate(chunks):
                summary = summarizer(chunk, max_length=120, min_length=30, do_sample=False)
                summaries.append(summary[0]['summary_text'])

                percent_complete = (i + 1) / len(chunks)
                elapsed_time = time.time() - start_time
                estimated_total_time = elapsed_time / percent_complete
                estimated_time_remaining = estimated_total_time - elapsed_time

                progress_bar.progress(percent_complete)
                status_text.markdown(f"**Progress:** {percent_complete * 100:.2f}% - "
                                     f"**Estimated time remaining:** {estimated_time_remaining:.2f} seconds")

            summary_text = ' '.join(summaries)

            # Display the summary
            st.subheader("Summarized Article Content")
            st.text_area("Summary", summary_text, height=300)
            st.markdown(f"**Summary Length:** {len(summary_text)} characters")

            # Compression ratio
            original_length = len(article.split())
            summary_length = len(summary_text.split())
            compression_ratio = (summary_length / original_length) * 100
            st.markdown(f"### Compression Ratio: {round(compression_ratio)}%")

            # Generate PDF
            pdf_buffer = create_pdf(summary_text)
            st.download_button(
                label="Download Summary as PDF",
                data=pdf_buffer,
                file_name="summarized_article.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == '__main__':
    main()
