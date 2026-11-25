"""Ingesta y normalización de datos del INE Guatemala para el simulador de la CBA.

El paquete implementa tres reglas de rigor que la aplicación web hereda:

1. Los meses se ordenan cronológicamente a partir de su nombre en español
   (``Septiembre`` va antes que ``Octubre``), nunca alfabéticamente.
2. El costo mensual per cápita es ``costo diario × 30`` y luego se escala por el
   tamaño del hogar.
3. Las variaciones del IPC se toman del empalme oficial del INE; jamás se
   encadenan índices de bases distintas sin aplicar el factor de enlace.
"""

__version__ = "1.0.0"
