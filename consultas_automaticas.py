# consultas_automaticas.py
"""
Sistema de consultas automáticas a la base de datos
Detecta intenciones del usuario y consulta la BD sin botones
"""

import re
from sett import get_mysql_connection

def detectar_intencion_consulta(texto):
    """
    Detecta automáticamente si el usuario quiere consultar algo en la BD
    """
    # Patrones para detectar consultas de piezas
    patrones_pieza = [
        r'(?:pieza|parte|componente|item|artículo)\s+(\w+)',
        r'código\s+(\w+)',
        r'disponibilidad\s+(?:de\s+)?(\w+)',
        r'stock\s+(?:de\s+)?(\w+)',
        r'inventario\s+(?:de\s+)?(\w+)',
        r'cuánto[as]?\s+(?:tenemos|hay)\s+(?:de\s+)?(\w+)',
        r'buscar\s+(\w+)',
        r'(\w+)\s+disponible',
        r'tenemos\s+(\w+)',
        r'hay\s+(\w+)',
        r'mostrar\s+(\w+)',
        r'información\s+(?:de\s+)?(\w+)'
    ]
    
    # Patrones para detectar consultas de órdenes
    patrones_orden = [
        r'orden\s+(\d+)',
        r'pedido\s+(\d+)',
        r'número\s+(\d+)',
        r'estado\s+(?:de\s+)?(?:orden\s+)?(\d+)',
        r'facturación\s+(\d+)',
        r'entrega\s+(\d+)',
        r'consultar\s+(\d+)',
        r'ver\s+orden\s+(\d+)'
    ]
    
    # Patrones para detectar consultas de estatus
    patrones_estatus = [
        r'estatus\s+(?:de\s+)?(\w+)',
        r'estado\s+(?:de\s+)?(\w+)',
        r'situación\s+(?:de\s+)?(\w+)',
        r'cómo\s+está\s+(\w+)',
        r'actualización\s+(?:de\s+)?(\w+)',
        r'proceso\s+(?:de\s+)?(\w+)'
    ]
    
    texto_lower = texto.lower()
    
    # Buscar patrones de piezas
    for patron in patrones_pieza:
        match = re.search(patron, texto_lower)
        if match:
            return {"tipo": "pieza", "termino": match.group(1), "texto_original": texto}
    
    # Buscar patrones de órdenes
    for patron in patrones_orden:
        match = re.search(patron, texto_lower)
        if match:
            return {"tipo": "orden", "numero": match.group(1), "texto_original": texto}
    
    # Buscar patrones de estatus
    for patron in patrones_estatus:
        match = re.search(patron, texto_lower)
        if match:
            return {"tipo": "estatus", "termino": match.group(1), "texto_original": texto}
    
    return None

def buscar_piezas_auto(termino):
    """Función auxiliar para buscar piezas"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, ItemName, ItemCode
                FROM avans_articulos_inventariables_accesos
                WHERE ItemName LIKE %s OR ItemCode LIKE %s
                ORDER BY IsCommited DESC
                LIMIT 10
            """, (f"%{termino}%", f"%{termino}%"))
            return cursor.fetchall()

def obtener_disponibilidad_auto(item_id):
    """Función auxiliar para obtener disponibilidad"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DfltWH AS bodega, OnHand AS cantidad
                FROM avans_articulos_inventariables_accesos
                WHERE id = %s
            """, (item_id,))
            return cursor.fetchall()

def obtener_datos_orden_auto(docnum):
    """Función auxiliar para obtener datos de orden"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT CardName, PaidToDate, OINVToDate, ODLNToDate
                FROM avans_ordr_accesos
                WHERE DocNum = %s
            """, (docnum,))
            return cursor.fetchone()

