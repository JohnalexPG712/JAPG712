import streamlit as st
from PIL import Image
import io
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="Image to PDF & PDF Merger", page_icon="📄", layout="centered")

st.title("📄 Image to PDF & PDF Merger")

mode = st.sidebar.radio("Select Function", ("Convert images to PDF", "Merge PDFs"))

if mode == "Convert images to PDF":
    st.header("Convert Images to a Single PDF")
    uploaded_files = st.file_uploader(
        "Upload image files",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        accept_multiple_files=True,
    )
    output_name = st.text_input("Output PDF filename", "merged_images.pdf")

    if st.button("Create PDF") and uploaded_files:
        images = []
        for uploaded in uploaded_files:
            image = Image.open(uploaded)
            # Ensure compatible mode
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            images.append(image)

        if images:
            buffer = io.BytesIO()
            # Save the first image and append the rest
            images[0].save(buffer, format="PDF", save_all=True, append_images=images[1:])
            buffer.seek(0)
            st.success(f"✅ {output_name} created successfully!")
            st.download_button(
                label="Download PDF",
                data=buffer,
                file_name=output_name,
                mime="application/pdf",
            )
        else:
            st.warning("No valid images found.")

elif mode == "Merge PDFs":
    st.header("Merge Multiple PDFs into One")
    pdf_files = st.file_uploader(
        "Upload PDF files", type=["pdf"], accept_multiple_files=True
    )
    merged_name = st.text_input("Merged PDF filename", "merged_document.pdf")

    if st.button("Merge PDFs") and pdf_files:
        writer = PdfWriter()
        for pdf in pdf_files:
            reader = PdfReader(pdf)
            for page in reader.pages:
                writer.add_page(page)

        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        st.success(f"✅ {merged_name} created successfully!")
        st.download_button(
            label="Download Merged PDF",
            data=buffer,
            file_name=merged_name,
            mime="application/pdf",
        )
