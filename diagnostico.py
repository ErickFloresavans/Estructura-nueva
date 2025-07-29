import json
import sys
import traceback

# Simula la variable que te da error
# 👇 Sustituye esta línea por tu variable real
response = '{"data": {"nombre": "Sergio"}}'  # ← puede ser str o dict, edítalo tú

print("✅ Tipo detectado:")
print(type(response))

print("\n📦 Contenido:")
print(response)

# Intenta convertir si es string JSON
if isinstance(response, str):
    try:
        print("\n🔄 Intentando convertir con json.loads...")
        response = json.loads(response)
        print("✅ Conversión exitosa. Nuevo tipo:", type(response))
    except Exception as e:
        print("❌ Error al hacer json.loads:")
        traceback.print_exc()
        sys.exit(1)

# Prueba de acceso por clave
try:
    print("\n🔍 Accediendo a clave 'data'...")
    data = response.get("data")
    print("✅ data:", data)
except Exception as e:
    print("❌ Error accediendo a .get('data'):")
    traceback.print_exc()

# Prueba de acceso encadenado
try:
    print("\n📥 Accediendo a data['nombre']...")
    nombre = data["nombre"]
    print("✅ nombre:", nombre)
except Exception as e:
    print("❌ Error accediendo a data['nombre']:")
    traceback.print_exc()
