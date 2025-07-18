"""
Funciones auxiliares y utilidades generales.
Contiene funciones reutilizables para procesamiento de datos.
"""

import re
import time
from typing import Dict, Any, Optional, List, Union


def extract_text_from_message(message: Dict[str, Any]) -> str:
    """
    Extrae texto de diferentes tipos de mensajes de WhatsApp.
    
    Args:
        message: Mensaje de WhatsApp según API
        
    Returns:
        Texto extraído del mensaje en minúsculas
    """
    message_type = message.get("type", "")
    
    if message_type == "text":
        return message.get("text", {}).get("body", "").lower()
    
    elif message_type == "button":
        # Priorizar payload sobre text
        button_data = message.get("button", {})
        return (button_data.get("payload") or 
                button_data.get("text", "mensaje no procesado")).lower()
    
    elif message_type == "interactive":
        interactive = message.get("interactive", {})
        
        if interactive.get("type") == "list_reply":
            return interactive.get("list_reply", {}).get("title", "").lower()
        
        elif interactive.get("type") == "button_reply":
            return interactive.get("button_reply", {}).get("title", "").lower()
    
    elif message_type == "image":
        return "imagen"
    
    elif message_type == "document":
        return "documento"
    
    elif message_type == "audio":
        return "audio"
    
    elif message_type == "video":
        return "video"
    
    return "mensaje no procesado"


def replace_start(phone_number: str) -> str:
    """
    Ajusta el formato de números de teléfono para diferentes países.
    
    Args:
        phone_number: Número de teléfono original
        
    Returns:
        Número de teléfono ajustado
    """
    if phone_number.startswith("521"):
        # México: remover el 1 extra
        return "52" + phone_number[3:]
    elif phone_number.startswith("549"):
        # Argentina: remover el 9 extra
        return "54" + phone_number[3:]
    else:
        return phone_number


def clean_text_for_processing(text: str) -> str:
    """
    Limpia texto para procesamiento más efectivo.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio y normalizado
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Convertir a minúsculas
    cleaned = text.lower().strip()
    
    # Remover caracteres especiales excesivos
    cleaned = re.sub(r'[^\w\s\-_.áéíóúñü]', ' ', cleaned)
    
    # Normalizar espacios
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remover acentos para búsquedas más flexibles (opcional)
    accent_map = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    
    for accented, plain in accent_map.items():
        cleaned = cleaned.replace(accented, plain)
    
    return cleaned.strip()


def format_timestamp(timestamp: float, format_type: str = "datetime") -> str:
    """
    Formatea un timestamp a string legible.
    
    Args:
        timestamp: Timestamp en segundos
        format_type: Tipo de formato ('datetime', 'date', 'time', 'relative')
        
    Returns:
        String formateado
    """
    try:
        if format_type == "datetime":
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        
        elif format_type == "date":
            return time.strftime("%Y-%m-%d", time.localtime(timestamp))
        
        elif format_type == "time":
            return time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        elif format_type == "relative":
            current_time = time.time()
            diff = current_time - timestamp
            
            if diff < 60:
                return f"hace {int(diff)} segundos"
            elif diff < 3600:
                return f"hace {int(diff/60)} minutos"
            elif diff < 86400:
                return f"hace {int(diff/3600)} horas"
            else:
                return f"hace {int(diff/86400)} días"
        
        else:
            return str(timestamp)
            
    except Exception:
        return "fecha inválida"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima permitida
        suffix: Sufijo a agregar si se trunca
        
    Returns:
        Texto truncado
    """
    if not text or len(text) <= max_length:
        return text
    
    # Buscar el último espacio dentro del límite para no cortar palabras
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.7:  # Solo si no corta demasiado
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_numbers_from_text(text: str) -> List[str]:
    """
    Extrae todos los números de un texto.
    
    Args:
        text: Texto del cual extraer números
        
    Returns:
        Lista de números encontrados como strings
    """
    if not text:
        return []
    
    # Buscar números (enteros y decimales)
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
    return numbers


