"""
Funciones de validación para diferentes tipos de datos.
Centraliza la lógica de validación para mantener consistencia.
"""

import re
from typing import Any, List, Dict, Optional, Union


def validate_order_number(value: Any) -> bool:
    """
    Valida que un valor sea un número de orden válido.
    
    Args:
        value: Valor a validar
        
    Returns:
        True si es un número de orden válido
    """
    try:
        # Convertir a string y limpiar
        str_value = str(value).strip()
        
        # Debe ser numérico
        if not str_value.isdigit():
            return False
        
        # Convertir a entero
        int_value = int(str_value)
        
        # Debe estar en un rango razonable (1 a 999999999)
        return 1 <= int_value <= 999999999
        
    except (ValueError, TypeError):
        return False


def validate_phone_number(phone: str) -> bool:
    """
    Valida formato de número de teléfono.
    
    Args:
        phone: Número de teléfono a validar
        
    Returns:
        True si el formato es válido
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Limpiar número (remover espacios, guiones, paréntesis)
    clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Debe ser solo dígitos
    if not clean_phone.isdigit():
        return False
    
    # Longitud apropiada para números internacionales
    return 10 <= len(clean_phone) <= 15


def validate_part_code(code: str) -> bool:
    """
    Valida formato de código de pieza.
    
    Args:
        code: Código de pieza a validar
        
    Returns:
        True si el formato es válido
    """
    if not code or not isinstance(code, str):
        return False
    
    code = code.strip().upper()
    
    # Debe tener al menos 3 caracteres
    if len(code) < 3:
        return False
    
    # Patrones comunes de códigos de piezas
    patterns = [
        r'^[A-Z]{2,4}-?\d{2,8}$',    # ABC-1234, ABCD1234
        r'^\d{3,8}-[A-Z]{1,4}$',     # 1234-A, 123456-ABC
        r'^[A-Z]\d{4,10}$',          # A12345, B123456
        r'^\d{4,12}$',               # 123456789 (solo números)
        r'^[A-Z]{1,3}\d{2,6}[A-Z]{0,2}$'  # A12B, ABC123XY
    ]
    
    return any(re.match(pattern, code) for pattern in patterns)


def validate_part_name(name: str) -> bool:
    """
    Valida nombre de pieza.
    
    Args:
        name: Nombre de pieza a validar
        
    Returns:
        True si el nombre es válido
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # Debe tener al menos 2 caracteres
    if len(name) < 2:
        return False
    
    # No debe ser solo números
    if name.isdigit():
        return False
    
    # Debe contener al menos una letra
    if not re.search(r'[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]', name):
        return False
    
    return True


def validate_search_term(term: str) -> bool:
    """
    Valida término de búsqueda general.
    
    Args:
        term: Término de búsqueda
        
    Returns:
        True si el término es válido para búsqueda
    """
    if not term or not isinstance(term, str):
        return False
    
    # Limpiar término
    clean_term = term.strip()
    
    # Debe tener al menos 2 caracteres
    if len(clean_term) < 2:
        return False
    
    # No debe ser solo espacios o caracteres especiales
    if re.match(r'^[\s\W]*$', clean_term):
        return False
    
    return True


def validate_warehouse_code(warehouse: str) -> bool:
    """
    Valida código de almacén.
    
    Args:
        warehouse: Código de almacén
        
    Returns:
        True si el código es válido
    """
    if not warehouse or not isinstance(warehouse, str):
        return False
    
    warehouse = warehouse.strip().upper()
    
    # Debe tener entre 1 y 10 caracteres
    if not 1 <= len(warehouse) <= 10:
        return False
    
    # Solo letras, números y algunos caracteres especiales
    if not re.match(r'^[A-Z0-9\-_]+$', warehouse):
        return False
    
    return True


def validate_quantity(quantity: Any) -> bool:
    """
    Valida cantidad de inventario.
    
    Args:
        quantity: Cantidad a validar
        
    Returns:
        True si la cantidad es válida
    """
    try:
        # Convertir a float para manejar decimales
        qty = float(quantity)
        
        # Debe ser no negativo y menor a un valor razonable
        return 0 <= qty <= 999999
        
    except (ValueError, TypeError):
        return False


