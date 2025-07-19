import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import os
import re
from pdf2image import convert_from_path

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="OCR Feedback Extractor", layout="wide")
st.title("🧾 OCR Feedback Extractor (Image to Structured Text)")

CSV_FILE = "structured_feedback.csv"

# Load existing data if file exists
if os.path.exists(CSV_FILE):
    cumulative_df = pd.read_csv(CSV_FILE)
else:
    cumulative_df = pd.DataFrame(columns=["Name", "Date", "Topic", "Feedback"])

# Upload section
uploaded_file = st.file_uploader("📤 Upload a scanned feedback form (Image or PDF)", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    # Extract text
    if uploaded_file.type == "application/pdf":
        pages = convert_from_path(uploaded_file, dpi=300)
        image = pages[0]
    else:
        image = Image.open(uploaded_file)

    raw_text = pytesseract.image_to_string(image)

    st.subheader("✏️ Edit Extracted Text Before Structuring")
    editable_text = st.text_area("Extracted Text", value=raw_text, height=200)

    # Extract data from text
    def extract_structured_data(text):
        name = re.search(r"name[:\-]?\s*(.+)", text, re.IGNORECASE)
        date = re.search(r"date[:\-]?\s*(.+)", text, re.IGNORECASE)
        topic = re.search(r"topic[:\-]?\s*(.+)", text, re.IGNORECASE)
        feedback = re.search(r"feedback[:\-]?\s*(.+)", text, re.IGNORECASE)

        return {
            "Name": name.group(1).strip() if name else "",
            "Date": date.group(1).strip() if date else "",
            "Topic": topic.group(1).strip() if topic else "",
            "Feedback": feedback.group(1).strip() if feedback else text.strip()
        }

    if st.button("📥 Save Entry to CSV"):
        new_data = extract_structured_data(editable_text)
        cumulative_df = cumulative_df._append(new_data, ignore_index=True)
        cumulative_df.to_csv(CSV_FILE, index=False)
        st.success("✅ Feedback saved successfully!")

# Display current entries
st.subheader("📊 Current Structured Feedback Data")
st.dataframe(cumulative_df)

# Download full CSV anytime
csv_data = cumulative_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Full CSV", data=csv_data, file_name="structured_feedback.csv", mime="text/csv")
