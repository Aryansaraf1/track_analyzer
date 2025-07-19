import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import io
import os
import re
from pdf2image import convert_from_path

# Optional: Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="OCR Feedback Extractor", layout="wide")
st.title("🧾 OCR Feedback Extractor (Image to Structured Text)")

uploaded_file = st.file_uploader("📤 Upload a scanned feedback form (Image or PDF)", type=["png", "jpg", "jpeg", "pdf"])

extracted_texts = []

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pages = convert_from_path(uploaded_file, dpi=300)
        for page in pages:
            text = pytesseract.image_to_string(page)
            extracted_texts.append(text)
    else:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
        extracted_texts.append(text)

    st.subheader("📜 Extracted Raw Text")
    for i, text in enumerate(extracted_texts):
        st.text_area(f"Page {i+1}", text, height=200, key=f"text_{i}")

    def extract_structured_data(text):
        # Try regex-based field extraction
        trainer = re.search(r"Trainer:\s*(.+)", text)
        batch = re.search(r"Batch:\s*(.+)", text)
        topic = re.search(r"Topic:\s*(.+)", text)
        feedback = re.search(r"Feedback:\s*(.+)", text)

        return {
            "Trainer": trainer.group(1) if trainer else "",
            "Batch": batch.group(1) if batch else "",
            "Topic": topic.group(1) if topic else "",
            "Feedback": feedback.group(1) if feedback else text.strip()
        }

    if st.button("📊 Extract Structured Data"):
        structured_data = [extract_structured_data(txt) for txt in extracted_texts]
        df = pd.DataFrame(structured_data)
        st.subheader("✅ Structured Feedback Data")
        st.dataframe(df)

        # Allow CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv,
            file_name="structured_feedback.csv",
            mime="text/csv"
        )