def obtener_estatus_auto(item_id):
    """Función auxiliar para obtener estatus"""
    with get_mysql_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT IsCommited AS ultima_etapa, Updated AS fecha_actualizacion
                FROM avans_articulos_inventariables_accesos
                WHERE id = %s
            """, (item_id,))
            return cursor.fetchone()

def consulta_automatica_pieza(termino):
    """
    Realiza consulta automática de piezas y devuelve resultado formateado
    """
    try:
        resultados = buscar_piezas_auto(termino)
        if not resultados:
            return f"❌ No encontré ninguna pieza con '{termino}' en el sistema."
        
        if len(resultados) == 1:
            # Una sola pieza - mostrar detalles completos
            pieza = resultados[0]
            disponibilidad = obtener_disponibilidad_auto(pieza["id"])
            
            respuesta = f"📦 *{pieza['ItemName']}*\n🔢 Código: `{pieza['ItemCode']}`"
            
            if disponibilidad:
                respuesta += "\n🧮 *Disponibilidad:*"
                for d in disponibilidad:
                    respuesta += f"\n- {d['bodega']}: {d['cantidad']} unidades"
            else:
                respuesta += "\n❌ Sin stock disponible"
                
            return respuesta
        else:
            # Múltiples piezas - mostrar resumen
            respuesta = f"🔍 Encontré {len(resultados)} piezas relacionadas con '{termino}':\n\n"
            for i, pieza in enumerate(resultados[:5]):  # Máximo 5
                respuesta += f"{i+1}. *{pieza['ItemName']}* (`{pieza['ItemCode']}`)\n"
            
            if len(resultados) > 5:
                respuesta += f"\n... y {len(resultados) - 5} más."
                
            return respuesta
            
    except Exception as e:
        print(f"❌ Error en consulta automática de pieza: {e}")
        return f"⚠️ Error consultando '{termino}'. Intenta con el menú principal."

def consulta_automatica_orden(numero):
    """
    Realiza consulta automática de órdenes
    """
    try:
        datos = obtener_datos_orden_auto(int(numero))
        if not datos:
            return f"❌ No encontré la orden número {numero} en el sistema."
        
        nombre_cliente = datos.get("CardName", "Cliente desconocido")
        pagado = datos.get("PaidToDate", "0%")
        facturado = datos.get("OINVToDate", "0%")
        entregado = datos.get("ODLNToDate", "0%")
        
        respuesta = f"📄 *Orden #{numero} - {nombre_cliente}*\n"
        respuesta += f"💰 Pagado: *{pagado}*\n"
        respuesta += f"🧾 Facturado: *{facturado}*\n"
        respuesta += f"🚚 Entregado: *{entregado}*"
        
        return respuesta
        
    except ValueError:
        return f"⚠️ '{numero}' no es un número de orden válido."
    except Exception as e:
        print(f"❌ Error en consulta automática de orden: {e}")
        return f"⚠️ Error consultando orden {numero}."

def consulta_automatica_estatus(termino):
    """
    Realiza consulta automática de estatus
    """
    try:
        resultados = buscar_piezas_auto(termino)
        if not resultados:
            return f"❌ No encontré ninguna pieza '{termino}' para consultar estatus."
        
        if len(resultados) == 1:
            pieza = resultados[0]
            estatus = obtener_estatus_auto(pieza["id"])
            
            respuesta = f"📦 *{pieza['ItemName']}*\n🔢 Código: `{pieza['ItemCode']}`"
            
            if estatus:
                respuesta += f"\n📄 Estatus: *{estatus['ultima_etapa']}*"
                respuesta += f"\n🕓 Actualizado: {estatus['fecha_actualizacion']}"
            else:
                respuesta += "\n⚠️ Sin información de estatus"
                
            return respuesta
        else:
            return f"🔍 Encontré {len(resultados)} piezas con '{termino}'. Especifica más para ver el estatus."
            
    except Exception as e:
        print(f"❌ Error en consulta automática de estatus: {e}")
        return f"⚠️ Error consultando estatus de '{termino}'."

def procesar_consulta_automatica(texto):
    """
    Función principal que procesa una consulta automática
    Devuelve el resultado de la BD o None si no detecta consulta
    """
    intencion = detectar_intencion_consulta(texto)
    
    if not intencion:
        return None
    
    print(f"[🎯 CONSULTA AUTO] Detectado: {intencion['tipo']} - {intencion.get('termino', intencion.get('numero'))}")
    
    if intencion["tipo"] == "pieza":
        return consulta_automatica_pieza(intencion["termino"])
    elif intencion["tipo"] == "orden":
        return consulta_automatica_orden(intencion["numero"])
    elif intencion["tipo"] == "estatus":
        return consulta_automatica_estatus(intencion["termino"])
    
    return None
