import streamlit as st
from PIL import Image
import io
from PyPDF2 import PdfReader, PdfWriter, PageObject, Transformation

# ────────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ────────────────────────────────────────────────────────────────────────────────
LETTER_WIDTH = 612   # 8.5  pulgadas × 72 pt
LETTER_HEIGHT = 792  # 11   pulgadas × 72 pt
JPEG_QUALITY = 35    # compresión automática (0‑100)

st.set_page_config(page_title="Image⇢PDF & PDF Merger", page_icon="📄", layout="centered")

st.title("📄 Image ⇢ PDF  •  PDF Merger")

# ────────────────────────────────────────────────────────────────────────────────
# BOTÓN UNIVERSAL DE LIMPIEZA
# ────────────────────────────────────────────────────────────────────────────────

def clear_inputs():
    """Reinicia los widgets de carga de archivos y los textos."""
    for key in ("img_files", "pdf_files", "output_name", "merged_name"):
        if key in st.session_state:
            st.session_state[key] = None

# Colocamos el botón en el sidebar para que aparezca siempre
st.sidebar.button("🧹 Limpiar", on_click=clear_inputs)

# Selector de modo
mode = st.sidebar.radio("Seleccione la función", ("Convertir imágenes a PDF", "Unir PDFs"))

# ────────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────────────────────────────────────

def fit_image_to_letter(img: Image.Image) -> Image.Image:
    """Ajusta la imagen para que quepa completamente en una hoja carta (sin recorte)."""
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Redimensionar manteniendo proporción
    img_copy = img.copy()
    img_copy.thumbnail((LETTER_WIDTH, LETTER_HEIGHT), Image.LANCZOS)

    # Crear lienzo blanco carta y centrar la foto
    canvas = Image.new("RGB", (LETTER_WIDTH, LETTER_HEIGHT), "white")
    off_x = (LETTER_WIDTH - img_copy.width) // 2
    off_y = (LETTER_HEIGHT - img_copy.height) // 2
    canvas.paste(img_copy, (off_x, off_y))

    # Comprimir
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", optimize=True, quality=JPEG_QUALITY)
    buf.seek(0)
    return Image.open(buf)


def add_page_as_letter(writer: PdfWriter, page) -> None:
    """Inserta una página PDF dentro de una hoja carta manteniendo proporción."""
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    scale = min(LETTER_WIDTH / w, LETTER_HEIGHT / h)
    tx = (LETTER_WIDTH - w * scale) / 2
    ty = (LETTER_HEIGHT - h * scale) / 2

    blank = PageObject.create_blank_page(None, width=LETTER_WIDTH, height=LETTER_HEIGHT)
    blank.merge_transformed_page(page, Transformation().scale(scale).translate(tx, ty))
    writer.add_page(blank)

# ────────────────────────────────────────────────────────────────────────────────
# MODO 1 — IMÁGENES → PDF
# ────────────────────────────────────────────────────────────────────────────────
if mode == "Convertir imágenes a PDF":
    st.header("🖼️  →  📄 Convertir imágenes a PDF")

    uploaded_files = st.file_uploader(
        "Sube tus imágenes (PNG, JPG, JPEG, BMP, TIFF)",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        accept_multiple_files=True,
        key="img_files",
    )

    output_name = st.text_input("Nombre del PDF a generar", "imagenes_carta.pdf", key="output_name")

    if st.button("Crear PDF") and uploaded_files:
        pages = []
        for uf in uploaded_files:
            try:
                pil = Image.open(uf)
                pages.append(fit_image_to_letter(pil))
            except Exception as e:
                st.error(f"❌ {uf.name}: {e}")

        if pages:
            buf = io.BytesIO()
            pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
            buf.seek(0)
            size = len(buf.getvalue()) / 1_048_576
            st.success(f"✅ {output_name} creado (≈ {size:.2f} MB)")
            st.download_button("📥 Descargar PDF", buf, file_name=output_name, mime="application/pdf")
        else:
            st.warning("No se generó ninguna página válida.")

# ────────────────────────────────────────────────────────────────────────────────
# MODO 2 — UNIR PDFs
# ────────────────────────────────────────────────────────────────────────────────
elif mode == "Unir PDFs":
    st.header("📚  →  📄 Unir varios PDFs en uno (formato carta)")

    pdf_files = st.file_uploader("Sube tus archivos PDF", type=["pdf"], accept_multiple_files=True, key="pdf_files")
    merged_name = st.text_input("Nombre del PDF combinado", "documento_unido.pdf", key="merged_name")

    if st.button("Unir PDFs") and pdf_files:
        writer = PdfWriter()
        for pf in pdf_files:
            try:
                reader = PdfReader(pf)
                for page in reader.pages:
                    add_page_as_letter(writer, page)
            except Exception as e:
                st.error(f"❌ {pf.name}: {e}")

        if writer.pages:
            buf = io.BytesIO()
            writer.write(buf)
            buf.seek(0)
            size = len(buf.getvalue()) / 1_048_576
            st.success(f"✅ {merged_name} creado ({len(writer.pages)} páginas, ≈ {size:.2f} MB)")
            st.download_button("📥 Descargar PDF unido", buf, file_name=merged_name, mime="application/pdf")
        else:
            st.warning("No se añadió ninguna página válida.")
