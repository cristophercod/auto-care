"""
services/schedules.py
---------------------
PRÓXIMAS REVISÕES: o usuário informa o serviço, a data e/ou a quilometragem prevista.
O sistema compara com a data de hoje e com a km atual do veículo para classificar:

    atrasada  -> a data já passou OU a km atual já chegou na km prevista
    proxima   -> está dentro da margem de aviso (padrão 30 dias / 1.000 km)
    no_prazo  -> ainda tem tempo
    concluida -> o usuário marcou como feita

IMPORTANTE: o sistema NÃO inventa intervalos de manutenção. A "margem de aviso"
é só um alerta configurável pelo usuário; a data e a km da revisão vêm dele.
"""
from core.database import connection
from core.formatters import km as fmt_km
from core.formatters import today, vehicle_label
from core.validators import (ValidationError, parse_date, run_checks, validate_days, validate_km,
                             validate_text)
from services.vehicles import get_vehicle

DEFAULT_WARN_DAYS = 30
DEFAULT_WARN_KM = 1000

STATUS_ORDER = {"atrasada": 0, "proxima": 1, "no_prazo": 2, "concluida": 3}
STATUS_LABEL = {"atrasada": "Atrasada", "proxima": "Próxima", "no_prazo": "No prazo", "concluida": "Concluída"}
STATUS_ICON = {"atrasada": "🔴", "proxima": "🟡", "no_prazo": "🟢", "concluida": "✅"}


# ---------- Cálculo do status (função pura: fácil de testar) ----------
def _plural(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def compute_status(due_date, due_km, current_km, warn_days, warn_km, reference_date=None):
    """
    Devolve (status, motivo). `due_date` é um objeto date ou None; `due_km` é int ou None.
    Se houver data E km, vale o critério mais grave dos dois.
    """
    reference_date = reference_date or today()
    severity = 0                      # 0 = no prazo, 1 = próxima, 2 = atrasada
    reasons = []

    if due_date is not None:
        days = (due_date - reference_date).days
        if days < 0:
            severity = max(severity, 2)
            reasons.append(f"Venceu há {_plural(-days, 'dia', 'dias')}")
        elif days == 0:
            severity = max(severity, 1)
            reasons.append("Vence hoje")
        else:
            if days <= warn_days:
                severity = max(severity, 1)
            reasons.append(f"Faltam {_plural(days, 'dia', 'dias')}")

    if due_km is not None:
        remaining = due_km - current_km
        if remaining < 0:
            severity = max(severity, 2)
            reasons.append(f"Passou {fmt_km(-remaining)} da prevista")
        elif remaining == 0:
            severity = max(severity, 2)
            reasons.append("Chegou na quilometragem prevista")
        else:
            if remaining <= warn_km:
                severity = max(severity, 1)
            reasons.append(f"Faltam {fmt_km(remaining)}")

    status = {2: "atrasada", 1: "proxima", 0: "no_prazo"}[severity]
    return status, " · ".join(reasons)


# ---------- Configuração da margem de aviso ----------
def get_alert_settings() -> tuple:
    with connection() as conn:
        rows = dict(conn.execute("SELECT key, value FROM settings").fetchall())
    return (int(rows.get("warn_days", DEFAULT_WARN_DAYS)), int(rows.get("warn_km", DEFAULT_WARN_KM)))


def save_alert_settings(days, km_margin) -> tuple:
    """Valida e salva a margem de aviso. Devolve (dias, km) já convertidos para número."""
    data = run_checks({
        "days": lambda: validate_days(days, "Avisar com quantos dias de antecedência"),
        "km": lambda: validate_km(km_margin, "Avisar com quantos km de antecedência"),
    })
    with connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('warn_days', ?)", (str(data["days"]),))
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('warn_km', ?)", (str(data["km"]),))
    return data["days"], data["km"]


# ---------- CRUD ----------
def _clean(vehicle_id, service_type, date_text, due_km, notes) -> dict:
    def check_vehicle():
        if vehicle_id is None:
            raise ValidationError("Escolha o veículo no menu «Veículo».")
        if get_vehicle(vehicle_id) is None:
            raise ValidationError("O veículo escolhido não existe mais. Escolha outro no menu «Veículo».")
        return int(vehicle_id)

    data = run_checks({
        "vehicle_id": check_vehicle,
        "service_type": lambda: validate_text(service_type, "Tipo de serviço", max_len=50),
        "due_date": lambda: parse_date(date_text, "Data prevista", required=False),
        "due_km": lambda: validate_km(due_km, "Quilometragem prevista", required=False),
        "notes": lambda: validate_text(notes, "Observação", required=False, max_len=200),
    })
    if data["due_date"] is None and data["due_km"] is None:
        raise ValidationError("Informe a «Data prevista», a «Quilometragem prevista» ou as duas. "
                              "O sistema precisa de pelo menos uma para avisar você.")
    return data


def create_schedule(vehicle_id, service_type, date_text, due_km, notes=None) -> int:
    d = _clean(vehicle_id, service_type, date_text, due_km, notes)
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO scheduled_maintenances (vehicle_id, service_type, due_date, due_km, notes)"
            " VALUES (?,?,?,?,?)",
            (d["vehicle_id"], d["service_type"], d["due_date"].isoformat() if d["due_date"] else None,
             d["due_km"], d["notes"]),
        )
        return cur.lastrowid


