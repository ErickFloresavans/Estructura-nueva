from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import os

# Asegura la ruta del nuevo caché
CACHE_DIR = "/home/ollama-bot/hf_cache"

processor = BlipProcessor.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    cache_dir=CACHE_DIR
)

model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base",
    cache_dir=CACHE_DIR
)

def describir_imagen(path_imagen):
    image = Image.open(path_imagen).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    return processor.decode(out[0], skip_special_tokens=True)
