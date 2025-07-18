"""
Servidor Flask principal para WhatsApp Bot de AVANS.
Versión refactorizada con separación de responsabilidades.
"""

import traceback
import logging
import sys
from flask import Flask, request, jsonify

# Importar configuraciones
import sett

# Importar el handler principal
from handlers.message_handler import MessageHandler

# Importar utilidades
from utils.validators import validate_whatsapp_message_format, validate_phone_number
from utils.helpers import replace_start, mask_sensitive_data

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Para caracteres especiales en JSON

# Inicializar el handler principal
message_handler = MessageHandler()

print("🔥 Flask cargado correctamente desde app.py")
logger.info("🔥 WhatsApp Bot iniciado correctamente")


@app.route("/")
def index():
    """
    Endpoint raíz para verificar que el servidor está funcionando.
    
    Returns:
        Mensaje de confirmación y código 200
    """
    return "✅ Flask + WSGI + Apache funcionando correctamente", 200


@app.route('/webhook/', methods=['GET'])
def verify_token():
    """
    Endpoint para verificación de webhook de WhatsApp.
    Meta requiere este endpoint para validar el webhook.
    
    Returns:
        Challenge string si el token es válido, error 403 si no
    """
    logger.info("📞 Verificación de token solicitada")
    
    try:
        # Obtener parámetros de verificación
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logger.info(f"Token recibido: {mask_sensitive_data(token or 'None')}")
        
        # Validar token
        if token == sett.token and challenge is not None:
            logger.info("✅ Token válido, devolviendo challenge")
            return challenge
        else:
            logger.warning("❌ Token inválido o challenge faltante")
            return 'Token incorrecto', 403
            
    except Exception as e:
        logger.error(f"❌ Error en verificación de token: {e}")
        return str(e), 403


@app.route('/webhook/', methods=['POST'])
def receive_messages():
    """
    Endpoint principal para recibir mensajes de WhatsApp.
    Procesa webhooks entrantes y los enruta al handler apropiado.
    
    Returns:
        Respuesta JSON indicando el estado del procesamiento
    """
    logger.info("📩 Webhook POST recibido")
    
    try:
        # Validar que el contenido sea JSON
        if not request.is_json:
            logger.warning("⚠️ Contenido recibido no es JSON válido")
            return jsonify({
                "status": "error",
                "message": "Contenido debe ser JSON válido"
            }), 400
        
        # Obtener body del request
        body = request.get_json()
        logger.info(f"📨 JSON recibido: {mask_sensitive_data(str(body))}")
        
        # Validar estructura básica del webhook
        validation_result = _validate_webhook_structure(body)
        if not validation_result["valid"]:
            logger.warning(f"⚠️ Estructura de webhook inválida: {validation_result['error']}")
            return jsonify({
                "status": "error",
                "message": validation_result["error"]
            }), 400
        
        # Extraer información del mensaje
        message_info = _extract_message_info(body)
        
        # Si no hay mensajes, probablemente es un evento de status
        if not message_info:
            logger.info("ℹ️ Webhook sin mensajes (probablemente evento de status)")
            return jsonify({
                "status": "success",
                "message": "Evento de status procesado"
            }), 200
        
        # Procesar mensaje con el handler
        _process_message_with_handler(message_info)
        
        logger.info("✅ Mensaje procesado correctamente")
        return jsonify({
            "status": "success",
            "message": "Mensaje procesado correctamente"
        }), 200
        
    except Exception as e:
        # Log completo del error
        error_details = traceback.format_exc()
        logger.error(f"❌ Error procesando webhook: {str(e)}")
        logger.error(f"❌ Traceback completo:\n{error_details}")
        
        return jsonify({
            "status": "error",
            "message": f"Error interno del servidor: {str(e)}"
        }), 500


def _validate_webhook_structure(body: dict) -> dict:
    """
    Valida la estructura básica del webhook de WhatsApp.
    
    Args:
        body: Body del webhook a validar
        
    Returns:
        Diccionario con resultado de validación
    """
    try:
        # Verificar que tenga entry
        if not isinstance(body.get("entry"), list) or len(body["entry"]) == 0:
            return {"valid": False, "error": "Entry está vacío o no es lista"}
        
        # Verificar primer entry
        first_entry = body["entry"][0]
        if not isinstance(first_entry.get("changes"), list) or len(first_entry["changes"]) == 0:
            return {"valid": False, "error": "Changes está vacío o no es lista"}
        
        # Verificar primer change
        change = first_entry["changes"][0]
        if not isinstance(change.get("value"), dict):
            return {"valid": False, "error": "Value no está presente o no es dict"}
        
        return {"valid": True, "error": None}
        
    except Exception as e:
        return {"valid": False, "error": f"Error validando estructura: {str(e)}"}


