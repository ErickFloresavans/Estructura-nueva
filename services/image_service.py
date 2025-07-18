"""
Servicio para procesamiento y análisis de imágenes.
Maneja la descarga, procesamiento y análisis de imágenes enviadas por WhatsApp.
"""

import os
import time
from typing import Optional, Dict, Any
from services.whatsapp_service import WhatsAppService

# Intentar importar BLIP para análisis de imágenes
try:
    from blip_utils import describir_imagen
    BLIP_AVAILABLE = True
    print("✅ BLIP utils disponible para procesamiento de imágenes")
except ImportError:
    BLIP_AVAILABLE = False
    print("⚠️ BLIP utils no disponible - procesamiento de imágenes deshabilitado")


class ImageService:
    """
    Servicio centralizado para procesamiento de imágenes.
    
    Responsabilidades:
    - Verificar disponibilidad de procesamiento de imágenes
    - Descargar imágenes de WhatsApp
    - Procesar imágenes con BLIP
    - Gestionar archivos temporales
    - Generar descripciones de imágenes
    """
    
    def __init__(self):
        self.blip_available = BLIP_AVAILABLE
        self.whatsapp_service = WhatsAppService()
        
        # Configuración de directorios
        self.upload_dir = "static/uploads"
        self.temp_dir = "temp/images"
        
        # Crear directorios si no existen
        self._ensure_directories()
        
        # Configuración de archivos
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_formats = ['.jpg', '.jpeg', '.png', '.webp']
        self.cleanup_after_hours = 24  # Limpiar archivos después de 24 horas
    
    def is_available(self) -> bool:
        """
        Verifica si el procesamiento de imágenes está disponible.
        
        Returns:
            True si BLIP está disponible, False en caso contrario
        """
        return self.blip_available
    
    def analyze_image(self, media_id: str) -> Optional[str]:
        """
        Analiza una imagen completa desde media_id hasta descripción.
        
        Args:
            media_id: ID del archivo de media en WhatsApp
            
        Returns:
            Descripción de la imagen o None si hay error
        """
        if not self.blip_available:
            print("⚠️ BLIP no disponible para análisis de imagen")
            return None
        
        try:
            # 1. Obtener URL del archivo
            media_url = self.whatsapp_service.get_media_url(media_id)
            if not media_url:
                return None
            
            # 2. Generar nombre de archivo
            if custom_filename:
                filename = custom_filename
            else:
                timestamp = int(time.time())
                filename = f"img_{timestamp}.jpg"
            
            # 3. Ruta completa del archivo
            file_path = os.path.join(self.upload_dir, filename)
            
            # 4. Descargar archivo
            success = self.whatsapp_service.download_media(media_url, file_path)
            
            if success:
                print(f"✅ Imagen guardada: {file_path}")
                return file_path
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error descargando y guardando imagen: {e}")
            return None
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información básica de un archivo de imagen.
        
        Args:
            file_path: Ruta del archivo de imagen
            
        Returns:
            Diccionario con información del archivo
        """
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
            
            stat = os.stat(file_path)
            
            info = {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "extension": os.path.splitext(file_path)[1].lower(),
                "filename": os.path.basename(file_path)
            }
            
            # Verificar si es un formato soportado
            info["supported_format"] = info["extension"] in self.allowed_formats
            info["size_ok"] = stat.st_size <= self.max_file_size
            
            return info
            
        except Exception as e:
            print(f"❌ Error obteniendo info de imagen: {e}")
            return {"exists": False, "error": str(e)}
    
    def cleanup_old_images(self, max_age_hours: int = None) -> int:
        """
        Limpia imágenes antiguas de los directorios temporales.
        
        Args:
            max_age_hours: Edad máxima en horas (usa default si es None)
            
        Returns:
            Número de archivos eliminados
        """
        max_age = max_age_hours or self.cleanup_after_hours
        current_time = time.time()
        cutoff_time = current_time - (max_age * 3600)  # Convertir horas a segundos
        
        deleted_count = 0
        
        # Limpiar directorio temporal
        for directory in [self.temp_dir, self.upload_dir]:
            if not os.path.exists(directory):
                continue
                
            try:
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    
                    # Solo procesar archivos (no directorios)
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Verificar edad del archivo
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"🗑️ Imagen antigua eliminada: {filename}")
                        
            except Exception as e:
                print(f"❌ Error limpiando directorio {directory}: {e}")
        
        if deleted_count > 0:
            print(f"✅ Limpieza completada: {deleted_count} archivos eliminados")
        
        return deleted_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de almacenamiento de imágenes.
        
        Returns:
            Diccionario con estadísticas de almacenamiento
        """
        stats = {
            "upload_dir": self._get_directory_stats(self.upload_dir),
            "temp_dir": self._get_directory_stats(self.temp_dir),
            "blip_available": self.blip_available,
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "allowed_formats": self.allowed_formats
        }
        
        # Calcular totales
        total_files = stats["upload_dir"]["file_count"] + stats["temp_dir"]["file_count"]
        total_size = stats["upload_dir"]["total_size_mb"] + stats["temp_dir"]["total_size_mb"]
        
        stats["totals"] = {
            "total_files": total_files,
            "total_size_mb": round(total_size, 2)
        }
        
        return stats
    
    def _download_image(self, media_url: str) -> Optional[str]:
        """
        Descarga una imagen a directorio temporal.
        
        Args:
            media_url: URL del archivo de media
            
        Returns:
            Ruta del archivo descargado o None si hay error
        """
        try:
            # Generar nombre temporal único
            timestamp = int(time.time())
            filename = f"temp_img_{timestamp}.jpg"
            file_path = os.path.join(self.temp_dir, filename)
            
            # Descargar archivo
            success = self.whatsapp_service.download_media(media_url, file_path)
            
            if success:
                return file_path
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error descargando imagen temporal: {e}")
            return None
    
    def _process_image_with_blip(self, image_path: str) -> Optional[str]:
        """
        Procesa una imagen usando BLIP para generar descripción.
        
        Args:
            image_path: Ruta del archivo de imagen
            
        Returns:
            Descripción de la imagen o None si hay error
        """
        if not self.blip_available:
            return None
        
        try:
            # Verificar que el archivo existe
            if not os.path.exists(image_path):
                print(f"❌ Archivo de imagen no encontrado: {image_path}")
                return None
            
            # Procesar con BLIP
            description = describir_imagen(image_path)
            
            if description and description.strip():
                print(f"✅ Imagen procesada con BLIP: {description[:50]}...")
                return description.strip()
            else:
                print("⚠️ BLIP no generó descripción")
                return None
                
        except Exception as e:
            print(f"❌ Error procesando imagen con BLIP: {e}")
            return None
    
    def _cleanup_file(self, file_path: str) -> bool:
        """
        Elimina un archivo específico.
        
        Args:
            file_path: Ruta del archivo a eliminar
            
        Returns:
            True si se eliminó exitosamente, False en caso contrario
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Archivo temporal eliminado: {os.path.basename(file_path)}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error eliminando archivo {file_path}: {e}")
            return False
    
    def _ensure_directories(self) -> None:
        """Crea los directorios necesarios si no existen."""
        for directory in [self.upload_dir, self.temp_dir]:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Directorio asegurado: {directory}")
            except Exception as e:
                print(f"❌ Error creando directorio {directory}: {e}")
    
    def _get_directory_stats(self, directory: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un directorio específico.
        
        Args:
            directory: Ruta del directorio
            
        Returns:
            Diccionario con estadísticas del directorio
        """
        if not os.path.exists(directory):
            return {
                "exists": False,
                "file_count": 0,
                "total_size_mb": 0,
                "files": []
            }
        
        try:
            files = []
            total_size = 0
            
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    file_size = stat.st_size
                    total_size += file_size
                    
                    files.append({
                        "name": filename,
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2),
                        "modified": stat.st_mtime
                    })
            
            return {
                "exists": True,
                "file_count": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files": sorted(files, key=lambda x: x["modified"], reverse=True)
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas de {directory}: {e}")
            return {
                "exists": True,
                "file_count": 0,
                "total_size_mb": 0,
                "files": [],
                "error": str(e)
            }

            # 1. Obtener URL del archivo
            media_url = self.whatsapp_service.get_media_url(media_id)
            if not media_url:
                print("❌ No se pudo obtener URL de la imagen")
                return None
            
            # 2. Descargar imagen
            image_path = self._download_image(media_url)
            if not image_path:
                print("❌ No se pudo descargar la imagen")
                return None
            
            # 3. Procesar imagen con BLIP
            description = self._process_image_with_blip(image_path)
            
            # 4. Limpiar archivo temporal (opcional, inmediato)
            self._cleanup_file(image_path)
            
            return description
            
        except Exception as e:
            print(f"❌ Error analizando imagen: {e}")
            return None
    
    def download_and_save_image(self, media_id: str, custom_filename: str = None) -> Optional[str]:
        """
        Descarga y guarda una imagen permanentemente.
        
        Args:
            media_id: ID del archivo de media en WhatsApp
            custom_filename: Nombre personalizado para el archivo
            
        Returns:
            Ruta del archivo guardado o None si hay error
        """
        try: