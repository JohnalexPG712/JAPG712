import streamlit as st
from PIL import Image
import io
from PyPDF2 import PdfReader, PdfWriter

st.set_page_config(page_title="Image⇢PDF & PDF Merger", page_icon="📄", layout="centered")

st.title("📄 Image ⇢ PDF  •  PDF Merger")

mode = st.sidebar.radio("Seleccione la función", ("Convertir imágenes a PDF", "Unir PDFs"))

# ────────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ────────────────────────────────────────────────────────────────────────────────

def resize_and_compress(img: Image.Image, dpi: int, quality: int) -> Image.Image:
    """Redimensiona la imagen proporcionalmente, la centra en una hoja carta y la comprime.

    - Hoja carta: 8.5 × 11 pulgadas
    - Se preserva aspect‑ratio y se rellena con fondo blanco
    - Luego se exporta a JPEG optimizado para reducir peso
    """
    # Asegurar modo RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Tamaño destino carta en píxeles
    target_px = (int(8.5 * dpi), int(11 * dpi))  # (ancho, alto)

    # Copia de la imagen para no alterar la original
    img_copy = img.copy()
    # Redimensionar conservando proporción
    img_copy.thumbnail(target_px, Image.LANCZOS)

    # Crear canvas blanco tamaño carta
    canvas = Image.new("RGB", target_px, color="white")
    # Calcular posición centrada
    offset_x = (target_px[0] - img_copy.width) // 2
    offset_y = (target_px[1] - img_copy.height) // 2
    canvas.paste(img_copy, (offset_x, offset_y))

    # Comprimir a JPEG en buffer
    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", optimize=True, quality=quality)
    buffer.seek(0)

    # Abrir de nuevo la versión comprimida como PIL Image
    return Image.open(buffer)

# ────────────────────────────────────────────────────────────────────────────────
# MODO 1 — IMÁGENES → PDF
# ────────────────────────────────────────────────────────────────────────────────
if mode == "Convertir imágenes a PDF":
    st.header("🖼️  →  📄 Convertir imágenes a PDF tamaño carta")

    uploaded_files = st.file_uploader(
        "Sube tus imágenes (PNG, JPG, JPEG, BMP, TIFF)",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        accept_multiple_files=True,
    )

    with st.expander("⚙️  Opciones de redimensionado y compresión"):
        do_resize = st.checkbox("Ajustar a carta y comprimir", value=True)
        dpi = st.slider("Resolución destino (DPI)", 72, 300, 150, step=12,
                        help="A 150 DPI se obtienen PDFs ligeros y legibles.")
        quality = st.slider("Calidad JPEG (10‑95)", 10, 95, 80,
                            help="Menor calidad ⇒ archivo más pequeño.")

    output_name = st.text_input("Nombre del PDF a generar", "imagenes_carta.pdf")

    if st.button("Crear PDF") and uploaded_files:
        processed_images = []
        for uf in uploaded_files:
            try:
                img = Image.open(uf)
            except Exception as e:
                st.error(f"No se pudo abrir {uf.name}: {e}")
                continue

            if do_resize:
                img_proc = resize_and_compress(img, dpi=dpi, quality=quality)
            else:
                img_proc = img.convert("RGB") if img.mode in ("RGBA", "P") else img

            processed_images.append(img_proc)

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
            st.warning("No se procesó ninguna imagen válida.")

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
            except Exception as e:
                st.error(f"No se pudo leer {pf.name}: {e}")
                continue
            for page in reader.pages:
                writer.add_page(page)

        total_pages = len(writer.pages)
        if total_pages:
            buffer = io.BytesIO()
            writer.write(buffer)
            buffer.seek(0)
            size_mb = len(buffer.getvalue()) / (1024 * 1024)
            st.success(f"✅ {merged_name} creado ({total_pages} páginas, ≈ {size_mb:.2f} MB)")
            st.download_button(
                label="📥 Descargar PDF unido",
                data=buffer,
                file_name=merged_name,
                mime="application/pdf",
            )
        else:
            st.warning("No se añadió ninguna página válida.")

