import streamlit as st
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter, Transformation

# ────────────────────────────────────────────────────────────────────────────────
# CONSTANTES Y CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────────────────────
LETTER_WIDTH = 612   # 8.5 in × 72 pt
LETTER_HEIGHT = 792  # 11 in × 72 pt
JPEG_QUALITY = 50    # Calidad de compresión JPEG (0–100)

st.set_page_config(page_title="Image⇢PDF & PDF Merger", page_icon="📄", layout="centered")

st.title("📄 Image ⇢ PDF  •  PDF Merger")

# ────────────────────────────────────────────────────────────────────────────────
# BOTÓN LIMPIAR (reinicia por completo la interfaz)
# ────────────────────────────────────────────────────────────────────────────────

def clear_and_rerun():
    st.session_state.clear()
    st.experimental_rerun()

st.sidebar.button("🧹 Limpiar", on_click=clear_and_rerun)

# Selector de modo principal
mode = st.sidebar.radio("Seleccione la función", ("Convertir imágenes a PDF", "Unir PDFs"))

# ────────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────────────────────────────────────

def fit_image_to_letter(img):
    """Ajusta una imagen para caber completa en una página tamaño carta."""
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    pic = img.copy()
    pic.thumbnail((LETTER_WIDTH, LETTER_HEIGHT), Image.LANCZOS)
    canvas = Image.new("RGB", (LETTER_WIDTH, LETTER_HEIGHT), "white")
    x = (LETTER_WIDTH - pic.width) // 2
    y = (LETTER_HEIGHT - pic.height) // 2
    canvas.paste(pic, (x, y))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", optimize=True, quality=JPEG_QUALITY)
    buf.seek(0)
    return Image.open(buf)


def add_page_as_letter(writer: PdfWriter, page):
    """Inserta una página PDF existente dentro de un lienzo carta en blanco."""
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)
    scale = min(LETTER_WIDTH / w, LETTER_HEIGHT / h)
    tx = (LETTER_WIDTH - w * scale) / 2
    ty = (LETTER_HEIGHT - h * scale) / 2
    blank = writer.add_blank_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)
    transform = Transformation().scale(scale).translate(tx, ty)
    if hasattr(blank, "merge_transformed_page"):
        blank.merge_transformed_page(page, transform)
    else:  # Compatibilidad retro
        blank.mergeTransformedPage(page, transform.ctm)

# ────────────────────────────────────────────────────────────────────────────────
# MODO 1 — CONVERTIR IMÁGENES A PDF
# ────────────────────────────────────────────────────────────────────────────────
if mode == "Convertir imágenes a PDF":
    st.header("🖼️ → 📄 Convertir imágenes a PDF")

    imgs = st.file_uploader("Sube imágenes", type=["png", "jpg", "jpeg", "bmp", "tiff"], accept_multiple_files=True)
    out_name = st.text_input("Nombre del PDF", "imagenes_carta.pdf")

    if st.button("Crear PDF") and imgs:
        pages = []
        for uf in imgs:
            try:
                pages.append(fit_image_to_letter(Image.open(uf)))
            except Exception as e:
                st.error(f"❌ {uf.name}: {e}")
        if pages:
            buf = io.BytesIO()
            pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
            buf.seek(0)
            st.success("PDF generado correctamente.")
            st.download_button("📥 Descargar PDF", buf, file_name=out_name, mime="application/pdf")
        else:
            st.warning("No se generó ninguna página válida.")

# ────────────────────────────────────────────────────────────────────────────────
# MODO 2 — UNIR PDFs Y NORMALIZAR A CARTA
# ────────────────────────────────────────────────────────────────────────────────
else:
    st.header("📚 → 📄 Unir PDFs (uniforme carta)")

    pdfs = st.file_uploader("Sube archivos PDF", type=["pdf"], accept_multiple_files=True)
    merged_name = st.text_input("Nombre del PDF combinado", "documento_unido.pdf")

    if st.button("Unir PDFs") and pdfs:
        writer = PdfWriter()
        for pf in pdfs:
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
            st.success("PDF combinado creado correctamente.")
            st.download_button("📥 Descargar PDF unido", buf, file_name=merged_name, mime="application/pdf")
        else:
            st.warning("No se añadió ninguna página válida.")
