"""
core/formatters.py
------------------
Funções que transformam dados do banco em texto bonito para a tela
(Heurística 2: linguagem do mundo real - R$, km, dd/mm/aaaa).
"""
from datetime import date, datetime


def money(value) -> str:
    """1234.5 -> 'R$ 1.234,50'"""
    value = float(value or 0)
    text = f"{value:,.2f}"                                   # 1,234.50
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def km(value) -> str:
    """45000 -> '45.000 km'"""
    if value is None:
        return "—"
    return f"{int(value):,}".replace(",", ".") + " km"


def date_br(value) -> str:
    """'2026-03-15' (ou date) -> '15/03/2026'"""
    if not value:
        return "—"
    if isinstance(value, str):
        value = datetime.strptime(value, "%Y-%m-%d").date()
    return value.strftime("%d/%m/%Y")


def plate_display(plate: str) -> str:
    """ABC1234 -> ABC-1234 (modelo antigo). Mercosul (ABC1D23) fica igual."""
    if plate and len(plate) == 7 and plate[4].isdigit():
        return f"{plate[:3]}-{plate[3:]}"
    return plate


def vehicle_label(brand, model, plate) -> str:
    """'Fiat Uno — ABC-1234'"""
    return f"{brand} {model} — {plate_display(plate)}"


def today() -> date:
    return date.today()
