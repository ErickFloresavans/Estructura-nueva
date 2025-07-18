"""
Servicio para comunicación con WhatsApp Business API.
Maneja el envío de mensajes y la interacción con la API de Meta.
"""

import json
import requests
from typing import Dict, List, Optional, Union
import sett  # Configuraciones originales


class WhatsAppService:
    """
    Servicio centralizado para comunicación con WhatsApp Business API.
    
    Responsabilidades:
    - Enviar mensajes de texto simple
    - Enviar mensajes interactivos (botones, listas)
    - Marcar mensajes como leídos
    - Manejar errores de API
    - Validar formatos de mensaje
    """
    
    def __init__(self):
        self.api_url = sett.whatsapp_url
        self.access_token = sett.whatsapp_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
    
    def send_text(self, number: str, text: str) -> bool:
        """
        Envía un mensaje de texto simple a un número de WhatsApp.
        
        Args:
            number: Número de teléfono del destinatario
            text: Texto del mensaje a enviar
            
        Returns:
            True si el mensaje se envió exitosamente, False en caso contrario
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {"body": text}
        }
        
        return self._send_message(payload)
    
    def send_interactive_message(self, number: str, interactive_json: str) -> bool:
        """
        Envía un mensaje interactivo (puede ser JSON string o dict).
        
        Args:
            number: Número de teléfono del destinatario
            interactive_json: JSON del mensaje interactivo o dict
            
        Returns:
            True si el mensaje se envió exitosamente, False en caso contrario
        """
        try:
            # Si es string, parsearlo; si es dict, usarlo directamente
            if isinstance(interactive_json, str):
                payload = json.loads(interactive_json)
            else:
                payload = interactive_json
            
            # Asegurar que tenga el número correcto
            payload["to"] = number
            
            return self._send_message(payload)
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON interactivo: {e}")
            return False
    
    def send_button_message(self, number: str, body_text: str, buttons: List[str], 
                           footer: str = "", button_id_prefix: str = "btn") -> bool:
        """
        Envía un mensaje con botones de manera simplificada.
        
        Args:
            number: Número de teléfono del destinatario
            body_text: Texto principal del mensaje
            buttons: Lista de textos para los botones (máximo 3)
            footer: Texto del pie de página (opcional)
            button_id_prefix: Prefijo para los IDs de botones
            
        Returns:
            True si el mensaje se envió exitosamente, False en caso contrario
        """
        if len(buttons) > 3:
            print("⚠️ WhatsApp permite máximo 3 botones, truncando lista")
            buttons = buttons[:3]
        
        button_objects = []
        for i, button_text in enumerate(buttons):
            button_objects.append({
                "type": "reply",
                "reply": {
                    "id": f"{button_id_prefix}{i+1}",
                    "title": button_text[:20]  # Límite de caracteres
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": button_objects}
            }
        }
        
        if footer:
            payload["interactive"]["footer"] = {"text": footer}
        
        return self._send_message(payload)
    
    def send_list_message(self, number: str, body_text: str, button_text: str,
                         sections: List[Dict], footer: str = "") -> bool:
        """
        Envía un mensaje con lista desplegable.
        
        Args:
            number: Número de teléfono del destinatario
            body_text: Texto principal del mensaje
            button_text: Texto del botón para abrir la lista
            sections: Secciones de la lista con sus opciones
            footer: Texto del pie de página (opcional)
            
        Returns:
            True si el mensaje se envió exitosamente, False en caso contrario
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        
        if footer:
            payload["interactive"]["footer"] = {"text": footer}
        
        return self._send_message(payload)
    
    def mark_message_read(self, message_id: str) -> bool:
        """
        Marca un mensaje como leído.
        
        Args:
            message_id: ID del mensaje a marcar como leído
            
        Returns:
            True si se marcó exitosamente, False en caso contrario
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        return self._send_message(payload)
    
    def send_media_message(self, number: str, media_type: str, media_url: str,
                          caption: str = "") -> bool:
        """
        Envía un mensaje con media (imagen, documento, etc.).
        
        Args:
            number: Número de teléfono del destinatario
            media_type: Tipo de media (image, document, audio, video)
            media_url: URL del archivo de media
            caption: Descripción del media (opcional)
            
        Returns:
            True si el mensaje se envió exitosamente, False en caso contrario
        """
        media_object = {"link": media_url}
        
        if caption and media_type in ["image", "document", "video"]:
            media_object["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": media_type,
            media_type: media_object
        }
        
        return self._send_message(payload)
    
    def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Obtiene la URL de un archivo de media usando su ID.
        
        Args:
            media_id: ID del archivo de media
            
        Returns:
            URL del archivo o None si hay error
        """
        try:
            url = f"https://graph.facebook.com/v22.0/{media_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            else:
                print(f"❌ Error obteniendo URL de media: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error en get_media_url: {e}")
            return None
    
    def download_media(self, media_url: str, save_path: str) -> bool:
        """
        Descarga un archivo de media y lo guarda localmente.
        
        Args:
            media_url: URL del archivo de media
            save_path: Ruta donde guardar el archivo
            
        Returns:
            True si se descargó exitosamente, False en caso contrario
        """
        try:
            response = requests.get(media_url, headers=self.headers, 
                                  stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                
                print(f"✅ Media descargado: {save_path}")
                return True
            else:
                print(f"❌ Error descargando media: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error en download_media: {e}")
            return False
    
    def _send_message(self, payload: Dict) -> bool:
        """
        Método interno para enviar cualquier tipo de mensaje.
        
        Args:
            payload: Payload del mensaje según API de WhatsApp
            
        Returns:
            True si el mensaje se envió exitosamente, False en caso contrario
        """
        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload,
                timeout=15
            )
            
            # Log para debugging
            print(f"[📤 WHATSAPP] Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"[📤 WHATSAPP] Mensaje enviado exitosamente")
                print(f"[📤 WHATSAPP] Response: {response_data}")
                return True
            else:
                print(f"❌ Error enviando mensaje: {response.status_code}")
                print(f"❌ Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Timeout enviando mensaje a WhatsApp")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con WhatsApp: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado enviando mensaje: {e}")
            return False
    
    def validate_phone_number(self, number: str) -> bool:
        """
        Valida el formato de un número de teléfono.
        
        Args:
            number: Número a validar
            
        Returns:
            True si el formato es válido, False en caso contrario
        """
        # Básicamente debe ser numérico y tener longitud apropiada
        if not number.isdigit():
            return False
        
        # Longitud típica para números internacionales (10-15 dígitos)
        if len(number) < 10 or len(number) > 15:
            return False
        
        return True
    
    def get_api_health(self) -> Dict[str, Union[bool, str]]:
        """
        Verifica el estado de la API de WhatsApp.
        
        Returns:
            Diccionario con información del estado de la API
        """
        try:
            # Intentar hacer una request simple para verificar conectividad
            test_url = "https://graph.facebook.com/v22.0/me"
            response = requests.get(test_url, headers=self.headers, timeout=10)
            
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "message": "API disponible" if response.status_code == 200 else "API no disponible"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status_code": 0,
                "message": f"Error de conectividad: {e}"
            }