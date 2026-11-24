"""
services/maintenances.py
------------------------
Manutenções JÁ REALIZADAS: cadastrar, consultar (com filtros), editar e excluir.
"""
from core.database import connection
from core.formatters import today, vehicle_label
from core.validators import (ValidationError, parse_date, run_checks, validate_km,
                             validate_money, validate_text)
from services.vehicles import get_vehicle

# Sugestões comuns. O usuário também pode digitar outro tipo no próprio menu.
COMMON_SERVICE_TYPES = [
    "Troca de óleo", "Filtros", "Pneus", "Freios", "Revisão geral", "Bateria",
    "Suspensão", "Alinhamento e balanceamento", "Correia dentada", "Outro",
]


def _require_vehicle(vehicle_id) -> int:
    if vehicle_id is None:
        raise ValidationError("Escolha o veículo no menu «Veículo».")
    if get_vehicle(vehicle_id) is None:
        raise ValidationError("O veículo escolhido não existe mais. Escolha outro no menu «Veículo».")
    return int(vehicle_id)


def _service_date(text):
    parsed = parse_date(text, "Data da manutenção")
    if parsed > today():
        raise ValidationError(
            "A data da manutenção não pode estar no futuro. "
            "Para planejar uma revisão futura, use a tela «Próximas revisões»."
        )
    return parsed


def _clean(vehicle_id, service_type, description, date_text, km, cost, workshop) -> dict:
    return run_checks({
        "vehicle_id": lambda: _require_vehicle(vehicle_id),
        "service_type": lambda: validate_text(service_type, "Tipo de manutenção", max_len=50),
        "description": lambda: validate_text(description, "Descrição do serviço", min_len=3, max_len=300),
        "date": lambda: _service_date(date_text),
        "km": lambda: validate_km(km, "Quilometragem no serviço"),
        "cost": lambda: validate_money(cost),
        "workshop": lambda: validate_text(workshop, "Oficina", required=False, max_len=80),
    })


def _raise_vehicle_km_if_higher(conn, vehicle_id, km) -> bool:
    """Se o serviço foi feito com km maior que a atual do veículo, atualiza o veículo."""
    cur = conn.execute("UPDATE vehicles SET current_km=? WHERE id=? AND current_km<?", (km, vehicle_id, km))
    return cur.rowcount > 0


def create_maintenance(vehicle_id, service_type, description, date_text, km, cost, workshop=None) -> dict:
    d = _clean(vehicle_id, service_type, description, date_text, km, cost, workshop)
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO maintenances (vehicle_id, service_type, description, service_date, km, cost, workshop)"
            " VALUES (?,?,?,?,?,?,?)",
            (d["vehicle_id"], d["service_type"], d["description"], d["date"].isoformat(),
             d["km"], d["cost"], d["workshop"]),
        )
        km_updated = _raise_vehicle_km_if_higher(conn, d["vehicle_id"], d["km"])
    return {"id": cur.lastrowid, "km_updated": km_updated, "km": d["km"]}


def update_maintenance(maintenance_id, vehicle_id, service_type, description, date_text, km, cost,
                       workshop=None) -> dict:
    d = _clean(vehicle_id, service_type, description, date_text, km, cost, workshop)
    with connection() as conn:
        cur = conn.execute(
            "UPDATE maintenances SET vehicle_id=?, service_type=?, description=?, service_date=?,"
            " km=?, cost=?, workshop=? WHERE id=?",
            (d["vehicle_id"], d["service_type"], d["description"], d["date"].isoformat(),
             d["km"], d["cost"], d["workshop"], maintenance_id),
        )
        if cur.rowcount == 0:
            raise ValidationError("Este registro não existe mais. Atualize a lista e tente de novo.")
        km_updated = _raise_vehicle_km_if_higher(conn, d["vehicle_id"], d["km"])
    return {"id": maintenance_id, "km_updated": km_updated, "km": d["km"]}


def delete_maintenance(maintenance_id) -> None:
    with connection() as conn:
        cur = conn.execute("DELETE FROM maintenances WHERE id=?", (maintenance_id,))
        if cur.rowcount == 0:
            raise ValidationError("Este registro não existe mais. Atualize a lista e tente de novo.")


def get_maintenance(maintenance_id):
    if maintenance_id is None:
        return None
    with connection() as conn:
        row = conn.execute("SELECT * FROM maintenances WHERE id=?", (maintenance_id,)).fetchone()
    return dict(row) if row else None


def list_maintenances(vehicle_id=None, service_type=None, date_from=None, date_to=None, search=None) -> list:
    """Lista manutenções, da mais recente para a mais antiga, aplicando os filtros informados."""
    sql = ("SELECT m.*, v.brand, v.model, v.plate FROM maintenances m "
           "JOIN vehicles v ON v.id = m.vehicle_id WHERE 1=1")
    params = []
    if vehicle_id is not None:
        sql += " AND m.vehicle_id = ?"
        params.append(vehicle_id)
    if service_type:
        sql += " AND m.service_type = ? COLLATE NOCASE"
        params.append(service_type)
    if date_from:
        sql += " AND m.service_date >= ?"
        params.append(date_from.isoformat())
    if date_to:
        sql += " AND m.service_date <= ?"
        params.append(date_to.isoformat())
    if search and search.strip():
        like = f"%{search.strip()}%"
        sql += " AND (m.description LIKE ? OR m.workshop LIKE ? OR m.service_type LIKE ?)"
        params += [like, like, like]
    sql += " ORDER BY m.service_date DESC, m.id DESC"
    with connection() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    for r in rows:
        r["vehicle_label"] = vehicle_label(r["brand"], r["model"], r["plate"])
    return rows


def recorded_service_types() -> list:
    """Tipos de serviço que realmente existem nos registros (para o filtro do histórico)."""
    with connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT service_type FROM maintenances ORDER BY service_type COLLATE NOCASE").fetchall()
    return [r[0] for r in rows]


def service_type_choices() -> list:
    """Sugestões comuns + tipos personalizados que o usuário já usou."""
    known = {t.lower() for t in COMMON_SERVICE_TYPES}
    extra = [t for t in recorded_service_types() if t.lower() not in known]
    return COMMON_SERVICE_TYPES + extra
