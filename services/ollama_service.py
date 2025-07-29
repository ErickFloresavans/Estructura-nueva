"""
Servicio para interacción con Ollama y gestión de memoria RAG.
Maneja consultas de IA y almacenamiento de conocimiento.
"""

import re
from typing import Optional, List, Dict, Any
from ollama_interface import preguntar_a_ollama, interpretar_mensaje

# Intentar importar RAG, pero funcionar sin él si no está disponible
try:
    from rag_memory import buscar_contexto, guardar_texto
    RAG_AVAILABLE = True
    print("✅ Sistema RAG disponible")
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️ Sistema RAG no disponible")


class OllamaService:
    """
    Servicio centralizado para interacción con Ollama y memoria RAG.
    
    Responsabilidades:
    - Generar respuestas usando Ollama
    - Gestionar memoria RAG (si está disponible)
    - Procesar consultas con contexto
    - Analizar imágenes con IA
    - Interpretar intenciones de usuario
    """
    
    def __init__(self):
        self.model_name = "llama3"
        self.max_response_length = 800
        self.rag_available = RAG_AVAILABLE
        
        # Configuraciones de prompt
        self.system_prompt = """
        Eres el asistente experto de AVANS especializado en muchas areas como SAP, manuales, bases de datos, entre otras mas.
        
        INSTRUCCIONES CRÍTICAS:
        - RESPONDE SIEMPRE EN ESPAÑOL
        - Da una respuesta COMPLETA y útil
        - Máximo 200 palabras
        - Si son pasos: incluye TODOS los pasos necesarios (máximo 6)
        - Sé específico y claro
        - NO uses frases como "Como asistente", "En resumen", etc.
        - Empieza directamente con la información útil
        """
    
    def ask(self, question: str) -> str:
        """
        Hace una pregunta directa a Ollama sin contexto adicional.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            Respuesta generada por Ollama
        """
        try:
            response = preguntar_a_ollama(question)
            return self._clean_response(response)
            
        except Exception as e:
            print(f"❌ Error en consulta Ollama: {e}")
            return "Sistema ocupado. Escribe 'hola' para ver las opciones del menú."
    
    def ask_with_context(self, question: str, additional_context: str = "") -> str:
        """
        Hace una pregunta a Ollama con contexto adicional.
        
        Args:
            question: Pregunta del usuario
            additional_context: Contexto adicional para la respuesta
            
        Returns:
            Respuesta generada por Ollama con contexto
        """
        try:
            # Construir prompt con contexto
            if additional_context:
                full_prompt = f"{additional_context}\n\nPregunta del usuario: {question}"
            else:
                full_prompt = question
            
            response = preguntar_a_ollama(full_prompt)
            return self._clean_response(response)
            
        except Exception as e:
            print(f"❌ Error en consulta Ollama con contexto: {e}")
            return "Error procesando consulta. Intenta nuevamente."
    
    def search_with_context(self, query: str, max_results: int = 3) -> Optional[str]:
        """
        Busca en la memoria RAG y genera respuesta con contexto.
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados RAG
            
        Returns:
            Respuesta basada en contexto RAG o None si no hay contexto
        """
        if not self.rag_available:
            return None
        
        try:
            # Buscar contexto en RAG
            context = buscar_contexto(query, k=max_results)
            
            if not context or not context.strip():
                return None
            
            # Generar respuesta con contexto
            prompt = f"Basándote en esta información: {context}\n\nResponde a: {query}"
            response = self.ask_with_context(query, context)
            
            return response
            
        except Exception as e:
            print(f"❌ Error en búsqueda con contexto: {e}")
            return None
    
    def analyze_image_with_context(self, image_description: str) -> str:
        """
        Analiza una descripción de imagen con contexto RAG si está disponible.
        
        Args:
            image_description: Descripción de la imagen
            
        Returns:
            Análisis de la imagen con contexto
        """
        try:
            # Intentar obtener contexto relacionado
            context = ""
            if self.rag_available:
                try:
                    context = buscar_contexto(image_description, k=2)
                except:
                    pass
            
            # Construir prompt para análisis de imagen
            if context:
                prompt = f"Imagen descrita como: '{image_description}'. Contexto relacionado: {context}. Analiza como experto AVANS en SAP."
            else:
                prompt = f"Como experto AVANS en SAP, analiza esta imagen: {image_description}"
            
            response = self.ask(prompt)
            return response
            
        except Exception as e:
            print(f"❌ Error analizando imagen: {e}")
            return "No se pudo analizar la imagen. Describe el contenido por texto."
    
    def interpret_user_intention(self, message: str) -> Dict[str, Any]:
        """
        Interpreta la intención del usuario usando Ollama.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Diccionario con la intención interpretada
        """
        try:
            result = interpretar_mensaje(message)
            
            # Validar que el resultado sea un diccionario válido
            if isinstance(result, dict) and "accion" in result:
                return result
            else:
                return {"accion": "texto_libre", "parametro": message}
                
        except Exception as e:
            print(f"❌ Error interpretando intención: {e}")
            return {"accion": "error", "parametro": message}
    
    def save_to_memory(self, text: str, source: str = "WhatsApp", 
                      metadata: Dict[str, Any] = None) -> bool:
        """
        Guarda información en la memoria RAG.
        
        Args:
            text: Texto a guardar
            source: Fuente del conocimiento
            metadata: Metadatos adicionales
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        if not self.rag_available:
            print("⚠️ Sistema RAG no disponible para guardar memoria")
            return False
        
        try:
            # Preparar metadatos por defecto
            default_metadata = {
                "tipo": "manual",
                "fuente": source,
                "categoria": "general"
            }
            
            if metadata:
                default_metadata.update(metadata)
            
            # Guardar en memoria
            guardar_texto(text, source, default_metadata.get("tipo", "manual"), 
                         default_metadata.get("categoria", "general"))
            
            print(f"✅ Conocimiento guardado en memoria: {text[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando en memoria: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la memoria RAG.
        
        Returns:
            Diccionario con estadísticas de memoria
        """
        if not self.rag_available:
            return {"available": False, "message": "Sistema RAG no disponible"}
        
        try:
            # Aquí podrías implementar estadísticas específicas del sistema RAG
            # Por ahora retornamos información básica
            return {
                "available": True,
                "message": "Sistema RAG operativo",
                "features": ["búsqueda_contexto", "guardar_texto", "análisis_imagen"]
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas de memoria: {e}")
            return {"available": False, "error": str(e)}
    
    def _clean_response(self, response: str) -> str:
        """
        Limpia y formatea la respuesta de Ollama.
        
        Args:
            response: Respuesta cruda de Ollama
            
        Returns:
            Respuesta limpia y formateada
        """
        if not response or not isinstance(response, str):
            return "No se pudo generar una respuesta."
        
        # Limpiezas básicas
        cleaned = response.strip()
        
        # Convertir markdown bold a WhatsApp format
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'*\1*', cleaned)
        
        # Limitar saltos de línea excesivos
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Limitar espacios excesivos
        cleaned = re.sub(r'\s{3,}', ' ', cleaned)
        
        # Remover frases de inicio no deseadas
        unwanted_starts = [
            r'^(Respuesta|Como asistente|En resumen).*?[:.]?\s*',
            r'^(Hola|Buenos días|Buenas tardes).*?[:.]?\s*'
        ]
        
        for pattern in unwanted_starts:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Cortar si es muy largo
        if len(cleaned) > self.max_response_length:
            # Buscar punto final apropiado
            cut_point = cleaned[:self.max_response_length].rfind('.')
            if cut_point > self.max_response_length * 0.7:  # Solo si no corta demasiado
                cleaned = cleaned[:cut_point + 1]
            else:
                # Buscar salto de línea apropiado
                cut_point = cleaned[:self.max_response_length].rfind('\n')
                if cut_point > self.max_response_length * 0.7:
                    cleaned = cleaned[:cut_point]
                else:
                    cleaned = cleaned[:self.max_response_length] + "..."
        
        # Asegurar que termine apropiadamente
        if cleaned and not cleaned.endswith(('.', '!', '?', ':', '...')):
            cleaned += '.'
        
        # Validación final
        if not cleaned or len(cleaned.strip()) < 10:
            return "Para consultas específicas sobre SAP, escribe 'hola' para ver el menú."
        
        return cleaned
    
    def test_ollama_connection(self) -> Dict[str, Any]:
        """
        Prueba la conectividad con Ollama.
        
        Returns:
            Diccionario con información del estado de Ollama
        """
        try:
            test_response = self.ask("Test de conectividad")
            
            return {
                "available": True,
                "model": self.model_name,
                "response_length": len(test_response),
                "rag_available": self.rag_available
            }
            
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "model": self.model_name,
                "rag_available": self.rag_available
            }