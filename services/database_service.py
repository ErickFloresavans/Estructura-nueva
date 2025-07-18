"""
Servicio centralizado para todas las operaciones de base de datos.
Maneja consultas a MySQL y procesamiento de consultas automáticas.
"""

from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import pymysql
from sett import get_mysql_connection
from consultas_automaticas import procesar_consulta_automatica


class DatabaseService:
    """
    Servicio centralizado para operaciones de base de datos.
    
    Responsabilidades:
    - Consultas de piezas e inventario
    - Consultas de órdenes y estatus
    - Procesamiento de consultas automáticas
    - Manejo de conexiones y errores
    - Cache de consultas frecuentes
    """
    
    def __init__(self):
        self._connection_pool = None
        self._query_cache = {}
        self.cache_timeout = 300  # 5 minutos
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener conexiones de base de datos.
        
        Yields:
            Conexión a la base de datos MySQL
        """
        connection = None
        try:
            connection = get_mysql_connection()
            yield connection
        except Exception as e:
            print(f"❌ Error de conexión a BD: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    def search_parts(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca piezas por nombre o código con información de disponibilidad.
        
        Args:
            search_term: Término de búsqueda (nombre o código)
            limit: Número máximo de resultados
            
        Returns:
            Lista de piezas con información de disponibilidad
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Buscar piezas por nombre o código
                    query = """
                        SELECT id, ItemName, ItemCode
                        FROM avans_articulos_inventariables_accesos
                        WHERE ItemName LIKE %s OR ItemCode LIKE %s
                        ORDER BY IsCommited DESC
                        LIMIT %s
                    """
                    
                    search_pattern = f"%{search_term}%"
                    cursor.execute(query, (search_pattern, search_pattern, limit))
                    parts = cursor.fetchall()
                    
                    # Enriquecer cada pieza con información de disponibilidad
                    enriched_parts = []
                    for part in parts:
                        part_with_availability = dict(part)
                        part_with_availability['availability'] = self._get_part_availability(part['id'])
                        enriched_parts.append(part_with_availability)
                    
                    return enriched_parts
                    
        except Exception as e:
            print(f"❌ Error buscando piezas: {e}")
            return []
    
    def search_parts_for_status(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca piezas por nombre o código con información de estatus.
        
        Args:
            search_term: Término de búsqueda (nombre o código)
            limit: Número máximo de resultados
            
        Returns:
            Lista de piezas con información de estatus
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Buscar piezas por nombre o código
                    query = """
                        SELECT id, ItemName, ItemCode
                        FROM avans_articulos_inventariables_accesos
                        WHERE ItemName LIKE %s OR ItemCode LIKE %s
                        LIMIT %s
                    """
                    
                    search_pattern = f"%{search_term}%"
                    cursor.execute(query, (search_pattern, search_pattern, limit))
                    parts = cursor.fetchall()
                    
                    # Enriquecer cada pieza con información de estatus
                    enriched_parts = []
                    for part in parts:
                        part_with_status = dict(part)
                        part_with_status['status'] = self._get_part_status(part['id'])
                        enriched_parts.append(part_with_status)
                    
                    return enriched_parts
                    
        except Exception as e:
            print(f"❌ Error buscando piezas para estatus: {e}")
            return []
    
    def get_order_data(self, order_number: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información detallada de una orden específica.
        
        Args:
            order_number: Número de la orden a consultar
            
        Returns:
            Diccionario con datos de la orden o None si no existe
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT CardName, PaidToDate, OINVToDate, ODLNToDate
                        FROM avans_ordr_accesos
                        WHERE DocNum = %s
                    """
                    
                    cursor.execute(query, (order_number,))
                    result = cursor.fetchone()
                    
                    return dict(result) if result else None
                    
        except Exception as e:
            print(f"❌ Error obteniendo datos de orden {order_number}: {e}")
            return None
    
    def process_automatic_query(self, query_text: str) -> Optional[str]:
        """
        Procesa una consulta automática usando el sistema existente.
        
        Args:
            query_text: Texto de la consulta del usuario
            
        Returns:
            Resultado de la consulta automática o None si no aplica
        """
        try:
            return procesar_consulta_automatica(query_text)
        except Exception as e:
            print(f"❌ Error en consulta automática: {e}")
            return None
    
    def get_inventory_summary(self, warehouse: str = None) -> Dict[str, Any]:
        """
        Obtiene un resumen del inventario por almacén.
        
        Args:
            warehouse: Almacén específico (opcional)
            
        Returns:
            Diccionario con estadísticas de inventario
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if warehouse:
                        query = """
                            SELECT 
                                DfltWH as warehouse,
                                COUNT(*) as total_items,
                                SUM(OnHand) as total_quantity,
                                AVG(OnHand) as avg_quantity
                            FROM avans_articulos_inventariables_accesos
                            WHERE DfltWH = %s
                            GROUP BY DfltWH
                        """
                        cursor.execute(query, (warehouse,))
                    else:
                        query = """
                            SELECT 
                                DfltWH as warehouse,
                                COUNT(*) as total_items,
                                SUM(OnHand) as total_quantity,
                                AVG(OnHand) as avg_quantity
                            FROM avans_articulos_inventariables_accesos
                            GROUP BY DfltWH
                        """
                        cursor.execute(query)
                    
                    results = cursor.fetchall()
                    
                    summary = {
                        'warehouses': [dict(row) for row in results],
                        'total_warehouses': len(results)
                    }
                    
                    if not warehouse:
                        # Agregar totales generales
                        total_items = sum(w['total_items'] for w in summary['warehouses'])
                        total_quantity = sum(w['total_quantity'] for w in summary['warehouses'])
                        
                        summary['grand_total'] = {
                            'total_items': total_items,
                            'total_quantity': total_quantity,
                            'avg_quantity': total_quantity / total_items if total_items > 0 else 0
                        }
                    
                    return summary
                    
        except Exception as e:
            print(f"❌ Error obteniendo resumen de inventario: {e}")
            return {}
    
    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las órdenes más recientes.
        
        Args:
            limit: Número máximo de órdenes a retornar
            
        Returns:
            Lista de órdenes recientes
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT DocNum, CardName, PaidToDate, OINVToDate, ODLNToDate
                        FROM avans_ordr_accesos
                        ORDER BY DocNum DESC
                        LIMIT %s
                    """
                    
                    cursor.execute(query, (limit,))
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            print(f"❌ Error obteniendo órdenes recientes: {e}")
            return []
    
    def search_orders_by_client(self, client_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca órdenes por nombre de cliente.
        
        Args:
            client_name: Nombre del cliente a buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de órdenes del cliente
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT DocNum, CardName, PaidToDate, OINVToDate, ODLNToDate
                        FROM avans_ordr_accesos
                        WHERE CardName LIKE %s
                        ORDER BY DocNum DESC
                        LIMIT %s
                    """
                    
                    search_pattern = f"%{client_name}%"
                    cursor.execute(query, (search_pattern, limit))
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            print(f"❌ Error buscando órdenes por cliente: {e}")
            return []
    
    def _get_part_availability(self, part_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene la disponibilidad de una pieza específica por almacén.
        
        Args:
            part_id: ID de la pieza
            
        Returns:
            Lista de disponibilidad por almacén
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT DfltWH as bodega, OnHand as cantidad
                        FROM avans_articulos_inventariables_accesos
                        WHERE id = %s
                    """
                    
                    cursor.execute(query, (part_id,))
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            print(f"❌ Error obteniendo disponibilidad para pieza {part_id}: {e}")
            return []
    
    def _get_part_status(self, part_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estatus de una pieza específica.
        
        Args:
            part_id: ID de la pieza
            
        Returns:
            Diccionario con información de estatus o None
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT IsCommited as ultima_etapa, Updated as fecha_actualizacion
                        FROM avans_articulos_inventariables_accesos
                        WHERE id = %s
                    """
                    
                    cursor.execute(query, (part_id,))
                    result = cursor.fetchone()
                    
                    return dict(result) if result else None
                    
        except Exception as e:
            print(f"❌ Error obteniendo estatus para pieza {part_id}: {e}")
            return None
    
    def get_low_stock_items(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene elementos con stock bajo.
        
        Args:
            threshold: Umbral para considerar stock bajo
            
        Returns:
            Lista de elementos con stock bajo
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT id, ItemName, ItemCode, OnHand, DfltWH
                        FROM avans_articulos_inventariables_accesos
                        WHERE OnHand <= %s AND OnHand >= 0
                        ORDER BY OnHand ASC
                    """
                    
                    cursor.execute(query, (threshold,))
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results]
                    
        except Exception as e:
            print(f"❌ Error obteniendo elementos con stock bajo: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de la base de datos.
        
        Returns:
            Diccionario con estadísticas de la BD
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    
                    # Contar total de piezas
                    cursor.execute("SELECT COUNT(*) as total FROM avans_articulos_inventariables_accesos")
                    stats['total_parts'] = cursor.fetchone()['total']
                    
                    # Contar total de órdenes
                    cursor.execute("SELECT COUNT(*) as total FROM avans_ordr_accesos")
                    stats['total_orders'] = cursor.fetchone()['total']
                    
                    # Contar almacenes únicos
                    cursor.execute("SELECT COUNT(DISTINCT DfltWH) as total FROM avans_articulos_inventariables_accesos")
                    stats['total_warehouses'] = cursor.fetchone()['total']
                    
                    # Cantidad total en stock
                    cursor.execute("SELECT SUM(OnHand) as total FROM avans_articulos_inventariables_accesos WHERE OnHand > 0")
                    result = cursor.fetchone()
                    stats['total_stock_quantity'] = result['total'] if result['total'] else 0
                    
                    return stats
                    
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas de BD: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """
        Prueba la conectividad con la base de datos.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            print(f"❌ Error probando conexión BD: {e}")
            return False