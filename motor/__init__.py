"""Motor Atlas: planeador de viajes TransMilenio.

Contrato público: from motor import Red, simular_fila
"""

from .fila import simular_fila
from .red import Red

__all__ = ["Red", "simular_fila"]
