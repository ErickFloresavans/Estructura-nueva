#!/bin/bash
echo "🧹 Eliminando prints anteriores..."
sed -i '/print("🧠 Consultando RAG/d' handlers/message_handler.py

echo "🧠 Reinserción solo en _handle_part_search..."
awk '
/def _handle_part_search/ {in_func=1}
/^    def / && $0 !~ /_handle_part_search/ {in_func=0}
in_func && /if not parts:/ {
    print $0
    print "        print(\"🧠 Consultando RAG por falta de resultados en BD\")"
    next
}
{print}
' handlers/message_handler.py > handlers/message_handler_temp.py && mv handlers/message_handler_temp.py handlers/message_handler.py

echo "✅ Hecho. Verificando inserción..."
grep -n "print(\"🧠 Consultando RAG" handlers/message_handler.py