def extract_codes_from_text(text: str) -> List[str]:
    """
    Extrae códigos alfanuméricos típicos (como códigos de piezas).
    
    Args:
        text: Texto del cual extraer códigos
        
    Returns:
        Lista de códigos encontrados
    """
    if not text:
        return []
    
    # Patrones comunes para códigos de piezas
    patterns = [
        r'\b[A-Z]{2,4}-?\d{2,6}\b',  # ABC-1234, ABCD1234
        r'\b\d{3,6}-[A-Z]{1,3}\b',   # 1234-A, 123456-ABC
        r'\b[A-Z]\d{4,8}\b',         # A12345, B123456
        r'\b\d{6,10}\b'              # Códigos numéricos largos
    ]
    
    codes = []
    for pattern in patterns:
        matches = re.findall(pattern, text.upper())
        codes.extend(matches)
    
    # Remover duplicados manteniendo orden
    unique_codes = []
    for code in codes:
        if code not in unique_codes:
            unique_codes.append(code)
    
    return unique_codes


def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        True si el formato es válido
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza un nombre de archivo removiendo caracteres problemáticos.
    
    Args:
        filename: Nombre de archivo original
        
    Returns:
        Nombre de archivo sanitizado
    """
    if not filename:
        return "archivo"
    
    # Remover caracteres problemáticos
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remover espacios múltiples y puntos múltiples
    sanitized = re.sub(r'\.{2,}', '.', sanitized)
    sanitized = re.sub(r'\s+', '_', sanitized)
    
    # Limitar longitud
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:95] + ext
    
    return sanitized


def parse_user_input_list(text: str, separator: str = ",") -> List[str]:
    """
    Parsea una lista de elementos desde input de usuario.
    
    Args:
        text: Texto con elementos separados
        separator: Separador de elementos
        
    Returns:
        Lista de elementos limpios
    """
    if not text:
        return []
    
    # Dividir por separador y limpiar cada elemento
    items = []
    for item in text.split(separator):
        cleaned_item = item.strip()
        if cleaned_item:  # Solo agregar elementos no vacíos
            items.append(cleaned_item)
    
    return items


def get_file_size_human(size_bytes: int) -> str:
    """
    Convierte tamaño en bytes a formato legible.
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        Tamaño en formato legible (KB, MB, GB)
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def mask_sensitive_data(text: str, mask_char: str = "*") -> str:
    """
    Enmascara datos sensibles en texto para logging seguro.
    
    Args:
        text: Texto que puede contener datos sensibles
        mask_char: Carácter para enmascarar
        
    Returns:
        Texto con datos sensibles enmascarados
    """
    if not text:
        return text
    
    masked = text
    
    # Enmascarar números de teléfono
    masked = re.sub(r'\b\d{10,15}\b', lambda m: m.group()[:3] + mask_char * (len(m.group()) - 6) + m.group()[-3:], masked)
    
    # Enmascarar emails
    masked = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                   lambda m: m.group()[:2] + mask_char * 5 + m.group()[-4:], masked)
    
    # Enmascarar tokens largos (posibles API keys)
    masked = re.sub(r'\b[A-Za-z0-9]{20,}\b', 
                   lambda m: m.group()[:4] + mask_char * 8 + m.group()[-4:], masked)
    
    return masked


def build_cache_key(*args) -> str:
    """
    Construye una clave de cache a partir de argumentos.
    
    Args:
        *args: Argumentos para construir la clave
        
    Returns:
        Clave de cache como string
    """
    # Convertir todos los argumentos a string y limpiar
    key_parts = []
    for arg in args:
        if arg is not None:
            clean_arg = str(arg).replace(" ", "_").replace(":", "_")
            key_parts.append(clean_arg)
    
    return "_".join(key_parts)


def is_business_hours(timezone_offset: int = -6) -> bool:
    """
    Verifica si es horario de oficina (9 AM - 6 PM, lunes a viernes).
    
    Args:
        timezone_offset: Diferencia horaria en horas (México = -6)
        
    Returns:
        True si es horario de oficina
    """
    try:
        # Obtener hora local ajustada
        current_time = time.time() + (timezone_offset * 3600)
        local_time = time.localtime(current_time)
        
        # Verificar día de la semana (0=lunes, 6=domingo)
        weekday = local_time.tm_wday
        hour = local_time.tm_hour
        
        # Lunes a viernes (0-4) y horario 9-18
        return weekday < 5 and 9 <= hour < 18
        
    except Exception:
        return True  # Asumir horario de oficina en caso de error