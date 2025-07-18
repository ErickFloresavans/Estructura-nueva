from limpieza import procesar_pdf, CARPETA_PDFS
from rag_memory import reiniciar_memoria, cargar_libros_en_lote
import os

print("🧹 Paso 1: Eliminando memoria anterior...")
reiniciar_memoria()

print("📄 Paso 2: Procesando libros con OCR y limpieza...")
carpeta_jsons = "datata/jsons"
os.makedirs(carpeta_jsons, exist_ok=True)

contador = 0
for archivo in os.listdir(CARPETA_PDFS):
    if archivo.lower().endswith(".pdf"):
        ruta = os.path.join(CARPETA_PDFS, archivo)
        procesar_pdf(ruta, archivo)
        contador += 1

print(f"✅ Se procesaron {contador} libros en total.")

print("🧠 Paso 3: Vectorizando libros y cargando en FAISS...")
cargar_libros_en_lote(carpeta_jsons)

print("✅ ¡Todo listo! Puedes iniciar el servidor con: python app.py")
