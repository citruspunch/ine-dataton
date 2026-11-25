# Uso de inteligencia artificial en el desarrollo

## En el producto

Ninguno. El prototipo no incluye modelos, prompts, agentes ni servicios de IA en
tiempo de ejecución:

- El motor (`engine/`) es determinista y no hace llamadas de red.
- El servidor MCP no contiene un LLM: expone dos herramientas tipadas de lectura.
- La interfaz no envía datos a terceros.

## En el desarrollo

Se usaron asistentes de código (OpenCode con modelos de la familia DeepSeek y
otros) para redactar y revisar código, pruebas y documentación. El criterio de
uso fue:

1. **Verificación contra la fuente.** Toda cifra del producto (por ejemplo
   `+0,501463 %`, base 2024=100) se comprobó contra el XLSX oficial del INE y
   contra el boletín, no contra la salida del asistente.
2. **Pruebas como contrato.** Cada regla tiene casos positivos y negativos en
   `tests/`; un cambio que rompe una regla falla la suite.
3. **Revisión humana del alcance.** Las decisiones de producto (qué se bloquea,
   qué se publica, qué lenguaje se evita) son del equipo y están en el PRD.

## Qué no se delegó

- La interpretación metodológica del empalme del IPC y del cambio de base.
- La redacción de los límites y advertencias del producto.
- La decisión de qué agregados se habilitan: eso es el gate humano, registrado
  con responsable y motivo en `stores/review_store/decisions/`.
