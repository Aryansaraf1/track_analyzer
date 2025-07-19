import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import os
import re
from pdf2image import convert_from_path

# Set path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="OCR Feedback Extractor", layout="wide")
st.title("🧾 OCR Feedback Extractor (Image to Structured Text)")

uploaded_file = st.file_uploader("📤 Upload a scanned feedback form (Image or PDF)", type=["png", "jpg", "jpeg", "pdf"])

editable_texts = []

if uploaded_file:
    extracted_texts = []

    # PDF or Image
    if uploaded_file.type == "application/pdf":
        pages = convert_from_path(uploaded_file, dpi=300)
        for page in pages:
            text = pytesseract.image_to_string(page)
            extracted_texts.append(text)
    else:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
        extracted_texts.append(text)

    st.subheader("📜 Extracted Raw Text (Editable)")
    for i, raw_text in enumerate(extracted_texts):
        edited_text = st.text_area(f"✏️ Page {i+1} - Review & Edit", value=raw_text, height=200, key=f"edit_text_{i}")
        editable_texts.append(edited_text)

    # Extraction logic
    def extract_structured_data(text):
        name = re.search(r"name[:\-]?\s*(.+)", text, re.IGNORECASE)
        Date = re.search(r"Date[:\-]?\s*(.+)", text, re.IGNORECASE)
        topic = re.search(r"Topic[:\-]?\s*(.+)", text, re.IGNORECASE)
        feedback = re.search(r"Feedback[:\-]?\s*(.+)", text, re.IGNORECASE)

        return {
            "name": name.group(1).strip() if name else "",
            "Date": Date.group(1).strip() if Date else "",
            "Topic": topic.group(1).strip() if topic else "",
            "Feedback": feedback.group(1).strip() if feedback else text.strip()
        }

    if st.button("📊 Extract Structured Data"):
        structured_data = [extract_structured_data(txt) for txt in editable_texts]
        df = pd.DataFrame(structured_data)
        st.subheader("✅ Structured Feedback Table")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, file_name="structured_feedback.csv", mime="text/csv")
