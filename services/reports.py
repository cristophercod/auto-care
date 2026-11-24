"""
services/reports.py
-------------------
Números para o Dashboard e para a tela de Gastos (somas, contagens e totais por veículo).
"""
from core.database import connection
from core.formatters import vehicle_label
from services.schedules import list_schedules


def dashboard_summary() -> dict:
    with connection() as conn:
        vehicles = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        count, total = conn.execute("SELECT COUNT(*), COALESCE(SUM(cost), 0) FROM maintenances").fetchone()

    schedules = list_schedules(include_done=False)
    return {
        "vehicles": vehicles,
        "maintenances": count,
        "total_spent": round(total, 2),
        "overdue": sum(1 for s in schedules if s["status"] == "atrasada"),
        "soon": sum(1 for s in schedules if s["status"] == "proxima"),
        "upcoming": schedules,          # já ordenadas por urgência
    }


def expenses_summary(date_from=None, date_to=None) -> dict:
    """Total, quantidade, média e total por veículo dentro do período informado."""
    # O filtro de datas fica dentro do JOIN (ON ... AND ...). Assim, veículos sem
    # gastos no período continuam aparecendo na lista, com R$ 0,00.
    period_filter, params = "", []
    if date_from:
        period_filter += " AND m.service_date >= ?"
        params.append(date_from.isoformat())
    if date_to:
        period_filter += " AND m.service_date <= ?"
        params.append(date_to.isoformat())

    sql = (
        "SELECT v.id, v.brand, v.model, v.plate, COUNT(m.id) AS services, COALESCE(SUM(m.cost), 0) AS total "
        "FROM vehicles v LEFT JOIN maintenances m ON m.vehicle_id = v.id" + period_filter +
        " GROUP BY v.id ORDER BY total DESC, v.brand"
    )
    with connection() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

    total = round(sum(r["total"] for r in rows), 2)
    services = sum(r["services"] for r in rows)
    for r in rows:
        r["vehicle_label"] = vehicle_label(r["brand"], r["model"], r["plate"])
        r["total"] = round(r["total"], 2)
        r["percent"] = (r["total"] / total * 100) if total > 0 else 0.0
    return {
        "total": total,
        "services": services,
        "average": round(total / services, 2) if services else 0.0,
        "by_vehicle": rows,
    }
