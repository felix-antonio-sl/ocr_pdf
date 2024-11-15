import streamlit as st
import ocrmypdf
import tempfile
import os
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from ocrmypdf.exceptions import Error, DigitalSignatureError, NotValidPdfError

# Título de la Aplicación
st.title("Conversor de PDF Escaneado a PDF Buscable con OCRmyPDF")

# Descripción
st.markdown("""
Esta aplicación permite cargar archivos PDF escaneados, aplicar OCR para convertirlos en PDFs buscables, y descargar el resultado.
""")

# Subida de Archivo
uploaded_file = st.file_uploader("Carga tu archivo PDF escaneado", type=["pdf"])

if uploaded_file is not None:
    # Mostrar el PDF original
    st.header("PDF Original")
    st.write("Vista previa de la primera página del PDF cargado:")

    # Guardar el archivo subido en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_original:
        tmp_original.write(uploaded_file.read())
        tmp_original_path = tmp_original.name

    # Convertir la primera página del PDF a imagen para vista previa
    try:
        original_pages = convert_from_path(tmp_original_path, first_page=1, last_page=1)
        if original_pages:
            st.image(original_pages[0], caption="Primera Página del PDF Original", use_container_width=True)
    except Exception as e:
        st.warning(f"No se pudo generar la vista previa del PDF original: {e}")

    # Opciones de OCR en la Barra Lateral
    st.sidebar.header("Opciones de OCR")
    language = st.sidebar.text_input("Idioma para OCR (ISO 639-2)", value="spa")
    optimize_level = st.sidebar.selectbox(
        "Nivel de Optimización",
        options=[0, 1, 2, 3],
        index=1,
        help="0: Sin optimización, 1: Optimización básica, 2: Optimización agresiva, 3: Máxima optimización"
    )
    output_type = st.sidebar.selectbox(
        "Tipo de Salida",
        options=["pdf", "pdfa-1", "pdfa-2", "pdfa-3"],
        index=1,
        help="pdf: Sin conversión a PDF/A, pdfa-1: PDF/A-1b, pdfa-2: PDF/A-2b, pdfa-3: PDF/A-3b"
    )
    rotate_pages = st.sidebar.checkbox("Rotar páginas automáticamente", value=True)
    deskew = st.sidebar.checkbox("Enderezar páginas (deskew)", value=True)
    clean = st.sidebar.checkbox("Limpiar imágenes (clean)", value=True)

    # Botón para Iniciar OCR
    if st.button("Iniciar OCR"):
        with st.spinner("Procesando el PDF con OCRmyPDF..."):
            try:
                # Crear un archivo temporal para el PDF procesado
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_output:
                    tmp_output_path = tmp_output.name

                # Ejecutar OCRmyPDF
                ocrmypdf.ocr(
                    input_file=tmp_original_path,
                    output_file=tmp_output_path,
                    language=language,
                    optimize=optimize_level,
                    output_type=output_type,
                    rotate_pages=rotate_pages,
                    deskew=deskew,
                    clean=clean,
                )

                # Verificar si el PDF procesado tiene una capa de texto
                reader = PdfReader(tmp_output_path)
                has_text = False
                for page in reader.pages:
                    if page.extract_text():
                        has_text = True
                        break

                if has_text:
                    # Leer el PDF procesado
                    with open(tmp_output_path, "rb") as f:
                        processed_pdf = f.read()

                    # Mostrar el PDF procesado
                    st.header("PDF con OCR Aplicado")
                    st.write("Vista previa de la primera página del PDF procesado:")

                    try:
                        processed_pages = convert_from_path(tmp_output_path, first_page=1, last_page=1)
                        if processed_pages:
                            st.image(processed_pages[0], caption="Primera Página del PDF con OCR", use_container_width=True)
                    except Exception as e:
                        st.warning(f"No se pudo generar la vista previa del PDF procesado: {e}")

                    st.download_button(
                        label="Descargar PDF con OCR",
                        data=processed_pdf,
                        file_name="searchable.pdf",
                        mime="application/pdf"
                    )

                    st.success("OCR completado exitosamente. El PDF descargado contiene texto buscable.")
                else:
                    st.error("OCR no se pudo aplicar correctamente. El PDF descargado no contiene texto buscable.")

                # Eliminar archivos temporales
                os.unlink(tmp_original_path)
                os.unlink(tmp_output_path)

            except DigitalSignatureError:
                st.error("El PDF de entrada contiene una firma digital. OCRmyPDF no puede procesar documentos con firmas digitales ya que el OCR alteraría el documento, invalidando la firma.")
            except NotValidPdfError:
                st.error("El archivo subido no es un PDF válido.")
            except Error as e:
                st.error(f"Ha ocurrido un error durante el procesamiento: {e}")
            except Exception as e:
                st.error(f"Ha ocurrido un error inesperado: {e}")
