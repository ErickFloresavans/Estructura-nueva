# test_handler.py

from handlers.message_handler import MessageHandler, MessageContext

def simular_mensaje(texto, estado=None):
    print("\n==============================")
    print(f"📨 Simulando mensaje: {texto}")
    
    # Crear un mensaje simulado
    context = MessageContext(
        text=texto,
        number="5215555555555",
        message_id="wamid.TEST123456",
        name="Erick",
        message_type="text",
        raw_message={
            "type": "text",
            "text": {
                "body": texto
            }
        }
    )

    # Instanciar handler
    handler = MessageHandler()

    # Opcional: forzar estado si se desea simular flujo intermedio
    if estado:
        handler.state_manager.set_state(context.number, estado)

    # Ejecutar el manejador de mensaje
    responses = handler.handle_message(context.raw_message, context.number, context.message_id, context.name)

    print(f"📤 Respuestas: {responses}")
    print("==============================\n")


if __name__ == "__main__":
    # 1. Simula mensaje inicial "consulta"
    simular_mensaje("consulta")

    # 2. Simula respuesta con pieza
    simular_mensaje("resistor 10k", estado="AWAITING_PART_SEARCH")
