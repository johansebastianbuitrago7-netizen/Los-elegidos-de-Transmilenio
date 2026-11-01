"""Contrato público del planeador; solo biblioteca estándar permitida."""
from .red import Red
from .simulacion import simular_fila

__all__ = ['Red', 'simular_fila']
