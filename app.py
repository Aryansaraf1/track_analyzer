import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import pdfkit
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import nltk
nltk.download('vader_lexicon')

sid = SentimentIntensityAnalyzer()

st.set_page_config(page_title="Training Feedback Analyzer", layout="wide")
st.title("📊 Training Feedback Analyzer")

uploaded_file = st.file_uploader("Upload Feedback CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Classify Feedback
    def classify_feedback(text):
        if not isinstance(text, str):
            return "Suggestion"
        score = sid.polarity_scores(text)["compound"]
        if score >= 0.3:
            return "Compliment"
        elif score <= -0.2:
            return "Complaint"
        else:
            return "Suggestion"

    df["Sentiment Score"] = df["Feedback"].apply(lambda x: sid.polarity_scores(str(x))["compound"])
    df["Category"] = df["Feedback"].apply(classify_feedback)

    st.subheader("🔍 Preview of Classified Feedback")
    st.dataframe(df[["Trainer", "Batch", "Topic", "Feedback", "Sentiment Score", "Category"]])

    # Category Heatmap (on-screen)
    categories = df["Category"].unique().tolist()
    selected = st.selectbox("Select Category for Heatmap", categories)
    filtered_df = df[df["Category"] == selected]

    pivot = filtered_df.pivot_table(
        index="Topic",
        columns="Trainer",
        values="Category",
        aggfunc="count",
        fill_value=0
    )

    st.subheader(f"📌 {selected}s Heatmap")
    fig, ax = plt.subplots(figsize=(8, 4)) 
    sns.heatmap(pivot, annot=True, cmap="YlGnBu", fmt='d', ax=ax)
    st.pyplot(fig)

    # Stacked Bar Chart
    st.subheader("📊 Feedback Category Distribution by Topic")
    pivot_bar = pd.crosstab(index=df["Topic"], columns=df["Category"])
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    pivot_bar.plot(kind="bar", stacked=True, colormap="Pastel1", ax=ax2)
    plt.xticks(rotation=45)
    st.pyplot(fig2)

    # --------------------------- PDF Report Generation ---------------------------

    # Save all heatmaps (one per category)
    os.makedirs("charts", exist_ok=True)
    heatmap_paths = []

    for cat in df["Category"].unique():
        pivot_all = df[df["Category"] == cat].pivot_table(
            index="Topic", columns="Trainer", values="Category", aggfunc="count", fill_value=0
        )
        fig_hm, ax_hm = plt.subplots()
        sns.heatmap(pivot_all, annot=True, cmap="YlGnBu", fmt='d', ax=ax_hm)
        path = f"charts/heatmap_{cat}.png"
        fig_hm.savefig(path, dpi=300, bbox_inches='tight')
        heatmap_paths.append(path)
        plt.close()

    # Save the bar chart
    bar_chart_path = "charts/bar_distribution.png"
    fig2.savefig(bar_chart_path, dpi=300, bbox_inches='tight')

    # PDF generation
    def generate_pdf(df, heatmaps, bar_img):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("report_template.html")

    # Convert paths to absolute file URLs
        heatmaps = [f"file:///{os.path.abspath(p).replace(os.sep, '/')}" for p in heatmaps]
        bar_img = f"file:///{os.path.abspath(bar_img).replace(os.sep, '/')}"

        html_out = template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            data=df.drop(columns=["Sentiment Score"]).to_dict(orient="records"),
            heatmaps=heatmaps,
            bar_chart=bar_img
        )

        with open("report.html", "w", encoding="utf-8") as f:
            f.write(html_out)

        pdf_path = "feedback_report.pdf"

        # Set path to wkhtmltopdf
        path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    
        # REQUIRED for local file access
        options = {"enable-local-file-access": ""}

    # Generate PDF
        pdfkit.from_file("report.html", pdf_path, configuration=config, options=options)
        return pdf_path



    # Report download button
    if st.button("📥 Generate Full PDF Report"):
        pdf_file = generate_pdf(df, heatmap_paths, bar_chart_path)
        with open(pdf_file, "rb") as f:
            st.download_button("⬇️ Download Report", f.read(), file_name="feedback_report.pdf", mime="application/pdf")
