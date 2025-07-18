from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os

os.environ["HF_HOME"] = "/home/ollama-bot/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/home/ollama-bot/hf_cache"
os.environ["HF_DATASETS_CACHE"] = "/home/ollama-bot/hf_cache"

# Cargar modelo de embeddings
model = SentenceTransformer("/home/ollama-bot/modelos/all-MiniLM-L6-v2")
print("✅ Modelo cargado:", model)

# Base de datos en memoria
textos = []
embeddings = []

# Archivo de respaldo
MEMORIA_JSON = "memoria_vectorial.json"

# Inicializar base FAISS
dim = 384  # Dimensión del embedding de MiniLM
index = faiss.IndexFlatL2(dim)

def cargar_memoria():
    global textos, embeddings, index
    if os.path.exists(MEMORIA_JSON):
        with open(MEMORIA_JSON, "r", encoding="utf-8") as f:
            textos = json.load(f)
        emb_matrix = model.encode(textos, convert_to_numpy=True)
        embeddings = emb_matrix
        index.add(emb_matrix)

def guardar_texto(texto):
    textos.append(texto)
    nuevo_vector = model.encode([texto])
    index.add(nuevo_vector)
    with open(MEMORIA_JSON, "w", encoding="utf-8") as f:
        json.dump(textos, f, ensure_ascii=False, indent=2)

def buscar_contexto(pregunta, k=3):
    pregunta_vec = model.encode([pregunta])
    D, I = index.search(pregunta_vec, k)
    resultados = [textos[i] for i in I[0] if i < len(textos)]
    return "\n".join(resultados)
