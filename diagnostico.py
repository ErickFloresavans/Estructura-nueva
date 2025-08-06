import sys
import traceback
from consultas_automaticas import buscar_piezas_auto  # 👈 reemplaza por el nombre real del archivo

def ejecutar_diagnostico(termino):
    try:
        print(f"🔍 Buscando piezas con el término: '{termino}'...")
        resultados = buscar_piezas_auto(termino)

        if resultados:
            print(f"✅ Se encontraron {len(resultados)} resultados:\n")
            for row in resultados:
                print(f"🧩 ID: {row['id']} | Nombre: {row['ItemName']} | Código: {row['ItemCode']}")

        else:
            print("⚠️ No se encontraron coincidencias.")

    except Exception as e:
        print("❌ Error durante la búsqueda:")
        traceback.print_exc()

if __name__ == "__main__":
    termino = sys.argv[1] if len(sys.argv) > 1 else "motor"
    ejecutar_diagnostico(termino)