def validate_message_id(message_id: str) -> bool:
    """
    Valida ID de mensaje de WhatsApp.
    
    Args:
        message_id: ID del mensaje
        
    Returns:
        True si el ID es válido
    """
    if not message_id or not isinstance(message_id, str):
        return False
    
    # Debe tener longitud razonable para IDs de WhatsApp
    if not 10 <= len(message_id) <= 100:
        return False
    
    # Solo caracteres alfanuméricos, guiones y puntos
    if not re.match(r'^[A-Za-z0-9\-_\.]+$', message_id):
        return False
    
    return True


def validate_user_input_length(text: str, min_length: int = 1, max_length: int = 1000) -> bool:
    """
    Valida longitud de input de usuario.
    
    Args:
        text: Texto a validar
        min_length: Longitud mínima
        max_length: Longitud máxima
        
    Returns:
        True si la longitud está en el rango válido
    """
    if not isinstance(text, str):
        return False
    
    return min_length <= len(text.strip()) <= max_length


def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Valida que un diccionario tenga los campos requeridos.
    
    Args:
        data: Diccionario a validar
        required_fields: Lista de campos requeridos
        
    Returns:
        True si tiene todos los campos requeridos
    """
    if not isinstance(data, dict):
        return False
    
    return all(field in data for field in required_fields)


def validate_whatsapp_message_format(message: Dict[str, Any]) -> bool:
    """
    Valida que un mensaje tenga el formato correcto de WhatsApp API.
    
    Args:
        message: Mensaje a validar
        
    Returns:
        True si el formato es válido
    """
    if not isinstance(message, dict):
        return False
    
    # Debe tener tipo de mensaje
    if "type" not in message:
        return False
    
    message_type = message["type"]
    
    # Validar según tipo de mensaje
    if message_type == "text":
        return "text" in message and "body" in message["text"]
    
    elif message_type == "button":
        return "button" in message
    
    elif message_type == "interactive":
        return "interactive" in message
    
    elif message_type in ["image", "document", "audio", "video"]:
        return message_type in message
    
    return True


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Valida que un archivo tenga una extensión permitida.
    
    Args:
        filename: Nombre del archivo
        allowed_extensions: Lista de extensiones permitidas (ej: ['.jpg', '.png'])
        
    Returns:
        True si la extensión está permitida
    """
    if not filename or not isinstance(filename, str):
        return False
    
    # Obtener extensión
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Agregar punto si no lo tiene
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    
    return extension in [ext.lower() for ext in allowed_extensions]


def validate_date_format(date_string: str, format_pattern: str = r'^\d{4}-\d{2}-\d{2}') -> bool:
    """
    Valida formato de fecha.
    
    Args:
        date_string: String de fecha a validar
        format_pattern: Patrón regex para validar formato
        
    Returns:
        True si el formato es válido
    """
    if not date_string or not isinstance(date_string, str):
        return False
    
    return bool(re.match(format_pattern, date_string.strip()))


def validate_pagination_params(page: Any, limit: Any, max_limit: int = 100) -> tuple:
    """
    Valida y normaliza parámetros de paginación.
    
    Args:
        page: Número de página
        limit: Límite de elementos por página
        max_limit: Límite máximo permitido
        
    Returns:
        Tupla (page_valid, limit_valid, page_int, limit_int)
    """
    try:
        # Validar página
        page_int = int(page) if page is not None else 1
        page_valid = page_int >= 1
        
        # Validar límite
        limit_int = int(limit) if limit is not None else 10
        limit_valid = 1 <= limit_int <= max_limit
        
        return page_valid, limit_valid, page_int, limit_int
        
    except (ValueError, TypeError):
        return False, False, 1, 10


