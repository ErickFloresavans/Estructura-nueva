import requests
import json
import re
import ollama

def preguntar_sobre_imagen(descripcion):
    """
    Usa el modelo de Ollama para deducir algo a partir de una descripción de imagen.
    """
    try:
        prompt = f"La imagen fue descrita como: '{descripcion}'. ¿Qué puedes deducir de esto?"
        response = ollama.chat(model='llama3', messages=[
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']
    except Exception as e:
        print("❌ Error en preguntar_sobre_imagen:", str(e))
        return "⚠️ No se pudo procesar la imagen."


def preguntar_a_ollama(texto):
    """
    Genera UNA respuesta completa EN ESPAÑOL para WhatsApp.
    """
    try:
        prompt = f"""
        Eres el asistente experto de AVANS especializado en SAP.

        INSTRUCCIONES CRÍTICAS:
        - RESPONDE SIEMPRE EN ESPAÑOL
        - Da una respuesta COMPLETA y útil
        - Máximo 200 palabras
        - Si son pasos: incluye TODOS los pasos necesarios (máximo 6)
        - Sé específico y claro
        - NO uses frases como "Como asistente", "En resumen", etc.
        - Empieza directamente con la información útil

        Pregunta: {texto.strip()}

        Respuesta completa en español:
        """

        response = ollama.chat(
            model='llama3',
            messages=[{"role": "system", "content": "Eres un experto en SAP que SIEMPRE responde en español de forma completa y útil."}, 
                     {"role": "user", "content": prompt}],
            options={
                "temperature": 0.1,   # Determinista
                "max_tokens": 250,    # Más tokens para respuesta completa
                "top_p": 0.8,
                "stop": ["Usuario:", "Pregunta:", "Como asistente", "En resumen"]
            }
        )

        respuesta = response['message']['content'].strip()

        # 🧹 LIMPIEZA BÁSICA (menos agresiva)
        respuesta = re.sub(r'\*\*(.*?)\*\*', r'*\1*', respuesta)
        respuesta = re.sub(r'\n{3,}', '\n\n', respuesta)  # Máximo 2 saltos de línea
        respuesta = re.sub(r'\s{3,}', ' ', respuesta)     # Máximo 2 espacios
        respuesta = re.sub(r'^(Respuesta|Como asistente|En resumen).*?[:.]?\s*', '', respuesta, flags=re.IGNORECASE)
        
        # 🔪 CORTE MENOS AGRESIVO
        if len(respuesta) > 800:  # Límite más generoso
            # Buscar el final de una oración o paso completo
            punto = respuesta[:800].rfind('.')
            if punto > 400:  # Si hay una oración completa razonable
                respuesta = respuesta[:punto + 1]
            else:
                # Buscar el final de un paso numerado
                paso = respuesta[:800].rfind('\n')
                if paso > 400:
                    respuesta = respuesta[:paso]
                else:
                    respuesta = respuesta[:800] + "..."

        # Finalizar apropiadamente
        if respuesta and not respuesta.endswith(('.', '!', '?', ':', '...')):
            respuesta += '.'

        # 🚫 VALIDACIÓN MENOS ESTRICTA
        if not respuesta or len(respuesta.strip()) < 20:
            return "Para consultas específicas sobre SAP, escribe 'hola' para ver el menú."

        # Detectar si está en inglés y rechazar
        palabras_ingles = ["create", "follow", "step", "contract", "maintenance", "system", "navigate"]
        if sum(1 for palabra in palabras_ingles if palabra in respuesta.lower()) > 2:
            return "🔧 Para crear un contrato de mantenimiento en SAP: 1. Ve a Logística > Mantenimiento. 2. Selecciona 'Contratos'. 3. Crea nuevo contrato. 4. Completa datos del cliente y equipo. 5. Define términos y fechas. 6. Guarda y activa."

        return respuesta

    except Exception as e:
        print("❌ Error en preguntar_a_ollama:", str(e))
        return "Sistema ocupado. Escribe 'hola' para ver las opciones del menú."

def interpretar_mensaje(mensaje_usuario):
    """
    Interpreta una solicitud en lenguaje natural y devuelve una instrucción en formato JSON.
    """
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read().replace("{mensaje}", mensaje_usuario)

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 200
                }
            }
        )

        if response.status_code != 200:
            print("⚠️ Error de Ollama:", response.status_code, response.text)
            return {"accion": "error"}

        texto_generado = response.json().get("response", "")
        print("🧠 Respuesta cruda de Ollama:")
        print(texto_generado)

        match = re.search(r"\{.*\}", texto_generado, re.DOTALL)
        if match:
            json_limpio = match.group(0)
            instruccion = json.loads(json_limpio)
            return instruccion
        else:
            print("❌ No se encontró un JSON válido en la respuesta.")
            return {"accion": "error"}

    except Exception as e:
        print("❌ Error al interpretar mensaje:", str(e))
        return {"accion": "error"}
