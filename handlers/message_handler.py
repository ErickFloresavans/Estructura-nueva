"""
Procesador principal de mensajes de WhatsApp.
Maneja la lógica de interpretación y enrutamiento de mensajes.
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from services.whatsapp_service import WhatsAppService
from services.database_service import DatabaseService
from services.ollama_service import OllamaService
from services.image_service import ImageService
from handlers.state_manager import StateManager, UserState
from handlers.response_builder import ResponseBuilder
from utils.validators import validate_order_number
from utils.helpers import extract_text_from_message
from db import guardar_interaccion


@dataclass
class MessageContext:
    """Contexto completo de un mensaje recibido."""
    text: str
    number: str
    message_id: str
    name: str
    message_type: str
    raw_message: dict


class MessageHandler:
    """
    Procesador principal de mensajes de WhatsApp.

    Responsabilidades:
    - Interpretar el tipo de mensaje recibido
    - Enrutar a los handlers apropiados
    - Coordinar respuestas entre servicios
    - Mantener el flujo de conversación
    """

    def __init__(self):
        self.whatsapp = WhatsAppService()
        self.database = DatabaseService()
        self.ollama = OllamaService()
        self.image_service = ImageService()
        self.state_manager = StateManager()
        self.response_builder = ResponseBuilder()

        # Control anti-spam más eficiente
        self._last_responses: Dict[str, float] = {}
        self._processing_users: set = set()
        self.COOLDOWN_SECONDS = 10

    def handle_message(self, raw_message: dict, number: str, message_id: str, name: str) -> None:
        """
        Punto de entrada principal para procesar un mensaje.

        Args:
            raw_message: Mensaje crudo de WhatsApp API
            number: Número de teléfono del usuario
            message_id: ID único del mensaje
            name: Nombre del usuario
        """
        print(f"[🔍 HANDLER] Procesando mensaje de {name} ({number})")

        # Extraer información del mensaje
        context = self._build_message_context(raw_message, number, message_id, name)
        print(f"📨 Texto recibido: {context.text}")

        print(f"👤 Número: {context.number}")

        print(f"🔎 Estado actual: {self.state_manager.get_user_state(context.number)}")
        print(f"📨 Texto recibido: {context.text}")
        print(f"👤 Número: {context.number}")
        print(f"🔎 Estado actual: {self.state_manager.get_user_state(context.number)}")

        # Verificar rate limiting
        if self._is_rate_limited(context):
            print(f"[🛑 RATE LIMIT] Usuario {number} está en cooldown")
            return

        try:
            # Marcar al usuario como en procesamiento
            self._mark_user_processing(number)

            # Marcar mensaje como leído
            self.whatsapp.mark_message_read(message_id)

            # Procesar según el tipo de mensaje
            responses = self._route_message(context)
            print(f"✅ Respuestas generadas: {responses}")

            # Enviar respuestas
            self._send_responses(number, responses)

            # Guardar interacción para analytics
            self._save_interaction(context, responses)

        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            error_response = self.response_builder.build_error_message()
            self.whatsapp.send_text(number, error_response)

        finally:
            # Liberar usuario del procesamiento
            self._unmark_user_processing(number)

    def _build_message_context(self, raw_message: dict, number: str,
                              message_id: str, name: str) -> MessageContext:
        """Construye el contexto completo del mensaje."""
        message_type = raw_message.get("type", "unknown")
        text = extract_text_from_message(raw_message)

        return MessageContext(
            text=text,
            number=number,
            message_id=message_id,
            name=name,
            message_type=message_type,
            raw_message=raw_message
        )

    def _is_rate_limited(self, context: MessageContext) -> bool:
        """Verifica si el usuario está en cooldown."""
        user_key = f"{context.number}_{context.text[:20].lower()}"
        current_time = time.time()

        # Verificar si está en procesamiento
        if context.number in self._processing_users:
            return True

        # Verificar cooldown
        if user_key in self._last_responses:
            time_diff = current_time - self._last_responses[user_key]
            if time_diff < self.COOLDOWN_SECONDS:
                return True

        # Actualizar timestamp
        self._last_responses[user_key] = current_time

        # Limpiar entradas viejas (cada 100 mensajes)
        if len(self._last_responses) > 100:
            self._cleanup_old_responses(current_time)

        return False

    def _cleanup_old_responses(self, current_time: float) -> None:
        """Limpia respuestas antiguas para evitar memory leaks."""
        cutoff_time = current_time - 600  # 10 minutos
        old_keys = [key for key, timestamp in self._last_responses.items()
                   if timestamp < cutoff_time]

        for key in old_keys:
            del self._last_responses[key]

    def _mark_user_processing(self, number: str) -> None:
        """Marca al usuario como en procesamiento."""
        self._processing_users.add(number)

    def _unmark_user_processing(self, number: str) -> None:
        """Libera al usuario del procesamiento."""
        self._processing_users.discard(number)

    def _route_message(self, context: MessageContext) -> List[str]:
        """
        Enruta el mensaje al handler apropiado según su tipo y estado del usuario.

        Returns:
            Lista de respuestas a enviar
        """
        # 1. Procesar imágenes
        if context.message_type == "image":
            return self._handle_image_message(context)

        # 2. Procesar comandos de memoria RAG
        if context.text.startswith(("memoria:", "agregar:")):
            return self._handle_memory_command(context)

        # 3. Obtener estado actual del usuario
        current_state = self.state_manager.get_user_state(context.number)

        # 4. Procesar según estado
        if current_state:
            return self._handle_stateful_message(context, current_state)
        else:
            return self._handle_stateless_message(context)

    def _handle_image_message(self, context: MessageContext) -> List[str]:
        """Procesa mensajes que contienen imágenes."""
        if not self.image_service.is_available():
            return ["📷 Imagen recibida. Describe el contenido por texto para ayudarte mejor."]

        try:
            # Procesar imagen
            analysis = self.image_service.analyze_image(context.raw_message["image"]["id"])

            # Generar respuesta con contexto
            response = self.ollama.analyze_image_with_context(analysis)

            return [f"🖼️ *Análisis de imagen:*\n{response}"]

        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            return ["⚠️ No se pudo procesar la imagen."]

    def _handle_memory_command(self, context: MessageContext) -> List[str]:
        """Procesa comandos de memoria RAG."""
        try:
            content = context.text.split(":", 1)[1].strip()

            if " | " in content:
                text, source = content.split(" | ", 1)
            else:
                text, source = content, f"WhatsApp ({context.name})"

            # Guardar en memoria
            self.ollama.save_to_memory(text, source)

            return [f"🧠 Conocimiento guardado:\n*{text[:100]}...*\n📁 Fuente: {source}"]

        except Exception as e:
            print(f"❌ Error guardando memoria: {e}")
            return ["⚠️ No se pudo guardar el conocimiento."]

    def _handle_stateful_message(self, context: MessageContext, state: str) -> List[str]:
        """Maneja mensajes cuando el usuario está en un estado específico."""

        if state == UserState.AWAITING_PART_SEARCH:
            return self._handle_part_search(context)

        elif state == UserState.AWAITING_STATUS_SEARCH:
            return self._handle_status_search(context)

        elif state == UserState.AWAITING_ORDER_NUMBER:
            return self._handle_order_search(context)

        elif state.startswith("post_"):
            return self._handle_post_action(context, state)

        else:
            # Estado desconocido, resetear
            self.state_manager.clear_user_state(context.number)
            return self._handle_greeting(context)

    def _handle_stateless_message(self, context: MessageContext) -> List[str]:
        """Maneja mensajes cuando el usuario no está en ningún estado específico."""

        # Comandos básicos
        if context.text in ["hola", "ayuda", "empezar", "menu"]:
            return self._handle_greeting(context)

        elif context.text in ["consulta", "menubtn1"]:
            return self._handle_part_consultation_start(context)

        elif context.text in ["estatus", "menubtn2"]:
            return self._handle_status_consultation_start(context)

        elif context.text in ["ordenes", "órdenes", "menubtn3"]:
            return self._handle_order_consultation_start(context)

        # Respuestas sí/no sin contexto
        elif context.text in ["sí", "si", "no"]:
            return self._handle_greeting(context)

        # Texto libre - intentar consulta automática + Ollama
        else:
            return self._handle_free_text(context)

    def _handle_greeting(self, context: MessageContext) -> List[str]:
        """Maneja saludos y muestra el menú principal."""
        self.state_manager.clear_user_state(context.number)

        return [self.response_builder.build_main_menu(
            title="Hola, ¿en qué puedo ayudarte?",
            options=["consulta", "estatus", "ordenes"],
            footer="Equipo AVANS"
        )]

    def _handle_part_consultation_start(self, context: MessageContext) -> List[str]:
        """Inicia consulta de piezas."""
        self.state_manager.set_user_state(context.number, UserState.AWAITING_PART_SEARCH)
        return ["🔍 Escribe el nombre o código de la pieza que deseas consultar."]

    def _handle_status_consultation_start(self, context: MessageContext) -> List[str]:
        """Inicia consulta de estatus."""
        self.state_manager.set_user_state(context.number, UserState.AWAITING_STATUS_SEARCH)
        return ["🛠️ Escribe el nombre o código de la pieza para consultar su estatus."]

    def _handle_order_consultation_start(self, context: MessageContext) -> List[str]:
        """Inicia consulta de órdenes."""
        self.state_manager.set_user_state(context.number, UserState.AWAITING_ORDER_NUMBER)
        return ["📦 Escribe el número de orden que deseas consultar."]

    def _handle_part_search(self, context: MessageContext) -> List[str]:
        """Procesa búsqueda de piezas."""
        print(f"🔍 Búsqueda de pieza: {context.text}")
        parts = self.database.search_parts(context.text)

        if not parts:
            print("🧠 Consultando RAG por falta de resultados en BD")
            # Intentar con RAG si no hay resultados
            rag_response = self.ollama.search_with_context(f"pieza {context.text}")
            if rag_response:
                response = f"⚠️ No encontré esa pieza en la base de datos.\n\n🧠 *Info relacionada:*\n{rag_response}"
            else:
                response = "⚠️ No se encontraron piezas con ese nombre o código."

            return [response]

        # Construir respuesta con disponibilidad
        response = self.response_builder.build_parts_response(parts)
        response.append(self.response_builder.build_yes_no_question(
            "¿Consultar otra pieza?", "postconsulta"
        ))

        self.state_manager.set_user_state(context.number, UserState.POST_CONSULTATION)
        return response

    def _handle_status_search(self, context: MessageContext) -> List[str]:
        """Procesa consulta de estatus."""
        parts = self.database.search_parts_for_status(context.text)

        if not parts:
            return ["⚠️ No se encontró esa pieza para consultar estatus."]

        response = self.response_builder.build_status_response(parts)
        response.append(self.response_builder.build_yes_no_question(
            "¿Consultar otra pieza?", "poststatus"
        ))

        self.state_manager.set_user_state(context.number, UserState.POST_STATUS)
        return response

    def _handle_order_search(self, context: MessageContext) -> List[str]:
        """Procesa consulta de órdenes."""
        if not validate_order_number(context.text):
            return ["⚠️ El número de orden debe ser numérico. Intenta nuevamente."]

        order_data = self.database.get_order_data(int(context.text))

        if not order_data:
            return ["⚠️ No se encontró una orden con ese número."]

        response = self.response_builder.build_order_response(order_data)
        response.append(self.response_builder.build_yes_no_question(
            "¿Consultar otra orden?", "postorden"
        ))

        self.state_manager.set_user_state(context.number, UserState.POST_ORDER)
        return response

    def _handle_post_action(self, context: MessageContext, state: str) -> List[str]:
        """Maneja respuestas después de una consulta."""
        if context.text in ["sí", "si"]:
            # Reiniciar el flujo correspondiente
            if state == "post_consultation":
                return self._handle_part_consultation_start(context)
            elif state == "post_status":
                return self._handle_status_consultation_start(context)
            elif state == "post_order":
                return self._handle_order_consultation_start(context)

        elif context.text == "no":
            self.state_manager.clear_user_state(context.number)
            return ["✅ Perfecto. Escribe *hola* si necesitas algo más. ¡Gracias por usar AVANS!"]

        # Respuesta no reconocida en estado post-acción
        return self._handle_greeting(context)

    def _handle_free_text(self, context: MessageContext) -> List[str]:
        """Maneja texto libre con múltiples estrategias de búsqueda."""
        try:
            print(f"🔍 Procesando texto libre: '{context.text}'")
            
            # 1. Intentar consulta automática
            db_result = self.database.process_automatic_query(context.text)
            print(f"📊 Resultado consulta automática: {db_result}")
            
            if db_result:
                return [f"🤖 *Resultado de base de datos:*\n\n{db_result}"]
            
            # 2. Intentar búsqueda directa de piezas si no hay resultado automático
            parts = self.database.search_parts(context.text, limit=3)
            print(f"🔧 Piezas encontradas: {len(parts) if parts else 0}")
            
            if parts:
                response = self.response_builder.build_parts_response(parts)
                return response
            
            # 3. Intentar búsqueda de órdenes por cliente si parece un nombre
            if context.text.replace(" ", "").isalpha() and len(context.text) > 3:
                orders = self.database.search_orders_by_client(context.text, limit=3)
                print(f"📦 Órdenes encontradas: {len(orders) if orders else 0}")
                
                if orders:
                    response = self.response_builder.build_orders_response(orders)
                    return response
            
            # 4. Si nada funciona, usar Ollama como respaldo
            print("🧠 Consultando Ollama como respaldo")
            ollama_response = self.ollama.search_with_context(context.text)
            
            if ollama_response:
                return [f"🤖 *Respuesta inteligente:*\n\n{ollama_response}"]
            
            # 5. Último recurso: mensaje de ayuda
            return [
                "🤖 No encontré información específica sobre eso.\n\n"
                "💡 *Puedes intentar:*\n"
                "• Escribe *consulta* para buscar piezas\n"
                "• Escribe *estatus* para verificar estados\n"
                "• Escribe *ordenes* para consultar pedidos\n"
                "• O describe mejor lo que necesitas"
            ]

        except Exception as e:
            print(f"❌ Error en texto libre: {e}")
            return ["🤖 Error procesando consulta. Escribe 'hola' para ver el menú."]


    def _send_responses(self, number: str, responses: List[str]) -> None:
        """Envía lista de respuestas con delay apropiado."""
        for i, response in enumerate(responses):
            try:
                if response.startswith('{'):
                    # Es un mensaje interactivo (JSON)
                    self.whatsapp.send_interactive_message(number, response)
                else:
                    # Es texto simple
                    self.whatsapp.send_text(number, response)

                # Pausa entre mensajes (excepto el último)
                if i < len(responses) - 1:
                    time.sleep(0.5)

            except Exception as e:
                print(f"❌ Error enviando respuesta {i+1}: {e}")

    def _save_interaction(self, context: MessageContext, responses: List[str]) -> None:
        """Guarda la interacción para analytics."""
        try:
            response_text = " | ".join(responses)
            guardar_interaccion(
                tipo=f"{context.message_type}-whatsapp",
                mensaje=context.text,
                respuesta=response_text,
                contexto=context.number
            )
        except Exception as e:
            print(f"⚠️ Error guardando interacción: {e}")
            
            
