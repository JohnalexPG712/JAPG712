import streamlit as st
from PIL import Image
import io
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="Image⇢PDF & PDF Merger", page_icon="📄", layout="centered")

st.title("📄 Image ⇢ PDF  •  PDF Merger")

mode = st.sidebar.radio("Seleccione la función", ("Convertir imágenes a PDF", "Unir PDFs"))

# ────────────────────────────────────────────────────────────────────────────────
# UTILIDAD: Ajustar imagen a hoja carta sin recorte (puede incluir márgenes blancos)
# ────────────────────────────────────────────────────────────────────────────────

def fit_image_to_letter(img: Image.Image, dpi: int = 150, quality: int = 50) -> Image.Image:
    """Ajusta la imagen para que quepa completamente en una hoja carta sin recorte.
    Se agregan márgenes blancos si la proporción no coincide.
    Redimensiona si es necesario y exporta como JPEG comprimido.
    """
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Tamaño de hoja carta en píxeles
    carta_px = (int(8.5 * dpi), int(11 * dpi))

    # Redimensionar conservando proporción (sin recorte)
    img_copy = img.copy()
    img_copy.thumbnail(carta_px, Image.LANCZOS)

    # Crear fondo blanco tamaño carta y centrar imagen
    canvas = Image.new("RGB", carta_px, "white")
    offset = (
        (carta_px[0] - img_copy.width) // 2,
        (carta_px[1] - img_copy.height) // 2
    )
    canvas.paste(img_copy, offset)

    # Comprimir a JPEG
    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", optimize=True, quality=quality)
    buffer.seek(0)
    return Image.open(buffer)

# ────────────────────────────────────────────────────────────────────────────────
# MODO 1 — IMÁGENES → PDF
# ────────────────────────────────────────────────────────────────────────────────
if mode == "Convertir imágenes a PDF":
    st.header("🖼️  →  📄 Convertir imágenes a PDF (hoja carta sin recorte)")

    uploaded_files = st.file_uploader(
        "Sube tus imágenes (PNG, JPG, JPEG, BMP, TIFF)",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        accept_multiple_files=True,
    )

    output_name = st.text_input("Nombre del PDF a generar", "imagenes_carta.pdf")

    if st.button("Crear PDF") and uploaded_files:
        processed_images = []
        for uf in uploaded_files:
            try:
                img = Image.open(uf)
                final_img = fit_image_to_letter(img)
                processed_images.append(final_img)
            except Exception as e:
                st.error(f"❌ Error al procesar {uf.name}: {e}")

        if processed_images:
            pdf_buffer = io.BytesIO()
            processed_images[0].save(
                pdf_buffer,
                format="PDF",
                save_all=True,
                append_images=processed_images[1:]
            )
            pdf_buffer.seek(0)
            size_mb = len(pdf_buffer.getvalue()) / (1024 * 1024)
            st.success(f"✅ {output_name} creado (≈ {size_mb:.2f} MB)")
            st.download_button(
                label="📥 Descargar PDF",
                data=pdf_buffer,
                file_name=output_name,
                mime="application/pdf",
            )
        else:
            st.warning("No se generó ninguna página válida.")

# ────────────────────────────────────────────────────────────────────────────────
# MODO 2 — UNIR PDFs
# ────────────────────────────────────────────────────────────────────────────────
elif mode == "Unir PDFs":
    st.header("📚  →  📄 Unir varios PDFs en uno")

    pdf_files = st.file_uploader(
        "Sube tus archivos PDF", type=["pdf"], accept_multiple_files=True
    )

    merged_name = st.text_input("Nombre del PDF combinado", "documento_unido.pdf")

    if st.button("Unir PDFs") and pdf_files:
        writer = PdfWriter()
        for pf in pdf_files:
            try:
                reader = PdfReader(pf)
                for page in reader.pages:
                    writer.add_page(page)
            except Exception as e:
                st.error(f"No se pudo leer {pf.name}: {e}")

        if writer.pages:
            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            size_mb = len(buffer.getvalue()) / (1024 * 1024)
            st.success(f"✅ {merged_name} creado ({len(writer.pages)} páginas, ≈ {size_mb:.2f} MB)")
            st.download_button(
                label="📥 Descargar PDF unido",
                data=buffer,
                file_name=merged_name,
                mime="application/pdf",
            )
        else:
            st.warning("No se añadió ninguna página válida.")
