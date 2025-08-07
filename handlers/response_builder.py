"""
Constructor de respuestas para mensajes de WhatsApp.
Centraliza la generación de diferentes tipos de mensajes y formatos.
"""

import json
from typing import List, Dict, Any, Optional


class ResponseBuilder:
    """
    Constructor centralizado de respuestas para WhatsApp.

    Responsabilidades:
    - Generar mensajes de texto estructurados
    - Crear mensajes interactivos (botones, listas)
    - Formatear datos de consultas de manera consistente
    - Mantener el estilo y tono de la marca
    """

    def __init__(self):
        self.brand_name = "AVANS"
        self.emoji_map = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "search": "🔍",
            "package": "📦",
            "order": "📄",
            "tools": "🛠️",
            "money": "💰",
            "truck": "🚚",
            "receipt": "🧾",
            "robot": "🤖",
            "brain": "🧠",
            "sparkles": "✨"
        }

    def build_main_menu(self, title: str = None, options: List[str] = None,
                       footer: str = None) -> str:
        """
        Construye el menú principal con botones interactivos.

        Args:
            title: Título del menú
            options: Lista de opciones para los botones
            footer: Texto del pie de página

        Returns:
            JSON string del mensaje interactivo
        """
        default_title = f"Hola, ¿en qué puedo ayudarte? {self.emoji_map['sparkles']}"
        default_options = ["Consultar Piezas", "Ver Estatus", "Consultar Órdenes"]
        default_footer = f"Equipo {self.brand_name}"

        title = title or default_title
        options = options or default_options
        footer = footer or default_footer

        buttons = []
        for i, option in enumerate(options[:3]):  # WhatsApp permite máximo 3 botones
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"menubtn{i+1}",
                    "title": option[:20]  # Límite de caracteres para botones
                }
            })

        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": title},
                "footer": {"text": footer},
                "action": {"buttons": buttons}
            }
        }

        return json.dumps(message, ensure_ascii=False)

    def build_yes_no_question(self, question: str, context: str = "general") -> str:
        """
        Construye una pregunta con botones Sí/No.

        Args:
            question: Pregunta a mostrar
            context: Contexto para identificar la respuesta

        Returns:
            JSON string del mensaje interactivo
        """
        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": question},
                "footer": {"text": f"Equipo {self.brand_name}"},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": f"{context}_yes", "title": "Sí"}
                        },
                        {
                            "type": "reply",
                            "reply": {"id": f"{context}_no", "title": "No"}
                        }
                    ]
                }
            }
        }

        return json.dumps(message, ensure_ascii=False)

    def build_orders_response(self, orders: List[Dict[str, Any]]) -> List[str]:
        """
        Construye respuesta de órdenes encontradas.

        Args:
            orders: Lista de órdenes

        Returns:
            Lista con las respuestas formateadas
        """
        if not orders:
            return ["📦 No se encontraron órdenes."]

        response = [f"📦 *Órdenes encontradas:* ({len(orders)})"]

        for i, order in enumerate(orders, 1):
            order_info = f"\n{i}. 📋 *Orden #{order.get('DocNum', 'N/A')}*"
            order_info += f"\n   👤 Cliente: {order.get('CardName', 'N/A')}"

            if order.get('PaidToDate'):
                order_info += f"\n   💰 Pagado: ${order['PaidToDate']}"
            if order.get('OINVToDate'):
                order_info += f"\n   🧾 Facturado: ${order['OINVToDate']}"
            if order.get('ODLNToDate'):
                order_info += f"\n   🚚 Entregado: ${order['ODLNToDate']}"

            response.append(order_info)

        return response

    def build_status_response(self, parts: List[Dict[str, Any]]) -> List[str]:
        """
        Construye respuesta formateada para consulta de estatus.

        Args:
            parts: Lista de piezas con información de estatus

        Returns:
            Lista de mensajes formateados
        """
        if not parts:
            return [f"{self.emoji_map['warning']} No se encontraron piezas para consultar estatus."]

        responses = []
        message = f"{self.emoji_map['tools']} *Estatus de piezas:*\n\n"

        for part in parts:
            status_info = self._format_part_status(part)
            message += f"{status_info}\n\n"

        responses.append(message.strip())
        return responses

    def build_order_response(self, order_data: Dict[str, Any]) -> List[str]:
        """
        Construye respuesta formateada para consulta de órdenes.

        Args:
            order_data: Datos de la orden

        Returns:
            Lista de mensajes formateados
        """
        if not order_data:
            return [f"{self.emoji_map['warning']} No se encontró información de la orden."]

        customer_name = order_data.get("CardName", "Cliente desconocido")
        paid = order_data.get("PaidToDate", "0%")
        invoiced = order_data.get("OINVToDate", "0%")
        delivered = order_data.get("ODLNToDate", "0%")

        message = f"{self.emoji_map['order']} *Información de Orden*\n\n"
        message += f"👤 *Cliente:* {customer_name}\n"
        message += f"{self.emoji_map['money']} *Pagado:* {paid}\n"
        message += f"{self.emoji_map['receipt']} *Facturado:* {invoiced}\n"
        message += f"{self.emoji_map['truck']} *Entregado:* {delivered}"

        return [message]

    def build_error_message(self, custom_message: str = None) -> str:
        """
        Construye mensaje de error estándar.

        Args:
            custom_message: Mensaje personalizado (opcional)

        Returns:
            Mensaje de error formateado
        """
        if custom_message:
            return f"{self.emoji_map['error']} {custom_message}"

        return (f"{self.emoji_map['error']} Ocurrió un error procesando tu consulta. "
                f"Escribe *hola* para volver al menú principal.")

    def build_timeout_message(self) -> str:
        """
        Construye mensaje de timeout de sesión.

        Returns:
            Mensaje de timeout formateado
        """
        return (f"{self.emoji_map['info']} Tu sesión ha expirado por inactividad. "
                f"Escribe *hola* para comenzar de nuevo.")

    def build_processing_message(self) -> str:
        """
        Construye mensaje de procesamiento.

        Returns:
            Mensaje de procesamiento
        """
        return f"{self.emoji_map['robot']} Procesando tu consulta, un momento por favor..."

    def build_help_message(self) -> str:
        """
        Construye mensaje de ayuda con comandos disponibles.

        Returns:
            Mensaje de ayuda completo
        """
        message = f"{self.emoji_map['info']} *Comandos disponibles:*\n\n"
        message += f"{self.emoji_map['search']} *consulta* - Buscar piezas por nombre o código\n"
        message += f"{self.emoji_map['tools']} *estatus* - Consultar estatus de piezas\n"
        message += f"{self.emoji_map['order']} *ordenes* - Consultar información de órdenes\n"
        message += f"{self.emoji_map['brain']} *memoria: [texto]* - Guardar conocimiento\n\n"
        message += f"💡 También puedes hacer preguntas libres sobre SAP y {self.brand_name}.\n\n"
        message += f"Escribe *hola* para volver al menú principal."

        return message

    def _format_single_part(self, part: Dict[str, Any]) -> str:
        """Formatea una sola pieza con detalles completos."""
        message = f"{self.emoji_map['package']} *{part.get('ItemName', 'Sin nombre')}*\n"
        message += f"🔢 *Código:* `{part.get('ItemCode', 'Sin código')}`\n"

        # Agregar disponibilidad si existe
        availability = part.get('availability', [])
        if availability:
            message += f"\n{self.emoji_map['info']} *Disponibilidad:*\n"
            for item in availability:
                warehouse = item.get('bodega', 'N/A')
                quantity = item.get('cantidad', 0)
                message += f"• {warehouse}: {quantity} unidades\n"
        else:
            message += f"\n{self.emoji_map['warning']} Sin stock disponible\n"

        return message.strip()

    def _format_part_summary(self, part: Dict[str, Any], index: int) -> str:
        """Formatea un resumen de pieza para listas."""
        name = part.get('ItemName', 'Sin nombre')
        code = part.get('ItemCode', 'Sin código')

        # Truncar nombre si es muy largo
        if len(name) > 30:
            name = name[:27] + "..."

        return f"{index}. *{name}* (`{code}`)"

    def _format_part_status(self, part: Dict[str, Any]) -> str:
        """Formatea información de estatus de una pieza."""
        name = part.get('ItemName', 'Sin nombre')
        code = part.get('ItemCode', 'Sin código')
        
        message = f"{self.emoji_map['package']} *{name}*\n"
        message += f"🔢 *Código:* `{code}`\n"
        
        # Información de disponibilidad (cantidad y bodega)
        availability = part.get('availability', [])
        if availability:
            message += f"📦 *Disponibilidad:*\n"
            for avail in availability:
                bodega = avail.get('bodega', 'N/A')
                cantidad = avail.get('cantidad', 0)
                message += f"   • {bodega}: {cantidad} unidades\n"
        else:
            # Información básica de la consulta principal
            on_hand = part.get('OnHand', 0)
            warehouse = part.get('DfltWH', 'N/A')
            if on_hand is not None:
                message += f"📦 *Disponible:* {on_hand} unidades\n"
                message += f"🏪 *Bodega:* {warehouse}\n"
            else:
                message += f"📦 *Disponibilidad:* Sin información\n"
        
        # Información de estatus
        status_info = part.get('status', {})
        if status_info:
            stage = status_info.get('ultima_etapa', 'Sin información')
            updated = status_info.get('fecha_actualizacion', 'N/A')
            message += f"📊 *Estatus:* {stage}\n"
            message += f"🕐 *Actualizado:* {updated}"
        else:
            # Usar información básica si no hay status detallado
            is_commited = part.get('IsCommited', 'N/A')
            updated = part.get('Updated', 'N/A')
            if is_commited is not None:
                status_text = "Disponible" if is_commited else "En proceso"
                message += f"📊 *Estatus:* {status_text}\n"
            if updated and updated != 'N/A':
                message += f"🕐 *Actualizado:* {updated}"
            else:
                message += f"{self.emoji_map['warning']} Sin información de estatus"
        
        return message

    def format_ai_response(self, response: str, source: str = "IA") -> str:
        """
        Formatea una respuesta de IA con el estilo de la marca.

        Args:
            response: Respuesta generada por IA
            source: Fuente de la respuesta (IA, BD, etc.)

        Returns:
            Respuesta formateada
        """
        if source.lower() == "ia":
            prefix = f"{self.emoji_map['robot']} *Asistente {self.brand_name}:*\n\n"
        elif source.lower() == "bd":
            prefix = f"{self.emoji_map['search']} *Base de Datos:*\n\n"
        else:
            prefix = f"{self.emoji_map['info']} *{source}:*\n\n"

        return f"{prefix}{response}"