def _extract_message_info(body: dict) -> dict:
    """
    Extrae información relevante del mensaje del webhook.
    
    Args:
        body: Body del webhook
        
    Returns:
        Diccionario con información del mensaje o None si no hay mensajes
    """
    try:
        # Navegar por la estructura del webhook
        entry = body["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        
        # Verificar si hay mensajes
        messages = value.get("messages")
        if not isinstance(messages, list) or len(messages) == 0:
            logger.info("📭 No hay mensajes en el webhook")
            return None
        
        # Extraer información del primer mensaje
        message = messages[0]
        
        # Extraer datos del contacto
        contacts = value.get("contacts", [{}])
        contact = contacts[0] if contacts else {}
        
        # Limpiar y validar número de teléfono
        raw_number = message.get("from", "")
        clean_number = replace_start(raw_number)
        
        if not validate_phone_number(clean_number):
            logger.warning(f"⚠️ Número de teléfono inválido: {mask_sensitive_data(raw_number)}")
        
        # Validar formato del mensaje
        if not validate_whatsapp_message_format(message):
            logger.warning("⚠️ Formato de mensaje no válido")
        
        return {
            "raw_message": message,
            "message_id": message.get("id", ""),
            "from_number": clean_number,
            "contact_name": contact.get("profile", {}).get("name", "Usuario"),
            "timestamp": message.get("timestamp", ""),
            "message_type": message.get("type", "unknown")
        }
        
    except Exception as e:
        logger.error(f"❌ Error extrayendo información del mensaje: {e}")
        return None


def _process_message_with_handler(message_info: dict) -> None:
    """
    Procesa el mensaje usando el MessageHandler.
    
    Args:
        message_info: Información extraída del mensaje
    """
    try:
        # Log de información del mensaje (con datos enmascarados)
        masked_info = {
            "message_id": message_info["message_id"][:10] + "...",
            "from_number": mask_sensitive_data(message_info["from_number"]),
            "contact_name": message_info["contact_name"],
            "message_type": message_info["message_type"]
        }
        logger.info(f"🔄 Procesando mensaje: {masked_info}")
        
        # Llamar al handler principal
        message_handler.handle_message(
            raw_message=message_info["raw_message"],
            number=message_info["from_number"],
            message_id=message_info["message_id"],
            name=message_info["contact_name"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error en el handler de mensajes: {e}")
        # Re-lanzar la excepción para que sea manejada por el endpoint principal
        raise


@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado de salud del servicio.
    
    Returns:
        JSON con información del estado del sistema
    """
    try:
        # Verificar componentes principales
        health_status = {
            "status": "healthy",
            "timestamp": request.headers.get('X-Request-Start', 'unknown'),
            "components": {
                "flask": "ok",
                "message_handler": "ok" if message_handler else "error",
                "database": "unknown",  # Se podría agregar test de BD
                "ollama": "unknown",    # Se podría agregar test de Ollama
                "whatsapp_api": "unknown"  # Se podría agregar test de API
            }
        }
        
        # Determinar estado general
        component_statuses = list(health_status["components"].values())
        if "error" in component_statuses:
            health_status["status"] = "degraded"
            return jsonify(health_status), 503
        elif "unknown" in component_statuses:
            health_status["status"] = "partial"
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Endpoint para obtener estadísticas del bot (opcional).
    
    Returns:
        JSON con estadísticas básicas
    """
    try:
        # Obtener estadísticas básicas del handler
        stats = {
            "uptime": "unknown",  # Se podría calcular desde inicio
            "messages_processed": "unknown",  # Se podría agregar contador
            "active_sessions": message_handler.state_manager.get_active_users_count(),
            "version": "2.0.0-refactored"
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handler para errores 404."""
    return jsonify({
        "status": "error",
        "message": "Endpoint no encontrado"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handler para errores 405."""
    return jsonify({
        "status": "error",
        "message": "Método no permitido"
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handler para errores 500."""
    logger.error(f"❌ Error interno del servidor: {error}")
    return jsonify({
        "status": "error",
        "message": "Error interno del servidor"
    }), 500


if __name__ == '__main__':
    """
    Punto de entrada principal para desarrollo.
    En producción se debe usar un servidor WSGI como Gunicorn.
    """
    logger.info("🚀 Iniciando servidor Flask en modo desarrollo")
    
    # Configuración para desarrollo
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Mantener False en producción
        threaded=True
    )
else:
    """
    Configuración para producción con WSGI.
    """
    logger.info("🚀 Aplicación Flask cargada para producción (WSGI)")