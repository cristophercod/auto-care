"""
services/vehicles.py
--------------------
Tudo que envolve VEÍCULOS no banco: cadastrar, listar, editar e excluir.
A interface (pasta ui/) nunca escreve SQL: ela chama estas funções.
"""
import sqlite3

from core.database import connection
from core.formatters import plate_display, vehicle_label
from core.validators import (ValidationError, run_checks, validate_km,
                             validate_plate, validate_text, validate_year)

FUEL_OPTIONS = ["Não informado", "Gasolina", "Etanol", "Flex", "Diesel", "GNV", "Elétrico", "Híbrido"]


def _clean(brand, model, year, plate, km, fuel) -> dict:
    """Valida os campos do formulário e devolve os dados prontos para salvar."""
    data = run_checks({
        "brand": lambda: validate_text(brand, "Marca", max_len=40),
        "model": lambda: validate_text(model, "Modelo", max_len=40),
        "year": lambda: validate_year(year),
        "plate": lambda: validate_plate(plate),
        "km": lambda: validate_km(km, "Quilometragem atual"),
    })
    data["fuel"] = None if (not fuel or fuel == "Não informado") else fuel
    return data


def _duplicate_plate_error(plate) -> ValidationError:
    return ValidationError(
        f"Já existe um veículo com a placa {plate_display(plate)}. "
        "Confira a placa digitada ou edite o veículo que já está cadastrado."
    )


def create_vehicle(brand, model, year, plate, km, fuel=None) -> int:
    data = _clean(brand, model, year, plate, km, fuel)
    try:
        with connection() as conn:
            cur = conn.execute(
                "INSERT INTO vehicles (brand, model, year, plate, current_km, fuel) VALUES (?,?,?,?,?,?)",
                (data["brand"], data["model"], data["year"], data["plate"], data["km"], data["fuel"]),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        raise _duplicate_plate_error(data["plate"])


def update_vehicle(vehicle_id, brand, model, year, plate, km, fuel=None) -> None:
    data = _clean(brand, model, year, plate, km, fuel)
    try:
        with connection() as conn:
            cur = conn.execute(
                "UPDATE vehicles SET brand=?, model=?, year=?, plate=?, current_km=?, fuel=? WHERE id=?",
                (data["brand"], data["model"], data["year"], data["plate"], data["km"], data["fuel"], vehicle_id),
            )
            if cur.rowcount == 0:
                raise ValidationError("Este veículo não existe mais. Atualize a lista e tente de novo.")
    except sqlite3.IntegrityError:
        raise _duplicate_plate_error(data["plate"])


def get_vehicle(vehicle_id):
    if vehicle_id is None:
        return None
    with connection() as conn:
        row = conn.execute("SELECT * FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
    return dict(row) if row else None


def list_vehicles(search: str = "") -> list:
    """Lista veículos; `search` procura em marca, modelo e placa."""
    sql, params = "SELECT * FROM vehicles", []
    search = (search or "").strip()
    if search:
        like = f"%{search}%"
        plate_like = "%" + search.replace("-", "").replace(" ", "").upper() + "%"
        sql += " WHERE brand LIKE ? OR model LIKE ? OR plate LIKE ?"
        params = [like, like, plate_like]
    sql += " ORDER BY brand COLLATE NOCASE, model COLLATE NOCASE"
    with connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def vehicle_choices() -> list:
    """Lista (texto, id) para usar nos menus de seleção: 'Fiat Uno — ABC-1234'."""
    return [(vehicle_label(v["brand"], v["model"], v["plate"]), v["id"]) for v in list_vehicles()]


def count_related(vehicle_id) -> tuple:
    """Quantas manutenções e revisões planejadas serão apagadas junto com o veículo."""
    with connection() as conn:
        done = conn.execute("SELECT COUNT(*) FROM maintenances WHERE vehicle_id=?", (vehicle_id,)).fetchone()[0]
        planned = conn.execute("SELECT COUNT(*) FROM scheduled_maintenances WHERE vehicle_id=?",
                               (vehicle_id,)).fetchone()[0]
    return done, planned


def delete_vehicle(vehicle_id) -> None:
    with connection() as conn:
        cur = conn.execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
        if cur.rowcount == 0:
            raise ValidationError("Este veículo não existe mais. Atualize a lista e tente de novo.")