def validate_sql_injection_risk(text: str) -> bool:
    """
    Detecta posibles intentos de inyección SQL.
    
    Args:
        text: Texto a validar
        
    Returns:
        True si el texto parece seguro, False si hay riesgo
    """
    if not text or not isinstance(text, str):
        return True  # Texto vacío es seguro
    
    # Patrones sospechosos de SQL injection
    dangerous_patterns = [
        r'\b(union|select|insert|update|delete|drop|create|alter)\b',
        r'[\'\"]\s*;\s*[\'\"]*',
        r'--',
        r'/\*.*\*/',
        r'\bor\s+[\'\"]*\d+[\'\"]*\s*=\s*[\'\"]*\d+',
        r'\band\s+[\'\"]*\d+[\'\"]*\s*=\s*[\'\"]*\d+'
    ]
    
    text_lower = text.lower()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            return False
    
    return True


def validate_business_rule_order_status(status: str) -> bool:
    """
    Valida que un estatus de orden sea válido según reglas de negocio.
    
    Args:
        status: Estatus a validar
        
    Returns:
        True si el estatus es válido
    """
    valid_statuses = [
        'pending', 'confirmed', 'in_progress', 'shipped', 
        'delivered', 'cancelled', 'returned'
    ]
    
    return status.lower() in valid_statuses


def validate_inventory_movement_type(movement_type: str) -> bool:
    """
    Valida tipo de movimiento de inventario.
    
    Args:
        movement_type: Tipo de movimiento
        
    Returns:
        True si el tipo es válido
    """
    valid_types = [
        'entry', 'exit', 'transfer', 'adjustment', 
        'return', 'loss', 'found'
    ]
    
    return movement_type.lower() in valid_types


def sanitize_search_input(search_term: str) -> str:
    """
    Limpia y sanitiza input de búsqueda.
    
    Args:
        search_term: Término de búsqueda original
        
    Returns:
        Término de búsqueda sanitizado
    """
    if not search_term or not isinstance(search_term, str):
        return ""
    
    # Limpiar término
    sanitized = search_term.strip()
    
    # Remover caracteres peligrosos
    sanitized = re.sub(r'[<>&"\';]', '', sanitized)
    
    # Limitar longitud
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    # Remover múltiples espacios
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    return sanitized


def validate_api_response_format(response: Dict[str, Any]) -> bool:
    """
    Valida formato de respuesta de API externa.
    
    Args:
        response: Respuesta de API a validar
        
    Returns:
        True si el formato es válido
    """
    if not isinstance(response, dict):
        return False
    
    # Debe tener al menos status o algún indicador de éxito/error
    required_indicators = ['status', 'success', 'error', 'data']
    
    return any(indicator in response for indicator in required_indicators)


class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


def validate_and_raise(value: Any, validator_func: callable, 
                      error_message: str, field_name: str = None) -> Any:
    """
    Valida un valor y lanza excepción si es inválido.
    
    Args:
        value: Valor a validar
        validator_func: Función de validación
        error_message: Mensaje de error si la validación falla
        field_name: Nombre del campo (opcional)
        
    Returns:
        El valor original si es válido
        
    Raises:
        ValidationError: Si la validación falla
    """
    if not validator_func(value):
        raise ValidationError(error_message, field_name, value)
    
    return value


def validate_batch(values: List[Any], validator_func: callable) -> List[bool]:
    """
    Valida una lista de valores usando la misma función de validación.
    
    Args:
        values: Lista de valores a validar
        validator_func: Función de validación
        
    Returns:
        Lista de booleanos indicando qué valores son válidos
    """
    return [validator_func(value) for value in values]


def get_validation_summary(validations: Dict[str, bool]) -> Dict[str, Any]:
    """
    Genera un resumen de múltiples validaciones.
    
    Args:
        validations: Diccionario con nombre_campo: resultado_validacion
        
    Returns:
        Diccionario con resumen de validaciones
    """
    total_fields = len(validations)
    valid_fields = sum(validations.values())
    invalid_fields = [field for field, valid in validations.items() if not valid]
    
    return {
        "total_fields": total_fields,
        "valid_fields": valid_fields,
        "invalid_fields": invalid_fields,
        "success_rate": (valid_fields / total_fields * 100) if total_fields > 0 else 0,
        "all_valid": len(invalid_fields) == 0
    }