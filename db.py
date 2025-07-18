# db.py
import json
import sqlite3
import time
from datetime import datetime


def conectar_db():
    return sqlite3.connect("inventario.db", timeout=10, check_same_thread=False)

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        marca TEXT NOT NULL,
        cantidad INTEGER NOT NULL
    )
    """)
    # Datos de prueba
    cursor.executemany("""
    INSERT INTO inventario (nombre, marca, cantidad) VALUES (?, ?, ?)
    """, [
        ("puerta", "bone", 15),
        ("ventana", "glassco", 6),
        ("puerta", "inox", 8),
    ])
    conn.commit()
    conn.close()

def inicializar_interacciones():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                mensaje TEXT,
                contexto TEXT,
                respuesta TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    
def guardar_interaccion(tipo, mensaje, respuesta, contexto=None):
    entrada = {
        "tipo": tipo,
        "mensaje": mensaje,
        "respuesta": respuesta,
        "contexto": contexto,
        "fecha": datetime.now().isoformat()
    }

    try:
        with open("interacciones_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        print("✅ Interacción guardada en interacciones_log.jsonl")
    except Exception as e:
        print("❌ ERROR grave al guardar interacción en archivo:", e)
