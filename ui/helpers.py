"""
ui/helpers.py
-------------
Pequenas funções reutilizadas por várias telas.
"""
import gradio as gr

from core.formatters import date_br, today
from services import vehicles as vehicles_svc

ALL_VEHICLES = 0          # valor do item "Todos os veículos" nos filtros
ALL_TYPES = "Todos os tipos"


def today_br() -> str:
    """Data de hoje no formato dd/mm/aaaa (valor inicial dos campos de data)."""
    return date_br(today())


def vehicle_dropdown_update(current, with_all=False):
    """
    Recarrega a lista de veículos de um menu. Mantém o item escolhido se ele ainda existir
    (evita erro quando o veículo foi excluído em outra tela).
    """
    choices = vehicles_svc.vehicle_choices()
    if with_all:
        choices = [("Todos os veículos", ALL_VEHICLES)] + choices
    valid = {value for _, value in choices}
    default = ALL_VEHICLES if with_all else None
    return gr.update(choices=choices, value=current if current in valid else default)
