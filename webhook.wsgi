#!/usr/bin/python3
import os
import sys

# 🚀 ACTIVAR ENTORNO VIRTUAL - MÉTODO SIMPLE
sys.path.insert(0, '/home/ollama-bot/venv/lib/python3.12/site-packages')

# 🧠 Variables de entorno para modelos de IA
os.environ["HF_HOME"] = "/home/ollama-bot/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/home/ollama-bot/hf_cache"
os.environ["HF_DATASETS_CACHE"] = "/home/ollama-bot/hf_cache"

# 📁 Agregar ruta del proyecto
sys.path.insert(0, "/home/ollama-bot/Pruebas")

# 🚀 Importar la aplicación
from app import app as application
