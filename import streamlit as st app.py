import streamlit as st
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter, Transformation

# ────────────────────────────────────────────────────────────────────────────────
# CONSTANTES Y CONFIGURACIÓN
# ────────────────────────────────────────────────────────────────────────────────
LETTER_WIDTH = 612   # 8.5 in × 72 pt
LETTER_HEIGHT = 792  # 11 in × 72 pt
JPEG_QUALITY = 50

st.set_page_config(page_title="Image⇢PDF & PDF Merger", page_icon="📄", layout="centered")

# ────────────────────────────────────────────────────────────────────────────────
# ESTADO: CONTADOR PARA FORZAR REFRESCO DE WIDGETS
# ────────────────────────────────────────────────────────────────────────────────
if "reset_token" not in st.session_state:
    st.session_state.reset_token = 0  # se incrementa al pulsar Limpiar

# ────────────────────────────────────────────────────────────────────────────────
# BOTÓN LIMPIAR — incrementa el token y hace un rerun
# ────────────────────────────────────────────────────────────────────────────────

def clear_interface():
    # Incrementa el token; el callback provoca el rerun automáticamente
    st.session_state.reset_token += 1
    # Basta con modificar el estado: el callback ya provoca un rerun implícito
    st.session_state.reset_token += 1
    st.session_state.reset_token += 1
    # Compatibilidad con versiones nuevas y antiguas de Streamlit
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun():
    st.session_state.reset_token += 1
    st.experimental_rerun()

st.sidebar.button("🧹 Limpiar", on_click=clear_interface)

st.title("📄 Image ⇢ PDF  •  PDF Merger")

# Selector de modo principal
mode = st.sidebar.radio("Seleccione la función", ("Convertir imágenes a PDF", "Unir PDFs"), key=f"mode_{st.session_state.reset_token}")

# ────────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────────────────────────────────────

def fit_image_to_letter(img):
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    pic = img.copy()
    pic.thumbnail((LETTER_WIDTH, LETTER_HEIGHT), Image.LANCZOS)
    canvas = Image.new("RGB", (LETTER_WIDTH, LETTER_HEIGHT), "white")
    cx = (LETTER_WIDTH - pic.width) // 2
    cy = (LETTER_HEIGHT - pic.height) // 2
    canvas.paste(pic, (cx, cy))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", optimize=True, quality=JPEG_QUALITY)
    buf.seek(0)
    return Image.open(buf)


def add_page_as_letter(writer: PdfWriter, page):
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    scale = min(LETTER_WIDTH / w, LETTER_HEIGHT / h)
    tx = (LETTER_WIDTH - w * scale) / 2
    ty = (LETTER_HEIGHT - h * scale) / 2
    blank = writer.add_blank_page(width=LETTER_WIDTH, height=LETTER_HEIGHT)
    transform = Transformation().scale(scale).translate(tx, ty)
    if hasattr(blank, "merge_transformed_page"):
        blank.merge_transformed_page(page, transform)
    else:
        blank.mergeTransformedPage(page, transform.ctm)

# ────────────────────────────────────────────────────────────────────────────────
# MODO 1 — IMÁGENES → PDF
# ────────────────────────────────────────────────────────────────────────────────
if mode == "Convertir imágenes a PDF":
    st.header("🖼️ → 📄 Convertir imágenes a PDF (tamaño carta)")

    imgs = st.file_uploader(
        "Sube imágenes",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        accept_multiple_files=True,
        key=f"img_files_{st.session_state.reset_token}"
    )
    out_name = st.text_input("Nombre del PDF", "imagenes_carta.pdf", key=f"out_name_{st.session_state.reset_token}")

    if st.button("Crear PDF", key=f"create_pdf_{st.session_state.reset_token}") and imgs:
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
            st.download_button("📥 Descargar PDF", buf, file_name=out_name, mime="application/pdf", key=f"dl_imgpdf_{st.session_state.reset_token}")
        else:
            st.warning("No se generó ninguna página válida.")

# ────────────────────────────────────────────────────────────────────────────────
# MODO 2 — UNIR PDFs
# ────────────────────────────────────────────────────────────────────────────────
else:
    st.header("📚 → 📄 Unir PDFs (uniforme carta)")

    pdfs = st.file_uploader(
        "Sube archivos PDF", type=["pdf"], accept_multiple_files=True, key=f"pdf_files_{st.session_state.reset_token}"
    )
    merged_name = st.text_input("Nombre del PDF combinado", "documento_unido.pdf", key=f"merged_name_{st.session_state.reset_token}")

    if st.button("Unir PDFs", key=f"merge_btn_{st.session_state.reset_token}") and pdfs:
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
            st.download_button("📥 Descargar PDF unido", buf, file_name=merged_name, mime="application/pdf", key=f"dl_merge_{st.session_state.reset_token}")
        else:
            st.warning("No se añadió ninguna página válida.")