def update_schedule(schedule_id, vehicle_id, service_type, date_text, due_km, notes=None) -> None:
    d = _clean(vehicle_id, service_type, date_text, due_km, notes)
    with connection() as conn:
        cur = conn.execute(
            "UPDATE scheduled_maintenances SET vehicle_id=?, service_type=?, due_date=?, due_km=?, notes=?"
            " WHERE id=?",
            (d["vehicle_id"], d["service_type"], d["due_date"].isoformat() if d["due_date"] else None,
             d["due_km"], d["notes"], schedule_id),
        )
        if cur.rowcount == 0:
            raise ValidationError("Esta revisão não existe mais. Atualize a lista e tente de novo.")


def set_done(schedule_id, done: bool) -> None:
    with connection() as conn:
        cur = conn.execute("UPDATE scheduled_maintenances SET done=? WHERE id=?", (1 if done else 0, schedule_id))
        if cur.rowcount == 0:
            raise ValidationError("Esta revisão não existe mais. Atualize a lista e tente de novo.")


def delete_schedule(schedule_id) -> None:
    with connection() as conn:
        cur = conn.execute("DELETE FROM scheduled_maintenances WHERE id=?", (schedule_id,))
        if cur.rowcount == 0:
            raise ValidationError("Esta revisão não existe mais. Atualize a lista e tente de novo.")


def get_schedule(schedule_id):
    if schedule_id is None:
        return None
    with connection() as conn:
        row = conn.execute("SELECT * FROM scheduled_maintenances WHERE id=?", (schedule_id,)).fetchone()
    return dict(row) if row else None


def list_schedules(include_done=False, vehicle_id=None) -> list:
    """
    Lista as revisões já com status calculado, das mais urgentes para as menos urgentes.
    Cada item traz: status, status_label, status_icon, reason (motivo) e vehicle_label.
    """
    sql = ("SELECT s.*, v.brand, v.model, v.plate, v.current_km FROM scheduled_maintenances s "
           "JOIN vehicles v ON v.id = s.vehicle_id WHERE 1=1")
    params = []
    if not include_done:
        sql += " AND s.done = 0"
    if vehicle_id is not None:
        sql += " AND s.vehicle_id = ?"
        params.append(vehicle_id)
    with connection() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

    warn_days, warn_km = get_alert_settings()
    for r in rows:
        due_date = parse_date(r["due_date"], "", required=False) if r["due_date"] else None
        if r["done"]:
            r["status"], r["reason"] = "concluida", "Serviço marcado como feito"
        else:
            r["status"], r["reason"] = compute_status(due_date, r["due_km"], r["current_km"], warn_days, warn_km)
        r["status_label"] = STATUS_LABEL[r["status"]]
        r["status_icon"] = STATUS_ICON[r["status"]]
        r["vehicle_label"] = vehicle_label(r["brand"], r["model"], r["plate"])

    rows.sort(key=lambda r: (STATUS_ORDER[r["status"]], r["due_date"] or "9999-12-31", r["due_km"] or 10**9))
    return rows
